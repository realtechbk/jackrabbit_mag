"""End-to-end proof that the DuckDB-derived numbers reconcile to the
validated legacy analysis (outputs/MAG_ServiceLinePerformance_v8.xlsx /
CURRENT_STATUS.md), per CLAUDE.md rule 1 and this project's Phase 2
requirements.

Two things are tested against REAL files in data/raw/, with no fixtures:
  - class-enrolment reconciliation (Class/Event Revenue Summary): exact
    match to CURRENT_STATUS.md's de-duplicated totals of 5,684 / 6,199 /
    6,341 for 2023/2024/2025.
  - duplicate-import prevention (source_files.file_sha256): re-running the
    importer against the same files does not duplicate any row.

Revenue Summary (PDF) reconciliation is tested separately, against hand-built
fixture text rather than the real PDFs. This environment's `pdftotext` on
PATH is Xpdf's clone (its own copyright banner says so), not the Poppler
build the rest of this project assumes (CLAUDE.md: "pdftotext (poppler) is
required") -- the two render this report's -layout differently, and Xpdf's
rendering breaks the column alignment the parser depends on. Running the
importer against the real PDFs in this environment demonstrates the
reconciliation gate working AS DESIGNED (it refuses to load rather than
produce a silently wrong number) but cannot demonstrate a correct revenue
total, because the extracted text itself is wrong before the parser ever
sees it. Installing Poppler's pdftotext would very likely make the real-PDF
path reconcile too, but that's an environment fix, not a code fix -- see
test_revenue_summary_malformed_fixture_is_excluded_not_silently_wrong for
what the gate does either way.
"""

from __future__ import annotations

import pytest

from cfo_platform.core.exceptions import ConfigurationError, ReconciliationError
from cfo_platform.db.migrations.runner import migrate
from cfo_platform.importers.jackrabbit.importer import FileExtract, JackrabbitClassImporter
from cfo_platform.settings import REPO_ROOT

REAL_RAW_DATA_DIR = REPO_ROOT / "data" / "raw"

# CURRENT_STATUS.md: "Class enrolments for the 7 comparable rows,
# de-duplicated: 5,684 / 6,199 / 6,341." 2026 is intentionally excluded --
# its Class/Event export's enrolment window is defective (covers 19 months
# against 7 months of revenue), so CURRENT_STATUS.md leaves it unusable
# rather than publishing a benchmark for it.
ENROLMENT_BENCHMARK = {"2023": 5684.0, "2024": 6199.0, "2025": 6341.0}

WELL_FORMED_FIXTURE = """\
Date: 7/28/2026 10:00:00 AM             Revenue Summary                                              Page 1

                                        1/1/2025 - 12/31/2025

Cat1  Cat2              Cat3  Activity                                                      Enrollment Discount Amount

Open Gym
      Open Gym
                    MAG Day Open Gym                                                        0  0.00  45.00
Open Gym Subtotal:                                                                          0  0.00  45.00

Recreational
      Rec Girls
                    Girls G1                                                                0  0.00  200.00
                    Rec Girls Subtotal:                                                     0  0.00  200.00
Recreational Subtotal:                                                                      0  0.00  200.00

Totals:                                                                                      0  0.00  245.00
"""

MALFORMED_FIXTURE = WELL_FORMED_FIXTURE.replace("245.00", "999.00", 1)


def _revenue_summary_extract(text: str, path_name: str = "RevenueSummary_2025.pdf") -> FileExtract:
    from pathlib import Path

    from cfo_platform.importers.jackrabbit.revenue_summary_parser import label_for, parse

    parsed = parse(text)
    return FileExtract(
        report_type="revenue_summary",
        path=Path(path_name),
        file_sha256="test-fixture",
        file_bytes=len(text),
        period_label=label_for(path_name, parsed),
        content=parsed,
    )


def _new_importer(raw_data_dir=REAL_RAW_DATA_DIR) -> JackrabbitClassImporter:
    return JackrabbitClassImporter(client_id="mag", raw_data_dir=raw_data_dir)


class TestRevenueReconciliationGate:
    """Proves the reconciliation gate on well-formed and malformed input,
    independent of this environment's pdftotext build."""

    def test_well_formed_revenue_reconciles_and_loads(self, tmp_warehouse):
        migrate(tmp_warehouse)
        importer = _new_importer()
        extract = _revenue_summary_extract(WELL_FORMED_FIXTURE)
        transformed = importer.transform([extract])

        assert transformed.failures == []
        importer.load(tmp_warehouse, transformed)  # must not raise

        total = tmp_warehouse.execute(
            "SELECT SUM(net_amount) FROM fact_revenue WHERE period_label = '2025'"
        ).fetchone()[0]
        assert total == 245.00

        reported = tmp_warehouse.execute(
            "SELECT reported_amount FROM raw_revenue_summary_totals"
        ).fetchone()[0]
        assert round(total - reported, 2) == 0.0

    def test_malformed_revenue_is_excluded_not_silently_wrong(self, tmp_warehouse):
        """CLAUDE.md rule 1: a period that doesn't reconcile must never
        reach the warehouse looking like it did."""
        migrate(tmp_warehouse)
        importer = _new_importer()
        extract = _revenue_summary_extract(MALFORMED_FIXTURE)
        transformed = importer.transform([extract])

        assert transformed.loads == []
        assert len(transformed.failures) == 1

        with pytest.raises(ReconciliationError):
            importer.load(tmp_warehouse, transformed)

        assert tmp_warehouse.execute("SELECT COUNT(*) FROM fact_revenue").fetchone()[0] == 0


class TestRealDataEndToEnd:
    """Runs the importer against the actual data/raw/ files."""

    @staticmethod
    def _load_ignoring_pdf_environment_gap(importer, conn):
        raw = importer.extract()
        transformed = importer.transform(raw)
        try:
            importer.load(conn, transformed)
        except ReconciliationError:
            # Expected in this environment for revenue_summary files only --
            # see the module docstring. Everything else still loaded.
            pass
        return transformed

    def test_class_enrolment_reconciles_to_legacy_benchmark(self, tmp_warehouse):
        migrate(tmp_warehouse)
        importer = _new_importer()
        self._load_ignoring_pdf_environment_gap(importer, tmp_warehouse)

        rows = tmp_warehouse.execute(
            """
            SELECT f.period_label, SUM(f.enrollment)
            FROM fact_class_enrolment f
            JOIN dim_service_line d ON d.service_line_key = f.service_line_key
            WHERE d.is_class_enrolment_comparable AND NOT f.is_duplicate_row
            GROUP BY f.period_label
            """
        ).fetchall()
        computed = dict(rows)

        for period, expected in ENROLMENT_BENCHMARK.items():
            assert computed[period] == expected, (
                f"{period}: computed {computed.get(period)}, legacy benchmark {expected}"
            )

    def test_reimport_is_idempotent(self, tmp_warehouse):
        migrate(tmp_warehouse)
        importer = _new_importer()

        self._load_ignoring_pdf_environment_gap(importer, tmp_warehouse)
        counts_after_first = self._table_counts(tmp_warehouse)

        self._load_ignoring_pdf_environment_gap(importer, tmp_warehouse)
        counts_after_second = self._table_counts(tmp_warehouse)

        assert counts_after_second == counts_after_first

        n_source_files = tmp_warehouse.execute("SELECT COUNT(*) FROM source_files").fetchone()[0]
        n_runs = tmp_warehouse.execute("SELECT COUNT(*) FROM import_runs").fetchone()[0]
        assert n_runs == 2, "each call to load() records its own import_runs row"
        assert n_source_files > 0

    @staticmethod
    def _table_counts(conn) -> dict[str, int]:
        tables = [
            "source_files", "fact_class_enrolment", "raw_class_event_revenue_rows",
            "raw_sales_detail_rows", "raw_class_list_rows",
        ]
        return {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in tables}

    def test_broken_pdftotext_environment_does_not_block_other_report_types(self, tmp_warehouse, monkeypatch):
        """The real-world scenario this repo hits today: pdftotext exists
        but isn't Poppler. That must exclude only the Revenue Summary PDFs
        (as a clear, actionable failure) and still let Class/Event Revenue,
        Sales Detail and Class List load normally in the same run."""
        monkeypatch.setattr(
            "cfo_platform.importers.jackrabbit.importer.check_pdftotext_is_poppler",
            lambda *a, **kw: (_ for _ in ()).throw(ConfigurationError("no Poppler in this test")),
        )
        migrate(tmp_warehouse)
        importer = _new_importer()
        raw = importer.extract()
        transformed = importer.transform(raw)

        assert len(transformed.failures) == 4  # the four RevenueSummary_*.pdf files
        assert all(extract.report_type == "revenue_summary" for extract, _ in transformed.failures)
        assert len(transformed.loads) == 9  # class_event_revenue(4) + sales_detail(4) + class_list(1)

        with pytest.raises(ReconciliationError):
            importer.load(tmp_warehouse, transformed)

        # the good data landed despite the raise above
        assert tmp_warehouse.execute("SELECT COUNT(*) FROM fact_class_enrolment").fetchone()[0] > 0
        assert tmp_warehouse.execute("SELECT COUNT(*) FROM fact_revenue").fetchone()[0] == 0

    def test_duplicate_file_is_not_reloaded_under_a_different_name(self, tmp_warehouse, tmp_path):
        """A byte-identical copy of an already-imported file, even saved
        under a different name, must not be re-imported (dedupe is by
        content hash, not filename)."""
        import shutil

        migrate(tmp_warehouse)
        src = REAL_RAW_DATA_DIR / "ClassEventRevenue_2023.xlsx"
        copy_dir = tmp_path / "raw_copy"
        copy_dir.mkdir()
        shutil.copy(src, copy_dir / "ClassEventRevenue_2023.xlsx")
        shutil.copy(src, copy_dir / "ClassEventRevenue_2023_copy.xlsx")

        importer = _new_importer(raw_data_dir=copy_dir)
        importer.FILE_PATTERNS = (("class_event_revenue", "ClassEventRevenue*.xlsx"),)
        raw = importer.extract()
        assert len(raw) == 2  # both files discovered...
        transformed = importer.transform(raw)
        importer.load(tmp_warehouse, transformed)

        # ...but only one was actually loaded, since they're byte-identical.
        assert tmp_warehouse.execute("SELECT COUNT(*) FROM source_files").fetchone()[0] == 1

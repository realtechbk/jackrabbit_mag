"""Permanent regression coverage: the real Revenue Summary PDFs, through the
real production ingestion path, must reconcile exactly to the validated
legacy analysis.

This is deliberately separate from tests/unit/test_revenue_summary_parser.py
(fixture-based, fast, tests the parsing algorithm in isolation) and from
tests/integration/test_jackrabbit_importer.py (tolerates a non-Poppler
pdftotext, because it also has to run in environments that don't have one).
This file asserts the real numbers, unconditionally -- if it fails, either
the source data changed, the parser/mapping changed, or the pdftotext on
PATH stopped being a Poppler build (the most likely cause historically; see
importers/jackrabbit/revenue_summary_parser.py's check_pdftotext_is_poppler,
which should turn that case into a clear ConfigurationError here rather than
a confusing variance).

Marked `regression` (registered in pyproject.toml) so it can be excluded from
a fast local loop with `pytest -m "not regression"` and run explicitly with
`pytest -m regression`.

No parsing or mapping logic is duplicated here: every assertion is a SQL
query against the DuckDB tables the real JackrabbitClassImporter.run() (the
same extract -> transform -> load path `cfo-platform db-import` uses)
produces.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

from cfo_platform.db.migrations.runner import migrate
from cfo_platform.importers.jackrabbit.importer import JackrabbitClassImporter
from cfo_platform.settings import REPO_ROOT

pytestmark = pytest.mark.regression

REAL_RAW_DATA_DIR = REPO_ROOT / "data" / "raw"

EXPECTED_REVENUE_SUMMARY_FILES = [
    "RevenueSummary_2023.pdf",
    "RevenueSummary_2024.pdf",
    "RevenueSummary_2025.pdf",
    "RevenueSummary_2026YTD.pdf",
]

# scripts/build_perf_v8.py's TARGETS constant -- each Revenue Summary's own
# stated total, previously verified by hand against the source PDFs.
EXPECTED_REPORTED_TOTALS = {
    "2023": 1996290.52,
    "2024": 2297353.81,
    "2025": 2241034.37,
    "2026": 1126223.32,
}
EXPECTED_COMBINED_TOTAL = round(sum(EXPECTED_REPORTED_TOTALS.values()), 2)  # 7,660,902.02

PERIODS = ("2023", "2024", "2025", "2026")

# Service-line revenue, ported verbatim from scripts/build_perf_v8.py's ROWS
# constant (columns are 2023, 2024, 2025, 2026 YTD, in that order) -- the
# same benchmark test_jackrabbit_importer.py uses for class enrolment,
# applied here to revenue instead.
LEGACY_SERVICE_LINE_REVENUE: dict[str, tuple[float, float, float, float]] = {
    "Recreational -- Preschool (The Jungle)":  (343335.26, 381504.55, 367014.79, 194726.85),
    "Recreational -- Girls Wings":              (748491.02, 999839.46, 975278.37, 505818.42),
    "Recreational -- Boys Wings":                (86323.49,  84553.60,  85489.15,  40964.00),
    "Recreational -- Tumbling":                  (83307.09, 102217.79,  89018.18,  36851.55),
    "Recreational -- Workshops & Class Series":     (36.00,    671.40,   3134.00,     25.00),
    "Recreational -- Unlinked Tuition":          (21708.45,  27214.03,  16502.96,   9443.75),
    "Competitive -- Pre-Team":                   (26248.25,       0.0,       0.0,       0.0),
    "Competitive -- American Flyers Teams":     (517731.45, 552485.77, 564294.62, 259212.55),
    "Ancillary -- Open Gym":                     (30059.50,  23357.15,  28128.56,  20980.25),
    "Ancillary -- Annual Membership Fees":       (58293.50,  61640.05,  52776.95,  21575.30),
    "Ancillary -- Birthday Parties":             (45767.05,  19038.20,       0.0,       0.0),
    "Ancillary -- Pro Shop":                      (28031.65,  28789.86,  34975.39,  15754.09),
    "Ancillary -- Private Lessons":                (3815.71,   5645.13,   8318.25,   6055.90),
    "Ancillary -- Gift Certificates":               (310.00,    270.00,       0.0,       0.0),
    "Ancillary -- Non-Instructional Time":             (0.0,       0.0,    340.00,       0.0),
    "Other -- Tumble (stray Cat1)":                    (0.0,       0.0,     17.80,       0.0),
    "Review -- Unapplied Payments":                 (172.00,   -100.00,  11920.58,  12817.63),
    "EXCLUDE -- Staff":                             (2660.10,  10226.82,   3824.77,   1998.03),
}


def _real_revenue_summary_importer() -> JackrabbitClassImporter:
    importer = JackrabbitClassImporter(client_id="mag", raw_data_dir=REAL_RAW_DATA_DIR)
    importer.FILE_PATTERNS = tuple(p for p in importer.FILE_PATTERNS if p[0] == "revenue_summary")
    return importer


@pytest.fixture(scope="module")
def imported_revenue_warehouse(tmp_path_factory) -> duckdb.DuckDBPyConnection:
    """Runs the real importer against the real PDFs exactly once, shared
    read-only across every assertion in this module."""
    missing = [f for f in EXPECTED_REVENUE_SUMMARY_FILES if not (REAL_RAW_DATA_DIR / f).exists()]
    if missing:
        pytest.skip(
            f"Real Revenue Summary PDFs not found in {REAL_RAW_DATA_DIR} "
            f"(missing: {missing}) -- skipping the revenue regression test."
        )

    db_path: Path = tmp_path_factory.mktemp("revenue_regression") / "mag_regression.duckdb"
    conn = duckdb.connect(str(db_path))
    migrate(conn)
    _real_revenue_summary_importer().run(conn)  # the real extract -> transform -> load path
    yield conn
    conn.close()


class TestRevenueRegressionAgainstLegacyBenchmark:
    def test_each_period_reconciles_to_its_stated_total(self, imported_revenue_warehouse):
        rows = imported_revenue_warehouse.execute(
            "SELECT sf.period_label, t.reported_amount "
            "FROM raw_revenue_summary_totals t "
            "JOIN source_files sf USING (source_file_id)"
        ).fetchall()
        assert dict(rows) == EXPECTED_REPORTED_TOTALS

    def test_computed_revenue_matches_reported_total_per_period(self, imported_revenue_warehouse):
        rows = imported_revenue_warehouse.execute(
            "SELECT period_label, ROUND(SUM(net_amount), 2) FROM fact_revenue GROUP BY period_label"
        ).fetchall()
        assert dict(rows) == EXPECTED_REPORTED_TOTALS

    def test_combined_revenue_across_all_periods(self, imported_revenue_warehouse):
        total = imported_revenue_warehouse.execute(
            "SELECT ROUND(SUM(net_amount), 2) FROM fact_revenue"
        ).fetchone()[0]
        assert total == EXPECTED_COMBINED_TOTAL

    def test_service_line_revenue_matches_legacy_analysis_exactly(self, imported_revenue_warehouse):
        rows = imported_revenue_warehouse.execute(
            "SELECT service_line_key, period_label, ROUND(SUM(net_amount), 2) "
            "FROM fact_revenue GROUP BY service_line_key, period_label"
        ).fetchall()
        computed: dict[str, dict[str, float]] = {}
        for service_line_key, period, amount in rows:
            computed.setdefault(service_line_key, {})[period] = amount

        mismatches = []
        for service_line_key, legacy_by_period in LEGACY_SERVICE_LINE_REVENUE.items():
            for period, expected in zip(PERIODS, legacy_by_period, strict=True):
                actual = computed.get(service_line_key, {}).get(period, 0.0)
                if actual != expected:
                    mismatches.append((service_line_key, period, actual, expected))

        assert mismatches == [], (
            f"{len(mismatches)} service-line x period cell(s) disagree with the validated "
            f"legacy analysis as (service_line, period, actual, expected): {mismatches}"
        )

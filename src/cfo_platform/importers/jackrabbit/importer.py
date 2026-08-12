"""JackrabbitClassImporter: extract -> transform -> load for MAG's four
Jackrabbit Class exports (DATA_DICTIONARY.md section 1).

extract() reads each source file into a source-native structure (a parsed
Revenue Summary dict, or a list of row dicts for the xlsx/xls reports) and
computes each file's identity (sha256, size) for lineage/dedupe.

transform() has no DB connection (see importers/base.py), so all
service-line mapping (mapping.py), de-duplication (dedupe.py) and the
reconciliation gate (validation.py) run here, in pure Python, before any of
it reaches the warehouse -- a period that fails to reconcile never gets as
far as load().

load() writes everything for files not already imported (by sha256, per
client) and records one import_runs row for the whole call plus one
source_files row per file actually loaded, wrapped in DuckDB's default
transaction so a failure partway through a run does not leave partial data.
"""

from __future__ import annotations

import hashlib
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import duckdb

from cfo_platform.core.exceptions import ReconciliationError
from cfo_platform.importers.base import Importer
from cfo_platform.importers.jackrabbit import dedupe, mapping, readers, validation
from cfo_platform.importers.jackrabbit.revenue_summary_parser import (
    ParsedRevenueSummary,
    label_for,
    parse,
    run_pdftotext,
)
from cfo_platform.importers.registry import register_importer
from cfo_platform.logging_config import get_logger

logger = get_logger(__name__)

_YEAR_RE = re.compile(r"(20\d{2})")


def _period_label_from_filename(name: str) -> str | None:
    m = _YEAR_RE.search(name)
    return m.group(1) if m else None


def _file_identity(path: Path) -> tuple[str, int]:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest(), len(data)


@dataclass
class FileExtract:
    report_type: str
    path: Path
    file_sha256: str
    file_bytes: int
    period_label: str | None
    content: Any  # ParsedRevenueSummary for revenue_summary; list[dict] otherwise


@dataclass
class FileLoad:
    """Everything transform() prepared for one file, ready for load()."""

    extract: FileExtract
    raw_rows: list[dict[str, Any]] = field(default_factory=list)
    revenue_totals: dict[str, Any] | None = None  # revenue_summary only
    fact_revenue_rows: list[dict[str, Any]] = field(default_factory=list)  # revenue_summary only
    fact_enrolment_rows: list[dict[str, Any]] = field(default_factory=list)  # class_event_revenue only


@dataclass
class TransformResult:
    """transform()'s return value: files ready to load, plus files that
    failed the reconciliation gate and were excluded rather than aborting
    the whole run. One bad Revenue Summary period must not block loading a
    perfectly good Class/Event Revenue or Sales Detail file in the same
    run -- CLAUDE.md rule 1 is about not shipping a wrong revenue number,
    not about treating unrelated report types as guilty by association.
    load() still surfaces every failure (raises after loading everything
    that did pass), so a partial run is never silently reported as clean.
    """

    loads: list[FileLoad] = field(default_factory=list)
    failures: list[tuple[FileExtract, str]] = field(default_factory=list)


@register_importer("jackrabbit_class")
class JackrabbitClassImporter(Importer):
    source_system = "jackrabbit_class"

    FILE_PATTERNS: tuple[tuple[str, str], ...] = (
        ("revenue_summary", "RevenueSummary_*.pdf"),
        ("class_event_revenue", "ClassEventRevenue_*.xlsx"),
        ("sales_detail", "SalesDetail_*.xls"),
        ("class_list", "ClassList_*.xls"),
    )

    def discover_files(self) -> list[tuple[str, Path]]:
        found: list[tuple[str, Path]] = []
        for report_type, pattern in self.FILE_PATTERNS:
            found.extend((report_type, p) for p in sorted(self.raw_data_dir.glob(pattern)))
        return found

    # ---------------------------------------------------------------- extract

    def extract(self) -> list[FileExtract]:
        extracts = []
        for report_type, path in self.discover_files():
            sha256, size = _file_identity(path)

            if report_type == "revenue_summary":
                parsed: ParsedRevenueSummary = parse(run_pdftotext(path))
                period_label = label_for(path.name, parsed)
                content: Any = parsed
            elif report_type == "class_event_revenue":
                content = readers.read_class_event_revenue(path)
                period_label = _period_label_from_filename(path.name)
            elif report_type == "sales_detail":
                content = readers.read_sales_detail(path)
                period_label = _period_label_from_filename(path.name)
            elif report_type == "class_list":
                content = readers.read_class_list(path)
                period_label = _period_label_from_filename(path.name)
            else:  # pragma: no cover - FILE_PATTERNS is the only source of report_type
                raise AssertionError(f"unhandled report_type {report_type!r}")

            extracts.append(FileExtract(report_type, path, sha256, size, period_label, content))
            logger.info("Extracted %s (%s, %d bytes, period=%s)",
                        path.name, report_type, size, period_label)
        return extracts

    # -------------------------------------------------------------- transform

    def transform(self, raw: list[FileExtract]) -> TransformResult:
        dispatch = {
            "revenue_summary": self._transform_revenue_summary,
            "class_event_revenue": self._transform_class_event_revenue,
            "sales_detail": self._transform_sales_detail,
            "class_list": self._transform_class_list,
        }
        result = TransformResult()
        for extract in raw:
            try:
                result.loads.append(dispatch[extract.report_type](extract))
            except ReconciliationError as exc:
                logger.error("Reconciliation failed for %s, excluding from this run: %s",
                             extract.path.name, exc)
                result.failures.append((extract, str(exc)))
        return result

    def _transform_revenue_summary(self, extract: FileExtract) -> FileLoad:
        parsed: ParsedRevenueSummary = extract.content
        period_label = extract.period_label
        grand = parsed["grand"]

        validation.check_report_total_present(period_label, grand.get("amt"))
        reported_amount = grand["amt"]
        reported_discount = grand.get("disc") or 0.0

        cat1_sum = sum(v[0] for v in parsed["cat1"].values())
        validation.check_cat1_reconciles_to_report(period_label, cat1_sum, reported_amount)

        raw_activities = [
            {
                "line_no": i,
                "cat1": a["cat1"],
                "cat2": a["cat2"],
                "activity_name": a["name"],
                "enrollment_raw": a["enroll"],
                "discount_amount": a["disc"],
                "net_amount": a["amt"],
            }
            for i, a in enumerate(parsed["activities"], start=1)
        ]
        cat1_totals = [
            {"cat1": cat1, "net_amount": v[0], "discount_amount": v[1]}
            for cat1, v in parsed["cat1"].items()
        ]
        cat2_totals = [
            {"cat1": cat1, "cat2": cat2, "net_amount": v[0], "discount_amount": v[1]}
            for (cat1, cat2), v in parsed["cat2"].items()
        ]

        fact_rows: list[dict[str, Any]] = []

        # Every Cat1 except Recreational maps 1:1 from its Cat1 total.
        for cat1, (amt, disc) in parsed["cat1"].items():
            key = mapping.map_r1_cat1_total(cat1)
            if key is None:
                continue
            fact_rows.append({
                "cat1": cat1, "cat2": "", "service_line_key": key,
                "derivation": "cat1_total", "net_amount": amt, "discount_amount": disc,
            })

        # Recreational maps from its named Cat2 totals. Cat3-level subtotal
        # labels also land in parsed['cat2'] (the parser doesn't distinguish
        # nesting depth -- see revenue_summary_parser.py) but aren't in
        # mapping.CATEGORY_MAP, so map_r1_cat2_total(...) is None for them
        # and they're skipped here without double-counting: their money is
        # already inside their parent Cat2's total (DATA_DICTIONARY.md
        # section 7 confirms this sums correctly, all four periods).
        for (cat1, cat2), (amt, disc) in parsed["cat2"].items():
            if cat1 != "Recreational" or cat2 == "(blank)":
                continue
            key = mapping.map_r1_cat2_total(cat2)
            if key is None:
                continue
            fact_rows.append({
                "cat1": cat1, "cat2": cat2, "service_line_key": key,
                "derivation": "cat2_total", "net_amount": amt, "discount_amount": disc,
            })

        # Recreational + blank Cat2 splits at the activity level.
        blank_cat2_splits: dict[str, list[float]] = {}
        for a in parsed["activities"]:
            if a["cat1"] == "Recreational" and a["cat2"] is None:
                key = mapping.split_recreational_blank_cat2(a["name"])
                bucket = blank_cat2_splits.setdefault(key, [0.0, 0.0])
                bucket[0] += a["amt"]
                bucket[1] += a["disc"]
        for key, (amt, disc) in blank_cat2_splits.items():
            derivation = ("activity_split:unlinked_tuition" if key == mapping.UNLINKED_TUITION
                          else "activity_split:workshops")
            fact_rows.append({
                "cat1": "Recreational", "cat2": "", "service_line_key": key,
                "derivation": derivation, "net_amount": amt, "discount_amount": disc,
            })

        fact_sum = sum(r["net_amount"] for r in fact_rows)
        validation.check_fact_revenue_reconciles_to_report(period_label, fact_sum, reported_amount)

        return FileLoad(
            extract=extract,
            raw_rows=raw_activities,
            revenue_totals={
                "reported_amount": reported_amount,
                "reported_discount": reported_discount,
                "cat1_totals": cat1_totals,
                "cat2_totals": cat2_totals,
            },
            fact_revenue_rows=fact_rows,
        )

    def _transform_class_event_revenue(self, extract: FileExtract) -> FileLoad:
        rows = dedupe.mark_duplicate_rows(extract.content)
        fact_rows = []
        for r in rows:
            key, _is_comparable = mapping.map_class_event_row(r["cat1"], r["cat2"])
            fact_rows.append({
                "class_event": r["class_event"], "session": r["session"],
                "cat1": r["cat1"], "cat2": r["cat2"], "cat3": r["cat3"],
                "service_line_key": key,
                "enrollment": r["enrollment"] or 0.0,
                "revenue": r["revenue"] or 0.0,
                "is_duplicate_row": r["is_duplicate_row"],
            })
        return FileLoad(extract=extract, raw_rows=rows, fact_enrolment_rows=fact_rows)

    def _transform_sales_detail(self, extract: FileExtract) -> FileLoad:
        return FileLoad(extract=extract, raw_rows=extract.content)

    def _transform_class_list(self, extract: FileExtract) -> FileLoad:
        return FileLoad(extract=extract, raw_rows=extract.content)

    # ------------------------------------------------------------------ load

    def load(self, conn: duckdb.DuckDBPyConnection, transformed: TransformResult) -> None:
        run_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO import_runs (run_id, client_id, source_system, started_at, status) "
            "VALUES (?, ?, ?, ?, ?)",
            [run_id, self.client_id, self.source_system, datetime.now(), "running"],
        )

        mapping.seed_dim_service_line(conn)
        mapping.seed_dim_category_map(conn)

        imported, skipped = 0, 0
        try:
            for file_load in transformed.loads:
                if self._already_imported(conn, file_load.extract.file_sha256):
                    logger.info(
                        "Skipping already-imported file %s (sha256=%s...)",
                        file_load.extract.path.name, file_load.extract.file_sha256[:12],
                    )
                    skipped += 1
                    continue
                self._load_one_file(conn, run_id, file_load)
                imported += 1
        except Exception as exc:
            conn.execute(
                "UPDATE import_runs SET finished_at = ?, status = ?, notes = ? WHERE run_id = ?",
                [datetime.now(), "failed", str(exc)[:500], run_id],
            )
            raise

        if transformed.failures:
            summary = "; ".join(f"{extract.path.name}: {msg}" for extract, msg in transformed.failures)
            conn.execute(
                "UPDATE import_runs SET finished_at = ?, status = ?, notes = ? WHERE run_id = ?",
                [datetime.now(), "partial_failure",
                 f"imported={imported} skipped_duplicate={skipped} failed={len(transformed.failures)}: {summary}"[:500],
                 run_id],
            )
            raise ReconciliationError(
                f"{len(transformed.failures)} file(s) failed reconciliation and were excluded "
                f"from this run (everything else loaded successfully): {summary}"
            )

        conn.execute(
            "UPDATE import_runs SET finished_at = ?, status = ?, notes = ? WHERE run_id = ?",
            [datetime.now(), "success", f"imported={imported} skipped_duplicate={skipped}", run_id],
        )

    def _already_imported(self, conn: duckdb.DuckDBPyConnection, file_sha256: str) -> bool:
        row = conn.execute(
            "SELECT 1 FROM source_files WHERE client_id = ? AND file_sha256 = ?",
            [self.client_id, file_sha256],
        ).fetchone()
        return row is not None

    def _load_one_file(self, conn: duckdb.DuckDBPyConnection, run_id: str, file_load: FileLoad) -> None:
        extract = file_load.extract
        source_file_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO source_files "
            "(source_file_id, client_id, import_run_id, report_type, file_path, file_name, "
            " file_sha256, file_bytes, period_label, row_count, imported_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [source_file_id, self.client_id, run_id, extract.report_type, str(extract.path),
             extract.path.name, extract.file_sha256, extract.file_bytes, extract.period_label,
             len(file_load.raw_rows), datetime.now()],
        )

        if extract.report_type == "revenue_summary":
            self._load_revenue_summary(conn, source_file_id, extract.period_label, file_load)
        elif extract.report_type == "class_event_revenue":
            self._load_class_event_revenue(conn, source_file_id, extract.period_label, file_load)
        elif extract.report_type == "sales_detail":
            self._load_sales_detail(conn, source_file_id, file_load)
        elif extract.report_type == "class_list":
            self._load_class_list(conn, source_file_id, file_load)

    def _load_revenue_summary(
        self, conn: duckdb.DuckDBPyConnection, source_file_id: str, period_label: str | None, file_load: FileLoad
    ) -> None:
        if file_load.raw_rows:
            conn.executemany(
                "INSERT INTO raw_revenue_summary_activities "
                "(source_file_id, line_no, cat1, cat2, activity_name, enrollment_raw, discount_amount, net_amount) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [(source_file_id, r["line_no"], r["cat1"], r["cat2"], r["activity_name"],
                  r["enrollment_raw"], r["discount_amount"], r["net_amount"]) for r in file_load.raw_rows],
            )

        totals = file_load.revenue_totals
        assert totals is not None
        if totals["cat1_totals"]:
            conn.executemany(
                "INSERT INTO raw_revenue_summary_cat1_totals (source_file_id, cat1, discount_amount, net_amount) "
                "VALUES (?, ?, ?, ?)",
                [(source_file_id, r["cat1"], r["discount_amount"], r["net_amount"]) for r in totals["cat1_totals"]],
            )
        if totals["cat2_totals"]:
            conn.executemany(
                "INSERT INTO raw_revenue_summary_cat2_totals (source_file_id, cat1, cat2, discount_amount, net_amount) "
                "VALUES (?, ?, ?, ?, ?)",
                [(source_file_id, r["cat1"], r["cat2"], r["discount_amount"], r["net_amount"])
                 for r in totals["cat2_totals"]],
            )
        conn.execute(
            "INSERT INTO raw_revenue_summary_totals (source_file_id, reported_discount, reported_amount) "
            "VALUES (?, ?, ?)",
            [source_file_id, totals["reported_discount"], totals["reported_amount"]],
        )

        if file_load.fact_revenue_rows:
            conn.executemany(
                "INSERT INTO fact_revenue "
                "(client_id, period_label, source_file_id, cat1, cat2, service_line_key, derivation, "
                " net_amount, discount_amount) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [(self.client_id, period_label, source_file_id, r["cat1"], r["cat2"], r["service_line_key"],
                  r["derivation"], r["net_amount"], r["discount_amount"]) for r in file_load.fact_revenue_rows],
            )

    def _load_class_event_revenue(
        self, conn: duckdb.DuckDBPyConnection, source_file_id: str, period_label: str | None, file_load: FileLoad
    ) -> None:
        if file_load.raw_rows:
            conn.executemany(
                "INSERT INTO raw_class_event_revenue_rows "
                "(source_file_id, row_no, location, class_event, cat1, cat2, cat3, session, days, "
                " enrollment, avg_revenue_per_student, revenue) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [(source_file_id, r["row_no"], r["location"], r["class_event"], r["cat1"], r["cat2"],
                  r["cat3"], r["session"], r["days"], r["enrollment"], r["avg_revenue_per_student"],
                  r["revenue"]) for r in file_load.raw_rows],
            )
        if file_load.fact_enrolment_rows:
            conn.executemany(
                "INSERT INTO fact_class_enrolment "
                "(client_id, period_label, source_file_id, class_event, session, cat1, cat2, cat3, "
                " service_line_key, enrollment, revenue, is_duplicate_row) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [(self.client_id, period_label, source_file_id, r["class_event"], r["session"], r["cat1"],
                  r["cat2"], r["cat3"], r["service_line_key"], r["enrollment"], r["revenue"],
                  r["is_duplicate_row"]) for r in file_load.fact_enrolment_rows],
            )

    def _load_sales_detail(self, conn: duckdb.DuckDBPyConnection, source_file_id: str, file_load: FileLoad) -> None:
        if not file_load.raw_rows:
            return
        conn.executemany(
            "INSERT INTO raw_sales_detail_rows "
            "(source_file_id, row_no, sale_date, item_number, item_name, qty, amount, discount, tax, "
            " total, note, payment_method, family, student, class_name) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(source_file_id, r["row_no"], r["sale_date"], r["item_number"], r["item_name"], r["qty"],
              r["amount"], r["discount"], r["tax"], r["total"], r["note"], r["payment_method"],
              r["family"], r["student"], r["class_name"]) for r in file_load.raw_rows],
        )

    def _load_class_list(self, conn: duckdb.DuckDBPyConnection, source_file_id: str, file_load: FileLoad) -> None:
        if not file_load.raw_rows:
            return
        conn.executemany(
            "INSERT INTO raw_class_list_rows "
            "(source_file_id, row_no, class_name, description, instructors, status, session, "
            " start_date, end_date, days, start_time, duration, cat1, cat2, cat3, size, "
            " max_enrollment, tuition) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(source_file_id, r["row_no"], r["class_name"], r["description"], r["instructors"],
              r["status"], r["session"], r["start_date"], r["end_date"], r["days"], r["start_time"],
              r["duration"], r["cat1"], r["cat2"], r["cat3"], r["size"], r["max_enrollment"],
              r["tuition"]) for r in file_load.raw_rows],
        )

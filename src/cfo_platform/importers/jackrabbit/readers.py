"""Pandas-based readers for the three non-PDF Jackrabbit exports.

Each reader takes a file path and returns a list of plain dicts in a shape
close to the source file (see DATA_DICTIONARY.md sections 3-4 for column
definitions), ready for source_file-scoped loading. No service-line mapping
or de-duplication happens here -- see mapping.py and dedupe.py.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).replace("\n", " ").strip() for c in df.columns]
    return df


def _find_column(df: pd.DataFrame, prefix: str) -> str:
    """Find the one column whose name starts with `prefix`.

    Used for the Class/Event Revenue Summary's date-ranged headers, e.g.
    'Enrollment 1/1/2025 - 12/31/2025', which vary by the export's date range.
    """
    matches = [c for c in df.columns if c.startswith(prefix)]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one column starting with {prefix!r}, found {matches}")
    return matches[0]


def read_class_event_revenue(path: Path) -> list[dict[str, Any]]:
    """Read a Class/Event Revenue Summary export (R2).

    Drops the trailing 'Total:' row. Does NOT de-duplicate on
    Class + Session + Cat3 -- that is CLAUDE.md rule 5, applied in
    dedupe.py against these raw rows, not baked into the reader.
    """
    df = _normalize_columns(pd.read_excel(path, sheet_name=0))
    enrollment_col = _find_column(df, "Enrollment")
    revenue_col = _find_column(df, "Revenue")

    df = df[df["Class/event"].astype(str).str.strip().str.lower() != "total:"]

    rows: list[dict[str, Any]] = []
    for row_no, rec in enumerate(df.to_dict(orient="records"), start=1):
        rows.append({
            "row_no": row_no,
            "location": _clean_str(rec.get("Location")),
            # class_event/session/cat3 are kept UNSTRIPPED: they feed the
            # Class + Session + Cat3 de-dup key (CLAUDE.md rule 5), and two
            # distinct Jackrabbit class records can render as the same text
            # after stripping while differing only in trailing whitespace --
            # stripping them collapses those into one and silently
            # undercounts enrolment (verified against 2023's Rec Girls: a
            # stripped key drops the total from 2,090 to 2,080).
            "class_event": _raw_str(rec.get("Class/event")),
            "cat1": _clean_str(rec.get("Category 1")),
            "cat2": _clean_str(rec.get("Category 2")),
            "cat3": _raw_str(rec.get("Category 3")),
            "session": _raw_str(rec.get("Session")),
            "days": _clean_str(rec.get("Days")),
            "enrollment": _clean_float(rec.get(enrollment_col)),
            "avg_revenue_per_student": _clean_float(rec.get("Avg revenue per student")),
            "revenue": _clean_float(rec.get(revenue_col)),
        })
    return rows


def read_sales_detail(path: Path) -> list[dict[str, Any]]:
    """Read a Sales Detail export (R3). 'Sales' is Maine sales tax, not a
    sales figure -- see DATA_DICTIONARY.md section 4."""
    df = _normalize_columns(pd.read_excel(path, sheet_name=0))

    rows: list[dict[str, Any]] = []
    for row_no, rec in enumerate(df.to_dict(orient="records"), start=1):
        rows.append({
            "row_no": row_no,
            "sale_date": _clean_date(rec.get("Date")),
            "item_number": _clean_str(rec.get("Item Number")),
            "item_name": _clean_str(rec.get("Item Name")),
            "qty": _clean_float(rec.get("Qty")),
            "amount": _clean_float(rec.get("Amount")),
            "discount": _clean_float(rec.get("Discount")),
            "tax": _clean_float(rec.get("Sales")),
            "total": _clean_float(rec.get("Total")),
            "note": _clean_str(rec.get("Note")),
            "payment_method": _clean_str(rec.get("Payment Method")),
            "family": _clean_str(rec.get("Family")),
            "student": _clean_str(rec.get("Student")),
            "class_name": _clean_str(rec.get("Class")),
        })
    return rows


def read_class_list(path: Path) -> list[dict[str, Any]]:
    """Read a Class List export (R4). Current session only -- see
    DATA_DICTIONARY.md section 1."""
    df = _normalize_columns(pd.read_excel(path, sheet_name=0))

    rows: list[dict[str, Any]] = []
    for row_no, rec in enumerate(df.to_dict(orient="records"), start=1):
        rows.append({
            "row_no": row_no,
            "class_name": _clean_str(rec.get("Class")),
            "description": _clean_str(rec.get("Description")),
            "instructors": _clean_str(rec.get("Instructors")),
            "status": _clean_str(rec.get("Status")),
            "session": _clean_str(rec.get("Session")),
            "start_date": _clean_date(rec.get("Start Date")),
            "end_date": _clean_date(rec.get("End Date")),
            "days": _clean_str(rec.get("Days")),
            "start_time": _clean_str(rec.get("Start Time")),
            "duration": _clean_str(rec.get("Duration")),
            "cat1": _clean_str(rec.get("Cat1")),
            "cat2": _clean_str(rec.get("Cat2")),
            "cat3": _clean_str(rec.get("Cat3")),
            "size": _clean_int(rec.get("Size")),
            "max_enrollment": _clean_int(rec.get("Max")),
            "tuition": _clean_float(rec.get("Tuition")),
        })
    return rows


def _clean_str(value: Any) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    return text or None


def _raw_str(value: Any) -> str | None:
    """Like _clean_str but does not strip whitespace -- see the comment at
    its call site in read_class_event_revenue for why that distinction
    matters here."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    return str(value)


def _clean_float(value: Any) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clean_int(value: Any) -> int | None:
    f = _clean_float(value)
    return int(f) if f is not None else None


def _clean_date(value: Any):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    ts = pd.Timestamp(value)
    if pd.isna(ts):
        return None
    return ts.date()

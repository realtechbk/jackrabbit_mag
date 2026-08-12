"""Parses a Jackrabbit Revenue Summary PDF into Cat1/Cat2/activity records.

This is a direct port of scripts/parse_rsr.py's parse() and label_for(), the
only non-trivial piece of engineering in the legacy analysis (CLAUDE.md). The
parsing algorithm -- including the documented traps -- is copied unchanged so
this importer reconciles the same way the legacy workbook does. Do not
"clean up" the regexes here without re-verifying against all four periods in
data/raw/; see DATA_DICTIONARY.md section 2 for what each trap protects
against:

  1. A Cat2 can share its Cat1's name (e.g. 'Open Gym'), producing several
     identically-labelled subtotal lines. The Cat1 subtotal is the LAST one
     in the section -- overwrite, not accumulate.
  2. Cat1 headings can start with '--' ('--Unapplied Payments--').
  3. Page headers repeat on every page and must be skipped.
  4. Long activity names wrap onto a second line with no numbers.
  5. An inverted date range returns $0.00 with no rows and no error -- always
     check the parsed period.

If scripts/parse_rsr.py is ever changed to fix a parsing bug, port the same
fix here.

IMPORTANT -- this parser only works with Poppler's `pdftotext`. The `-layout`
flag's column-alignment heuristic is implementation-specific: Xpdf (and
clones derived from it, including the one bundled with Git for Windows/MSYS2)
lay out this report's columns differently, wrapping numeric fields onto lines
that don't contain their row label. That breaks every regex above, and it
fails in a way that looks like a data problem (a reconciliation variance)
rather than an environment problem. check_pdftotext_is_poppler() exists
specifically so that failure mode surfaces as a clear, actionable error
instead -- callers should invoke it before run_pdftotext() whenever they're
about to process a real PDF for the first time in a process.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import TypedDict

from cfo_platform.core.exceptions import ConfigurationError

MONEY = r"-?[\d,]+\.\d{2}"


class ActivityLine(TypedDict):
    cat1: str | None
    cat2: str | None
    name: str
    enroll: int
    disc: float
    amt: float


class ParsedRevenueSummary(TypedDict):
    period: tuple[str, str] | None
    grand: dict[str, float | None]
    cat1: dict[str, list[float]]
    cat2: dict[tuple[str, str], list[float]]
    activities: list[ActivityLine]


def _resolve_pdftotext_path(pdftotext_path: str | Path | None) -> str:
    if pdftotext_path is not None:
        return str(pdftotext_path)
    from cfo_platform.settings import get_settings

    configured = get_settings().pdftotext_path
    return str(configured) if configured is not None else "pdftotext"


def check_pdftotext_is_poppler(pdftotext_path: str | Path | None = None) -> None:
    """Raise ConfigurationError unless the resolved `pdftotext` binary
    identifies itself as Poppler.

    Every pdftotext clone answers `-v`/`-h` with a version banner, but only
    Poppler's mentions "Poppler" -- Xpdf's says only 'Copyright ... Glyph &
    Cog, LLC' (Poppler forked from Xpdf and keeps that same attribution line,
    so checking for Glyph & Cog would not distinguish them; checking for the
    absence of "Poppler" is the reliable signal). The banner goes to stderr
    for both, and Xpdf's `-v` even exits non-zero (99) -- so this checks
    combined output text, not the exit code.
    """
    resolved = _resolve_pdftotext_path(pdftotext_path)
    try:
        result = subprocess.run(
            [resolved, "-v"], capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
    except FileNotFoundError as exc:
        raise ConfigurationError(
            f"pdftotext not found at {resolved!r}. Revenue Summary import requires Poppler's "
            f"pdftotext -- install it (e.g. `conda install -c conda-forge poppler`) and either "
            f"put it on PATH or set CFO_PDFTOTEXT_PATH to its full path."
        ) from exc

    banner = (result.stdout + result.stderr).strip()
    if "poppler" not in banner.lower():
        raise ConfigurationError(
            f"pdftotext at {resolved!r} is not a Poppler build -- Revenue Summary parsing depends "
            f"on Poppler's specific -layout column-alignment behaviour, and other builds (Xpdf and "
            f"its clones, including the one bundled with Git for Windows/MSYS2) render this report's "
            f"columns differently, silently breaking the parser. Detected banner: {banner!r}. "
            f"Install Poppler (e.g. `conda install -c conda-forge poppler`) and either put its "
            f"pdftotext first on PATH or set CFO_PDFTOTEXT_PATH to its full path."
        )


def run_pdftotext(pdf_path: Path, pdftotext_path: str | Path | None = None) -> str:
    """Run `pdftotext -layout` and return the extracted text.

    Requires a Poppler build of `pdftotext` -- see this module's docstring
    and check_pdftotext_is_poppler(), which callers should run first.
    Resolves the binary from `pdftotext_path`, then CFO_PDFTOTEXT_PATH
    (Settings.pdftotext_path), then falls back to "pdftotext" on PATH.
    Raises FileNotFoundError if it is missing, or
    subprocess.CalledProcessError if pdftotext itself fails.
    """
    resolved = _resolve_pdftotext_path(pdftotext_path)
    result = subprocess.run(
        [resolved, "-layout", str(pdf_path), "-"],
        capture_output=True,
        check=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout


def parse(text: str) -> ParsedRevenueSummary:
    """Parse pdftotext -layout output into Cat1/Cat2/activity records.

    Ported from scripts/parse_rsr.py:parse(), which took a file path; this
    takes the already-extracted text so callers control how the PDF is read.
    """
    lines = text.split("\n")

    period: tuple[str, str] | None = None
    grand: dict[str, float | None] = {"disc": None, "amt": None}
    cat1_totals: dict[str, list[float]] = {}
    cat2_totals: dict[tuple[str, str], list[float]] = {}
    activities: list[ActivityLine] = []

    cur1: str | None = None
    cur2: str | None = None

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            continue

        if period is None:
            m = re.search(r"(\d{1,2}/\d{1,2}/\d{4})\s*-\s*(\d{1,2}/\d{1,2}/\d{4})", line)
            if m and "Date:" not in line:
                period = (m.group(1), m.group(2))
                continue

        if "Date:" in line or "Revenue Summary" in line or line.strip().startswith("Cat1"):
            continue
        if "Total Revenue*" in line or line.strip().startswith("*Due to"):
            continue

        # grand total
        m = re.search(r"Totals:\s+(\d+)\s+(" + MONEY + r")\s+(" + MONEY + r")\s*$", line)
        if m:
            grand["disc"] = float(m.group(2).replace(",", ""))
            grand["amt"] = float(m.group(3).replace(",", ""))
            continue

        indent = len(line) - len(line.lstrip())
        body = line.strip()

        # Cat1 heading: starts at column 0 (may begin with '--', e.g. '--Unapplied Payments--')
        if indent == 0 and not re.match(r"^[\d,]", body) and "Subtotal" not in body:
            cur1 = body
            cur2 = None
            cat1_totals.setdefault(cur1, [0.0, 0.0])
            continue

        # subtotal lines
        m = re.match(r"^(.*?)\s+Subtotal:\s+(\d+)\s+(" + MONEY + r")\s+(" + MONEY + r")\s*$", body)
        if m:
            what = m.group(1).strip()
            disc = float(m.group(3).replace(",", ""))
            amt = float(m.group(4).replace(",", ""))
            if cur1 and what == cur1:
                # A Cat2 can share its Cat1's name (e.g. 'Open Gym'), producing several
                # identically-labelled subtotals. The Cat1 subtotal is always the last
                # one in the section, so overwrite rather than accumulate.
                cat1_totals[cur1] = [amt, disc]
            elif what in ("Cat2",):
                key = (cur1, "(blank)")
                cat2_totals.setdefault(key, [0.0, 0.0])
                cat2_totals[key][0] += amt
                cat2_totals[key][1] += disc
            elif what.startswith("Cat3") or what in ("Cat3",):
                pass
            else:
                # named Cat2 or Cat3 subtotal; treat as Cat2 if it matches cur2
                key = (cur1, what)
                cat2_totals.setdefault(key, [0.0, 0.0])
                cat2_totals[key][0] += amt
                cat2_totals[key][1] += disc
            continue

        # activity line with numbers
        m = re.match(r"^(.*?)\s+(\d+)\s+(" + MONEY + r")\s+(" + MONEY + r")\s*$", body)
        if m:
            name = m.group(1).strip()
            activities.append({
                "cat1": cur1, "cat2": cur2, "name": name,
                "enroll": int(m.group(2)),
                "disc": float(m.group(3).replace(",", "")),
                "amt": float(m.group(4).replace(",", "")),
            })
            continue

        # activity line with no enrollment column (rare)
        m = re.match(r"^(.*?)\s+(" + MONEY + r")\s+(" + MONEY + r")\s*$", body)
        if m:
            activities.append({
                "cat1": cur1, "cat2": cur2, "name": m.group(1).strip(),
                "enroll": 0,
                "disc": float(m.group(2).replace(",", "")),
                "amt": float(m.group(3).replace(",", "")),
            })
            continue

        # bare label -- a Cat2 or Cat3 heading
        if indent > 0 and "Subtotal" not in body and not re.search(MONEY, body):
            if indent <= 20:
                cur2 = body
            continue

    return {
        "period": period,
        "grand": grand,
        "cat1": dict(cat1_totals),
        "cat2": dict(cat2_totals),
        "activities": activities,
    }


def label_for(file_name: str, parsed: ParsedRevenueSummary) -> str:
    """Key a parsed report by year.

    Prefer a 4-digit year in the filename; fall back to the year in the
    report's own date range; last resort, the filename stem. Never crash on
    an unexpected filename.
    """
    m = re.search(r"(20\d{2})", file_name)
    if m:
        return m.group(1)
    period = parsed.get("period")
    if period:
        m = re.search(r"(20\d{2})", period[0])
        if m:
            return m.group(1)
    return file_name.rsplit(".", 1)[0]

"""Reconciliation checks for the Jackrabbit importer.

CLAUDE.md rule 1: every revenue figure must reconcile to the source report
total with zero variance, and a failed check must stop the pipeline, not
print a warning someone can ignore. These raise cfo_platform's typed
ReconciliationError -- see core/exceptions.py and
docs/architecture/overview.md's "reconciliation discipline" note.
"""

from __future__ import annotations

from cfo_platform.core.exceptions import ReconciliationError

# Money in these reports is stated to the cent; anything beyond float
# round-trip noise is a real mapping error, not a rounding artifact.
TOLERANCE = 0.01


def check_report_total_present(period_label: str, reported_amount: float | None) -> None:
    """DATA_DICTIONARY.md section 2, trap 5: an inverted date range returns
    $0.00 with no rows and no error from Jackrabbit itself -- catch it here."""
    if reported_amount is None or reported_amount == 0:
        raise ReconciliationError(
            f"Revenue Summary for period {period_label!r} has no usable grand total "
            f"(reported_amount={reported_amount!r}). An inverted date range returns "
            f"$0.00 with no rows and no error -- check the report's date range before "
            f"re-importing. Refusing to load."
        )


def check_cat1_reconciles_to_report(
    period_label: str, cat1_sum: float, reported_amount: float
) -> None:
    """The parser's own invariant (scripts/parse_rsr.py): SUM(cat1 totals)
    must equal the report's stated grand total."""
    variance = round(cat1_sum - reported_amount, 2)
    if abs(variance) > TOLERANCE:
        raise ReconciliationError(
            f"Revenue Summary for period {period_label!r}: Cat1 totals sum to "
            f"{cat1_sum:.2f} but the report states {reported_amount:.2f} "
            f"(variance {variance:+.2f}). Must be 0.00 per CLAUDE.md rule 1. Refusing to load."
        )


def check_fact_revenue_reconciles_to_report(
    period_label: str, fact_revenue_sum: float, reported_amount: float
) -> None:
    """After service-line mapping is applied, the mapped total must still tie
    out. A gap here means a Cat1/Cat2 combination has no entry in
    mapping.CATEGORY_MAP -- new Jackrabbit category, not a parsing bug."""
    variance = round(fact_revenue_sum - reported_amount, 2)
    if abs(variance) > TOLERANCE:
        raise ReconciliationError(
            f"Revenue Summary for period {period_label!r}: mapped service-line revenue "
            f"sums to {fact_revenue_sum:.2f} but the report states {reported_amount:.2f} "
            f"(variance {variance:+.2f}). Likely an unmapped Cat1/Cat2 combination -- "
            f"see importers/jackrabbit/mapping.py CATEGORY_MAP. Refusing to load."
        )

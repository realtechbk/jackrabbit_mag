"""Verifies the ported parser (revenue_summary_parser.py) behaves exactly
like scripts/parse_rsr.py, including its documented traps
(DATA_DICTIONARY.md section 2). Uses a hand-built fixture that mimics
correctly-rendered `pdftotext -layout` output rather than a real PDF,
because the poppler build this repo's traditional pipeline expects is not
what ships in this environment -- see the module docstring in
importers/jackrabbit/importer.py's reconciliation tests for why that
matters and how it's handled.
"""

from __future__ import annotations

from cfo_platform.importers.jackrabbit.revenue_summary_parser import label_for, parse

FIXTURE_TEXT = """\
Date: 7/28/2026 10:00:00 AM             Revenue Summary                                              Page 1

                                        1/1/2025 - 12/31/2025

Cat1  Cat2              Cat3  Activity                                                      Enrollment Discount Amount

--Unapplied Payments--
                    --No Activity Name--                                                    0  0.00  100.00
                    Cat2 Subtotal:                                                          0  0.00  100.00
--Unapplied Payments-- Subtotal:                                                            0  0.00  100.00

Open Gym
      Open Gym
                    MAG Day Open Gym                                                        0  0.00  20.00
      Open Gym Subtotal:                                                                    0  0.00  20.00
      Open Gym
                    MAG Evening Open Gym                                                    0  0.00  25.00
      Open Gym Subtotal:                                                                    0  0.00  45.00
Open Gym Subtotal:                                                                          0  0.00  45.00

Recreational
                    --No Activity Name--                                                    0  0.00  30.00
                    Cat2 Subtotal:                                                          0  0.00  30.00
                    Summer Tumble Series                                                    0  0.00  50.00
                    Cat2 Subtotal:                                                          0  0.00  50.00
      Rec Girls
                    Girls G1                                                                0  0.00  200.00
                    Rec Girls Subtotal:                                                     0  0.00  200.00
Recreational Subtotal:                                                                      0  0.00  280.00

Totals:                                                                                      0  0.00  425.00
"""


def test_parses_period():
    parsed = parse(FIXTURE_TEXT)
    assert parsed["period"] == ("1/1/2025", "12/31/2025")


def test_grand_total():
    parsed = parse(FIXTURE_TEXT)
    assert parsed["grand"]["amt"] == 425.00
    assert parsed["grand"]["disc"] == 0.00


def test_cat1_subtotal_overwrites_not_accumulates():
    """Trap 1 (DATA_DICTIONARY.md section 2): a Cat2 can share its Cat1's
    name, producing repeated identically-labelled subtotal lines. The Cat1
    total is the LAST one printed (45.00), not the sum of every occurrence
    (20 + 45 = 65, which is what an accumulate-instead-of-overwrite bug
    would produce)."""
    parsed = parse(FIXTURE_TEXT)
    assert parsed["cat1"]["Open Gym"] == [45.00, 0.0]


def test_cat1_heading_starting_with_double_hyphen():
    """Trap 2: Cat1 headings can start with '--' ('--Unapplied Payments--')
    and must not be excluded by the heading regex."""
    parsed = parse(FIXTURE_TEXT)
    assert parsed["cat1"]["--Unapplied Payments--"] == [100.00, 0.0]


def test_cat1_sum_reconciles_to_grand_total():
    """The parser's own gate (CLAUDE.md rule 1): SUM(cat1 totals) must equal
    the report's stated grand total, to the penny."""
    parsed = parse(FIXTURE_TEXT)
    cat1_sum = sum(v[0] for v in parsed["cat1"].values())
    assert round(cat1_sum - parsed["grand"]["amt"], 2) == 0.0


def test_recreational_cat1_total_is_its_own_subtotal_line_not_derived():
    parsed = parse(FIXTURE_TEXT)
    assert parsed["cat1"]["Recreational"] == [280.00, 0.0]


def test_recreational_named_cat2_total():
    parsed = parse(FIXTURE_TEXT)
    assert parsed["cat2"][("Recreational", "Rec Girls")] == [200.00, 0.0]


def test_recreational_blank_cat2_activities_are_flagged_with_none_cat2():
    """Cat1 Recreational + blank Cat2 activities carry cat2=None (not the
    '(blank)' sentinel used in cat2_totals) -- see
    mapping.split_recreational_blank_cat2, which switches on this."""
    parsed = parse(FIXTURE_TEXT)
    blank_cat2_activities = [
        a for a in parsed["activities"] if a["cat1"] == "Recreational" and a["cat2"] is None
    ]
    names = {a["name"]: a["amt"] for a in blank_cat2_activities}
    assert names == {"--No Activity Name--": 30.00, "Summer Tumble Series": 50.00}


def test_label_for_prefers_year_in_filename():
    parsed = parse(FIXTURE_TEXT)
    assert label_for("RevenueSummary_2025.pdf", parsed) == "2025"


def test_label_for_falls_back_to_period_year():
    parsed = parse(FIXTURE_TEXT)
    assert label_for("weird_filename.pdf", parsed) == "2025"

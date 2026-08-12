"""Cat1/Cat2 -> service-line mapping. Single source of truth for both the
DuckDB dimensions (dim_service_line, dim_jackrabbit_category_map) and the
in-Python mapping used during Importer.transform() (which runs with no DB
connection -- see importers/base.py).

Ported from the legacy analysis, not re-derived:
  - SERVICE_LINES = the ROWS constant in scripts/build_perf_v8.py (label,
    row_kind, unit_type, in the same order -- sort_order preserves the grid).
  - CATEGORY_MAP = DATA_DICTIONARY.md section 5 (Cat1 value reference / Cat2
    values under Recreational).

Two splits are NOT plain (cat1, cat2) lookups and are implemented as
functions instead -- see each docstring for why:
  - split_recreational_blank_cat2 (R1 Revenue Summary only)
  - map_class_event_row (R2 Class/Event Revenue Summary; also folds in the
    handful of classes with no Category 1 at all)
"""

from __future__ import annotations

CLIENT_ID = "mag"

NO_ACTIVITY_NAME = "--No Activity Name--"

# (service_line_key, revenue_group, sub_group, row_kind, unit_type,
#  is_class_enrolment_comparable, sort_order, notes)
SERVICE_LINES: list[tuple[str, str, str, str, str, bool, int, str]] = [
    ("Recreational -- Preschool (The Jungle)", "Recreational", "Preschool (The Jungle)", "E", "enrolment", True, 1,
     "Cat2 Pre-School + Parent-Child (First Flight)."),
    ("Recreational -- Girls Wings", "Recreational", "Girls Wings", "E", "enrolment", True, 2,
     "Cat2 Rec Girls. Largest single line."),
    ("Recreational -- Boys Wings", "Recreational", "Boys Wings", "E", "enrolment", True, 3,
     "Cat2 Rec Boys."),
    ("Recreational -- Tumbling", "Recreational", "Tumbling", "E", "enrolment", True, 4,
     "Cat2 Tumble (Combined)."),
    ("Recreational -- Workshops & Class Series", "Recreational", "Workshops & Class Series", "E", "enrolment", True, 5,
     "Cat1 Recreational, blank Cat2, activity name present (not --No Activity Name--)."),
    ("Recreational -- Unlinked Tuition", "Recreational", "Unlinked Tuition", "F", "n/a", False, 6,
     "Cat1 Recreational, blank Cat2, activity = --No Activity Name--. Data-quality bucket, not a service."),
    ("Competitive -- Pre-Team", "Competitive", "Pre-Team", "E", "enrolment", True, 7,
     "Cat2 Pre-Team (Invite Only) -- 2023 only under current mapping; folds into Wings rows from 2024."),
    ("Competitive -- American Flyers Teams", "Competitive", "American Flyers Teams", "E", "enrolment", True, 8,
     "Cat1 Team. Enrolment double-counts athletes (billing group + practice group + roster) -- CLAUDE.md."),
    ("Ancillary -- Open Gym", "Ancillary", "Open Gym", "U", "booking", False, 9,
     "Cat1 Open Gym."),
    ("Ancillary -- Annual Membership Fees", "Ancillary", "Annual Membership Fees", "U", "membership", False, 10,
     "Cat1 Annual Membership. Units are a formula (revenue / 45), not a headcount -- CLAUDE.md rule 3."),
    ("Ancillary -- Birthday Parties", "Ancillary", "Birthday Parties", "U", "party", False, 11,
     "Cat1 Birthday Parties."),
    ("Ancillary -- Pro Shop", "Ancillary", "Pro Shop", "U", "item sold", False, 12,
     "Cat1 ProShop. Cost of sales here is inventory cost, not coach labour."),
    ("Ancillary -- Private Lessons", "Ancillary", "Private Lessons", "U", "lesson", False, 13,
     "Cat1 Private Lessons."),
    ("Ancillary -- Gift Certificates", "Ancillary", "Gift Certificates", "U", "certificate", False, 14,
     "Cat1 Gift Certificate."),
    ("Ancillary -- Non-Instructional Time", "Ancillary", "Non-Instructional Time", "N", "n/a", False, 15,
     "Cat1 Non-Instructional time -- present 2025 only."),
    ("Other -- Tumble (stray Cat1)", "Other", "Tumble (stray Cat1)", "F", "n/a", False, 16,
     "Stray Cat1 Tumble (distinct from Cat2 Tumble (Combined)) -- a mis-tag, belongs under Recreational -- Tumbling."),
    ("Review -- Unapplied Payments", "Review", "Unapplied Payments", "F", "n/a", False, 17,
     "Cat1 --Unapplied Payments--. Data-quality bucket, not a service."),
    ("EXCLUDE -- Staff", "EXCLUDE", "Staff", "X", "n/a", False, 18,
     "Cat1 Staff. Not customer revenue."),
]

SERVICE_LINE_BY_KEY = {row[0]: row for row in SERVICE_LINES}

PRESCHOOL = "Recreational -- Preschool (The Jungle)"
GIRLS_WINGS = "Recreational -- Girls Wings"
BOYS_WINGS = "Recreational -- Boys Wings"
TUMBLING = "Recreational -- Tumbling"
WORKSHOPS = "Recreational -- Workshops & Class Series"
UNLINKED_TUITION = "Recreational -- Unlinked Tuition"
PRE_TEAM = "Competitive -- Pre-Team"
TEAM = "Competitive -- American Flyers Teams"

# (cat1, cat2) -> service_line_key. cat2 == '' is the sentinel for a blank
# Cat2 that maps 1:1 (i.e. every Cat1 case except Recreational, whose blank
# Cat2 needs activity-level data -- see split_recreational_blank_cat2 below).
CATEGORY_MAP: dict[tuple[str, str], str] = {
    ("Team", ""): TEAM,
    ("Annual Membership", ""): "Ancillary -- Annual Membership Fees",
    ("Open Gym", ""): "Ancillary -- Open Gym",
    ("ProShop", ""): "Ancillary -- Pro Shop",
    ("Private Lessons", ""): "Ancillary -- Private Lessons",
    ("Staff", ""): "EXCLUDE -- Staff",
    ("--Unapplied Payments--", ""): "Review -- Unapplied Payments",
    ("Birthday Parties", ""): "Ancillary -- Birthday Parties",
    ("Gift Certificate", ""): "Ancillary -- Gift Certificates",
    ("Non-Instructional time", ""): "Ancillary -- Non-Instructional Time",
    ("Tumble", ""): "Other -- Tumble (stray Cat1)",
    ("Recreational", "Pre-School"): PRESCHOOL,
    ("Recreational", "Parent-Child"): PRESCHOOL,
    ("Recreational", "Rec Girls"): GIRLS_WINGS,
    ("Recreational", "Rec Boys"): BOYS_WINGS,
    ("Recreational", "Tumble (Combined)"): TUMBLING,
    ("Recreational", "Pre-Team (Invite Only)"): PRE_TEAM,
}


def split_recreational_blank_cat2(activity_name: str) -> str:
    """R1 only: Cat1 Recreational with a blank Cat2 splits at the activity
    level (DATA_DICTIONARY.md section 5) -- '--No Activity Name--' is
    Unlinked Tuition, any real class name is Workshops & Class Series.
    """
    if activity_name.strip() == NO_ACTIVITY_NAME:
        return UNLINKED_TUITION
    return WORKSHOPS


def map_r1_cat1_total(cat1: str) -> str | None:
    """R1 Cat1-level total -> service_line_key, for every Cat1 except
    Recreational (which is mapped via its Cat2 totals instead, since a
    single Cat1 total would blend Preschool/Girls/Boys/Tumbling/etc.)."""
    if cat1 == "Recreational":
        return None
    return CATEGORY_MAP.get((cat1, ""))


def map_r1_cat2_total(cat2: str) -> str | None:
    """R1 Cat2-level total under Cat1 Recreational -> service_line_key.
    '(blank)' is the sentinel raw_revenue_summary_parser uses for a Cat2
    heading that never appears in the source text -- handled by the caller
    via split_recreational_blank_cat2 instead, using activity-level data."""
    return CATEGORY_MAP.get(("Recreational", cat2))


def map_class_event_row(cat1: str | None, cat2: str | None) -> tuple[str | None, bool]:
    """R2 Class/Event Revenue row -> (service_line_key, is_comparable).

    Every R2 row is already a real class, so Recreational + blank Cat2 maps
    straight to Workshops & Class Series (no Unlinked Tuition equivalent --
    that bucket only exists because R1 has '--No Activity Name--' lines with
    no class at all). A handful of classes carry no Category 1 whatsoever
    (DATA_DICTIONARY.md section 1, "three classes missing Category 1
    entirely"); verified against 2023/2024's known Workshops enrolment counts
    (1 and 5), these fold into Workshops & Class Series too.

    Returns (None, False) for rows this mapping doesn't cover at all (Team
    apparel via Store, an unexpected new category, etc.) -- those rows are
    still preserved in fact_class_enrolment, just excluded from the
    class-enrolment-comparable subtotal (CLAUDE.md rule 2).
    """
    cat1 = cat1 or ""
    cat2 = cat2 or ""

    if cat1 == "" or (cat1 == "Recreational" and cat2 == ""):
        key = WORKSHOPS
    else:
        # Try the exact (cat1, cat2) pair first (this is what every one of
        # the 7 comparable rows matches on). Some non-comparable Cat1s repeat
        # their own name as Cat2 in R2 even though R1 treats them as having
        # a blank Cat2 (e.g. Open Gym rows carry Category 2 = 'Open Gym') --
        # fall back to the blank-Cat2 mapping for that Cat1 rather than
        # reporting a real, known category as unmapped.
        key = CATEGORY_MAP.get((cat1, cat2))
        if key is None and cat1 != "Recreational":
            key = CATEGORY_MAP.get((cat1, ""))
        if key is None:
            return None, False

    is_comparable = SERVICE_LINE_BY_KEY[key][5]
    return key, is_comparable


def seed_dim_service_line(conn) -> None:
    conn.executemany(
        """
        INSERT INTO dim_service_line
            (service_line_key, revenue_group, sub_group, row_kind, unit_type,
             is_class_enrolment_comparable, sort_order, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (service_line_key) DO NOTHING
        """,
        SERVICE_LINES,
    )


def seed_dim_category_map(conn) -> None:
    rows = [(CLIENT_ID, cat1, cat2, key) for (cat1, cat2), key in CATEGORY_MAP.items()]
    conn.executemany(
        """
        INSERT INTO dim_jackrabbit_category_map (client_id, cat1, cat2, service_line_key)
        VALUES (?, ?, ?, ?)
        ON CONFLICT (client_id, cat1, cat2) DO NOTHING
        """,
        rows,
    )

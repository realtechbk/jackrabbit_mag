from __future__ import annotations

from cfo_platform.importers.jackrabbit import mapping


def test_direct_cat1_mappings():
    assert mapping.map_r1_cat1_total("Team") == mapping.TEAM
    assert mapping.map_r1_cat1_total("Open Gym") == "Ancillary -- Open Gym"
    assert mapping.map_r1_cat1_total("Staff") == "EXCLUDE -- Staff"
    assert mapping.map_r1_cat1_total("--Unapplied Payments--") == "Review -- Unapplied Payments"


def test_recreational_has_no_direct_cat1_mapping():
    """Recreational must be mapped via its Cat2 totals, not its Cat1 total,
    or Preschool/Girls/Boys/Tumbling revenue would all blend into one row."""
    assert mapping.map_r1_cat1_total("Recreational") is None


def test_recreational_cat2_mappings():
    assert mapping.map_r1_cat2_total("Rec Girls") == mapping.GIRLS_WINGS
    assert mapping.map_r1_cat2_total("Rec Boys") == mapping.BOYS_WINGS
    assert mapping.map_r1_cat2_total("Pre-School") == mapping.PRESCHOOL
    assert mapping.map_r1_cat2_total("Parent-Child") == mapping.PRESCHOOL
    assert mapping.map_r1_cat2_total("Pre-Team (Invite Only)") == mapping.PRE_TEAM


def test_split_recreational_blank_cat2_by_activity_name():
    assert mapping.split_recreational_blank_cat2("--No Activity Name--") == mapping.UNLINKED_TUITION
    assert mapping.split_recreational_blank_cat2("Summer Tumble Series") == mapping.WORKSHOPS


def test_map_class_event_row_direct_cat1():
    key, comparable = mapping.map_class_event_row("Team", None)
    assert key == mapping.TEAM
    assert comparable is True

    key, comparable = mapping.map_class_event_row("Open Gym", "Open Gym")
    assert key == "Ancillary -- Open Gym"
    assert comparable is False


def test_map_class_event_row_recreational_blank_cat2_is_workshops():
    """Every R2 row is a real class, so blank Cat2 under Recreational maps
    straight to Workshops & Class Series -- no Unlinked Tuition equivalent
    here (that bucket only exists because R1 has --No Activity Name--
    lines with no class at all)."""
    key, comparable = mapping.map_class_event_row("Recreational", None)
    assert key == mapping.WORKSHOPS
    assert comparable is True

    key, comparable = mapping.map_class_event_row("Recreational", "")
    assert key == mapping.WORKSHOPS


def test_map_class_event_row_missing_cat1_folds_into_workshops():
    """A handful of classes carry no Category 1 at all (DATA_DICTIONARY.md
    section 1); verified against the known 2023/2024 Workshops enrolment
    counts, these fold into Workshops & Class Series."""
    key, comparable = mapping.map_class_event_row(None, None)
    assert key == mapping.WORKSHOPS
    assert comparable is True


def test_map_class_event_row_unmapped_combo_returns_none_not_a_guess():
    key, comparable = mapping.map_class_event_row("Some New Category", "Some New Subcategory")
    assert key is None
    assert comparable is False


def test_every_category_map_target_exists_as_a_service_line():
    for service_line_key in mapping.CATEGORY_MAP.values():
        assert service_line_key in mapping.SERVICE_LINE_BY_KEY


def test_is_class_enrolment_comparable_matches_the_seven_e_rows():
    """CLAUDE.md rule 2 / CURRENT_STATUS.md: exactly 7 rows are comparable
    class-enrolment rows."""
    comparable = [key for key, row in mapping.SERVICE_LINE_BY_KEY.items() if row[5]]
    assert len(comparable) == 7

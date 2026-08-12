from __future__ import annotations

from cfo_platform.importers.jackrabbit.dedupe import mark_duplicate_rows


def _row(row_no, class_event, session, cat3, enrollment):
    return {
        "row_no": row_no, "class_event": class_event, "session": session, "cat3": cat3,
        "enrollment": enrollment,
    }


def test_repeated_class_session_cat3_marks_second_occurrence_as_duplicate():
    """Documented example (DATA_DICTIONARY.md section 3): 'MAG Open Gym'
    appears twice in 2023, both rows showing enrolment 1,127."""
    rows = [
        _row(1, "MAG Open Gym", None, None, 1127),
        _row(2, "MAG Open Gym", None, None, 1127),
    ]
    result = mark_duplicate_rows(rows)
    assert [r["is_duplicate_row"] for r in result] == [False, True]


def test_distinct_classes_sharing_a_name_after_whitespace_differences_are_not_merged():
    """A trailing-whitespace difference in the exported class name can mean
    two genuinely distinct Jackrabbit class records, not a split of the same
    class across two revenue rows -- see readers.py's _raw_str comment.
    Verified against real 2023 data: stripping whitespace before the dedup
    key undercounts Rec Girls enrolment by 10."""
    rows = [
        _row(1, "White Wings/Intermediate Th 6:30p", "2023-24 Rec", "Girls G2", 10),
        _row(2, "White Wings/Intermediate Th 6:30p ", "2023-24 Rec", "Girls G2", 4),
    ]
    result = mark_duplicate_rows(rows)
    assert [r["is_duplicate_row"] for r in result] == [False, False]


def test_first_occurrence_by_row_order_is_kept_regardless_of_value():
    """Not every duplicate pair has an identical enrolment value on both
    rows -- keep whichever appears first in the export, deterministically."""
    rows = [
        _row(1, "Blue Wings/Advanced W 6:30p", "2023-24 Rec", "Girls G3", 17),
        _row(2, "Blue Wings/Advanced W 6:30p", "2023-24 Rec", "Girls G3", 20),
    ]
    result = mark_duplicate_rows(rows)
    kept = [r for r in result if not r["is_duplicate_row"]]
    assert len(kept) == 1
    assert kept[0]["enrollment"] == 17


def test_unrelated_rows_with_no_shared_key_are_never_marked_duplicate():
    rows = [
        _row(1, "Girls G1 Class", "2023-24 Rec", "Girls G1", 10),
        _row(2, "Boys B1 Class", "2023-24 Rec", "Boys B1", 8),
    ]
    result = mark_duplicate_rows(rows)
    assert [r["is_duplicate_row"] for r in result] == [False, False]


def test_dedup_key_ignores_row_order_in_the_input_list():
    """De-duplication is applied in row_no order regardless of how the
    caller happens to pass the rows in."""
    rows = [
        _row(2, "MAG Open Gym", None, None, 1127),
        _row(1, "MAG Open Gym", None, None, 1127),
    ]
    result = mark_duplicate_rows(rows)
    by_row_no = {r["row_no"]: r["is_duplicate_row"] for r in result}
    assert by_row_no == {1: False, 2: True}

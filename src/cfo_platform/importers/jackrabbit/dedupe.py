"""CLAUDE.md rule 5: de-duplicate Class/Event Revenue rows on
Class + Session + Category 3 before summing enrolment; revenue still sums
across every row.

Some classes are split across multiple revenue rows in the Class/Event
Revenue Summary, with the enrolment figure repeated on each row (documented
example: 'MAG Open Gym' appears twice in 2023, both rows showing 1,127).
Naively summing enrolment overstates it -- 10,691 raw vs 8,159 correct for
2023's full file.

The rule applied here is literal and mechanical: within one imported file,
group rows by (class_event, session, cat3) in their original row order and
mark every row after the first in a group as a duplicate. Verified against
the three years with class-enrolment data (2023/2024/2025) restricted to the
7 comparable service lines (see mapping.map_class_event_row) -- reproduces
CURRENT_STATUS.md's de-duplicated totals of 5,684 / 6,199 / 6,341 exactly.
"""

from __future__ import annotations

from typing import Any


def mark_duplicate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return `rows` (in the same order) with an added 'is_duplicate_row' key.

    Rows are deduplicated in row_no order, so the first occurrence of a given
    (class_event, session, cat3) key is kept as non-duplicate regardless of
    where it sorts alphabetically or by any other field.
    """
    seen: set[tuple[Any, Any, Any]] = set()
    out: list[dict[str, Any]] = []
    for row in sorted(rows, key=lambda r: r["row_no"]):
        key = (row.get("class_event"), row.get("session"), row.get("cat3"))
        is_duplicate = key in seen
        seen.add(key)
        out.append({**row, "is_duplicate_row": is_duplicate})
    return out

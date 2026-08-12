-- 0003_mag_service_line_facts: MAG-specific dimensions and analytical facts.
--
-- Client-scoped per docs/architecture/data-model.md's convention (prefixed
-- once more than one client has custom tables -- MAG is first, so the prefix
-- starts now). Ported from the legacy analysis rather than re-derived:
--   - dim_service_line = the ROWS constant in scripts/build_perf_v8.py
--     (label, row_kind, unit_type, in that exact order -- sort_order below
--     preserves the grid's row order).
--   - dim_jackrabbit_category_map = DATA_DICTIONARY.md section 5
--     (Cat1 value reference / Cat2 values under Recreational).
--
-- Neither dimension is seeded with INSERT statements here. The Importer's
-- transform() step runs in pure Python with no DB connection (see
-- importers/base.py), so the mapping has to exist as Python data regardless
-- -- importers/jackrabbit/mapping.py is that single source of truth, and
-- JackrabbitClassImporter.load() upserts these two tables from it on every
-- run (idempotent: INSERT ... ON CONFLICT DO NOTHING). Duplicating the seed
-- as static SQL here would let the two drift.
--
-- Two rules from CLAUDE.md are structural here, not just documented:
--   rule 2 (never sum # Units Sold across rows) -> is_class_enrolment_comparable
--     marks exactly the 7 rows the legacy 'Subtotal - class enrolments only'
--     covers; nothing computes a whole-column SUM over fact_class_enrolment.
--   rule 5 (de-duplicate on Class + Session + Cat3) -> fact_class_enrolment
--     carries is_duplicate_row so the dedup decision is auditable, not
--     silently applied and discarded.
--
-- One exception is NOT encoded in dim_jackrabbit_category_map: Cat1
-- Recreational with a blank Cat2 in the REVENUE SUMMARY (R1) does not map to
-- a single service row. Per DATA_DICTIONARY.md section 5, it splits at the
-- ACTIVITY level by whether the activity name is '--No Activity Name--'
-- (-> Unlinked Tuition) or a real class name (-> Workshops & Class Series).
-- That split needs raw_revenue_summary_activities, not the cat1/cat2 totals
-- this map table is keyed on, so it is implemented in code
-- (importers/jackrabbit/mapping.py: split_recreational_blank_cat2) rather
-- than as a row here. The CLASS/EVENT REVENUE report (R2) has no equivalent
-- split -- every R2 row is already a real class, so Recreational + blank
-- Cat2 there maps straight to Workshops & Class Series (see
-- mapping.py: map_class_event_row).

CREATE TABLE IF NOT EXISTS dim_service_line (
    service_line_key VARCHAR PRIMARY KEY,   -- '[Revenue Group] -- [Sub Group]'
    revenue_group     VARCHAR NOT NULL,     -- Recreational | Competitive | Ancillary | Review | EXCLUDE | Other
    sub_group         VARCHAR NOT NULL,
    row_kind          VARCHAR NOT NULL,     -- E enrolment-comparable | U other unit | F data-quality flag | N new/small n-a | X excluded
    unit_type         VARCHAR NOT NULL,     -- enrolment | booking | membership | party | item sold | lesson | certificate | n/a
    is_class_enrolment_comparable BOOLEAN NOT NULL,
    sort_order        INTEGER NOT NULL,
    notes             VARCHAR
);

CREATE TABLE IF NOT EXISTS dim_jackrabbit_category_map (
    client_id        VARCHAR NOT NULL,
    cat1             VARCHAR NOT NULL,
    cat2             VARCHAR NOT NULL,      -- '' sentinel for a blank Cat2 that maps 1:1 (see file header for the R1 blank-Cat2 exception that does NOT live here)
    service_line_key VARCHAR NOT NULL REFERENCES dim_service_line(service_line_key),
    PRIMARY KEY (client_id, cat1, cat2)
);

-- R1-derived revenue, grained at one row per (period, cat1, cat2) mapped
-- unit -- either a Cat1 total (most rows) or a Cat2 total under
-- Recreational, or one of the two activity-level splits of Recreational's
-- blank-Cat2 bucket. SUM(net_amount) per (client_id, period_label) must
-- equal raw_revenue_summary_totals.reported_amount for that period's
-- source_file_id -- enforced by the importer's reconciliation gate at load
-- time (CLAUDE.md rule 1), not just checked after the fact.
CREATE TABLE IF NOT EXISTS fact_revenue (
    client_id        VARCHAR NOT NULL,
    period_label     VARCHAR NOT NULL,
    source_file_id   VARCHAR NOT NULL REFERENCES source_files(source_file_id),
    cat1             VARCHAR NOT NULL,
    cat2             VARCHAR NOT NULL,
    service_line_key VARCHAR NOT NULL REFERENCES dim_service_line(service_line_key),
    derivation       VARCHAR NOT NULL,   -- cat1_total | cat2_total | activity_split:unlinked_tuition | activity_split:workshops
    net_amount       DOUBLE NOT NULL,
    discount_amount  DOUBLE NOT NULL
);

-- R2-derived class enrolment, one row per raw Class/Event Revenue line.
-- is_duplicate_row implements CLAUDE.md rule 5: revenue sums across every
-- row for a period; enrolment sums only WHERE NOT is_duplicate_row, over
-- rows where dim_service_line.is_class_enrolment_comparable is true.
CREATE TABLE IF NOT EXISTS fact_class_enrolment (
    client_id        VARCHAR NOT NULL,
    period_label     VARCHAR NOT NULL,
    source_file_id   VARCHAR NOT NULL REFERENCES source_files(source_file_id),
    class_event      VARCHAR NOT NULL,
    session          VARCHAR,
    cat1             VARCHAR,
    cat2             VARCHAR,
    cat3             VARCHAR,
    service_line_key VARCHAR REFERENCES dim_service_line(service_line_key),
    enrollment       DOUBLE NOT NULL,
    revenue          DOUBLE NOT NULL,
    is_duplicate_row BOOLEAN NOT NULL
);

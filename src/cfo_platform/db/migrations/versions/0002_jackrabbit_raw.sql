-- 0002_jackrabbit_raw: landing tables for Jackrabbit Class source exports.
--
-- source_files is the lineage/dedupe spine: one row per file ingested, keyed
-- by (client_id, file_sha256) so re-importing byte-identical export is a
-- no-op (CLAUDE.md rule 1 discipline applied to the import layer itself, not
-- just to revenue mapping). Every raw_* row carries source_file_id back to
-- it, and source_files carries import_run_id back to import_runs (0001_init)
-- -- that FK chain is the full lineage trail from a warehouse row back to
-- the run that loaded it and the file it came from.
--
-- Raw tables preserve each report close to its original shape (CLAUDE.md's
-- report definitions in DATA_DICTIONARY.md sections 2-4). They are never
-- overwritten in place -- a corrected re-export of the same period is a new
-- source_file row, so history of what was imported when is never lost.

CREATE TABLE IF NOT EXISTS source_files (
    source_file_id  VARCHAR PRIMARY KEY,
    client_id       VARCHAR NOT NULL,
    import_run_id   VARCHAR NOT NULL REFERENCES import_runs(run_id),
    report_type     VARCHAR NOT NULL,  -- revenue_summary | class_event_revenue | sales_detail | class_list
    file_path       VARCHAR NOT NULL,
    file_name       VARCHAR NOT NULL,
    file_sha256     VARCHAR NOT NULL,
    file_bytes      BIGINT NOT NULL,
    period_label    VARCHAR,           -- e.g. '2023', '2026YTD' -- label_for() in the ported parser
    period_start    DATE,
    period_end      DATE,
    row_count       INTEGER NOT NULL,
    imported_at     TIMESTAMP NOT NULL DEFAULT current_timestamp,
    UNIQUE (client_id, file_sha256)
);

-- R1 Revenue Summary (PDF, parsed via pdftotext -layout). One row per parsed
-- activity line -- the finest grain the report exposes. cat2 here is
-- whatever the parser's indentation logic captured as the innermost heading
-- above the activity line (see revenue_summary_parser.py's port of the
-- 'cur2' trap from scripts/parse_rsr.py) -- it is not guaranteed to be a
-- clean Category-2-only value, which is why cat1_totals/cat2_totals below
-- are kept as separately-parsed, independently-reconciling numbers rather
-- than derived by summing this table.
CREATE TABLE IF NOT EXISTS raw_revenue_summary_activities (
    source_file_id  VARCHAR NOT NULL REFERENCES source_files(source_file_id),
    line_no         INTEGER NOT NULL,
    cat1            VARCHAR,
    cat2            VARCHAR,
    activity_name   VARCHAR NOT NULL,
    enrollment_raw  INTEGER,
    discount_amount DOUBLE NOT NULL,
    net_amount      DOUBLE NOT NULL
);

-- Cat1-level subtotals as printed on the report (the 'Subtotal:' line whose
-- label matches the Cat1 heading -- last-one-wins per the parser's
-- documented overwrite rule, since a Cat2 can share its Cat1's name).
CREATE TABLE IF NOT EXISTS raw_revenue_summary_cat1_totals (
    source_file_id  VARCHAR NOT NULL REFERENCES source_files(source_file_id),
    cat1            VARCHAR NOT NULL,
    discount_amount DOUBLE NOT NULL,
    net_amount      DOUBLE NOT NULL,
    PRIMARY KEY (source_file_id, cat1)
);

-- Cat2-level subtotals (accumulated, since distinct Cat2 labels don't share
-- the overwrite trap that Cat1 does). '(blank)' is the sentinel used by the
-- parser for a Cat2 heading that never appears in the source text.
CREATE TABLE IF NOT EXISTS raw_revenue_summary_cat2_totals (
    source_file_id  VARCHAR NOT NULL REFERENCES source_files(source_file_id),
    cat1            VARCHAR NOT NULL,
    cat2            VARCHAR NOT NULL,
    discount_amount DOUBLE NOT NULL,
    net_amount      DOUBLE NOT NULL,
    PRIMARY KEY (source_file_id, cat1, cat2)
);

-- The report's own printed grand total -- the reconciliation target.
CREATE TABLE IF NOT EXISTS raw_revenue_summary_totals (
    source_file_id    VARCHAR PRIMARY KEY REFERENCES source_files(source_file_id),
    reported_discount DOUBLE NOT NULL,
    reported_amount   DOUBLE NOT NULL
);

-- R2 Class/Event Revenue Summary (xlsx). One row per exported line, before
-- de-duplication -- fact_class_enrolment (0003) is where CLAUDE.md rule 5's
-- de-dup is applied and recorded.
CREATE TABLE IF NOT EXISTS raw_class_event_revenue_rows (
    source_file_id          VARCHAR NOT NULL REFERENCES source_files(source_file_id),
    row_no                  INTEGER NOT NULL,
    location                VARCHAR,
    class_event             VARCHAR,
    cat1                    VARCHAR,
    cat2                    VARCHAR,
    cat3                    VARCHAR,
    session                 VARCHAR,
    days                    VARCHAR,
    enrollment              DOUBLE,
    avg_revenue_per_student DOUBLE,
    revenue                 DOUBLE
);

-- R3 Sales Detail (xls). Item-level; preserved as-is. No unit/cost analytics
-- are built on this yet -- see docs/architecture/data-model.md.
CREATE TABLE IF NOT EXISTS raw_sales_detail_rows (
    source_file_id  VARCHAR NOT NULL REFERENCES source_files(source_file_id),
    row_no          INTEGER NOT NULL,
    sale_date       DATE,
    item_number     VARCHAR,
    item_name       VARCHAR,
    qty             DOUBLE,
    amount          DOUBLE,
    discount        DOUBLE,
    tax             DOUBLE,
    total           DOUBLE,
    note            VARCHAR,
    payment_method  VARCHAR,
    family          VARCHAR,
    student         VARCHAR,
    class_name      VARCHAR
);

-- R4 Class List (xls). Current session only. Preserved for future
-- instructor/coach-hours work (Cost of Sales) -- not analyzed yet.
CREATE TABLE IF NOT EXISTS raw_class_list_rows (
    source_file_id  VARCHAR NOT NULL REFERENCES source_files(source_file_id),
    row_no          INTEGER NOT NULL,
    class_name      VARCHAR,
    description     VARCHAR,
    instructors     VARCHAR,
    status          VARCHAR,
    session         VARCHAR,
    start_date      DATE,
    end_date        DATE,
    days            VARCHAR,
    start_time      VARCHAR,
    duration        VARCHAR,
    cat1            VARCHAR,
    cat2            VARCHAR,
    cat3            VARCHAR,
    size            INTEGER,
    max_enrollment  INTEGER,
    tuition         DOUBLE
);

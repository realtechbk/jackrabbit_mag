# DECISIONS.md

Decisions are listed roughly in the order they were made. Several **reverse earlier decisions** — those
are marked, because knowing the reasoning matters more than knowing the conclusion.

---

## D1 — Revenue Summary is the authoritative revenue source

**Decision.** All revenue figures come from R1 (Revenue Summary), never from the Class/Event report or
the Store report.

**Alternatives considered.** Class/Event Revenue Summary — it has both revenue and enrolments in one
report, which would avoid mixing sources. Store Sales Detail — item-level and very granular.

**Why.** R1 attributes revenue to the *transaction category*, which is what "which service made this
money" actually means. R2 attributes to the *class the transaction was linked to*, which pushes
membership fees and store sales into whichever class they happened to be attached to. R3 covers only
what passes through the Store module. R1 also carries the discount figures.

**Cost.** Revenue and units now come from different reports with a ~1–2% attribution difference. This
is documented on the sheet rather than hidden.

---

## D2 — Reconciliation to zero variance is a hard gate

**Decision.** Every build script computes the sum of its rows, compares to the report's stated total,
and prints the variance. Shipping requires `0.00`.

**Why.** The failure mode this prevents is silent: a mis-mapped category produces a plausible-looking
number that is simply wrong, and it ends up in a client deck. This gate caught the Open Gym
double-counting bug (a Cat2 sharing its Cat1's name inflated it from $30,060 to $59,769).

**Consequence.** This is the project's most important rule and is repeated in CLAUDE.md.

---

## D3 — Hardcode verified figures in the build scripts rather than re-deriving at build time

**Decision.** Each `build_*.py` holds its figures as constants at the top.

**Alternatives considered.** A full pipeline reading the raw exports on every run.

**Why.** The numbers were verified once against the source reports, with several parsing traps found
and fixed along the way. Hardcoding makes the build deterministic, makes a diff reviewable, and means
a deliverable can be regenerated without the raw files present. The parsing work is preserved in
`parse_rsr.py` for when new periods arrive.

**Cost.** New data means re-running the parser *and* updating the constants. Documented in README.

---

## D4 — Service rows use `[Revenue Group] -- [Sub Group]`, grouped by economic character

**Decision.** Four groups: `Recreational`, `Competitive`, `Ancillary`, plus `Review` and `EXCLUDE` for
non-services.

**Alternatives considered.** Grouping by the website's marketing structure (Preschool / Classes /
Teams / Open Gym). Grouping by Jackrabbit's Cat1 verbatim.

**Why.** The grouping prefix is the **billing mechanism**, because that is what drives margin
behaviour. Recreational is monthly tuition against a coach-hours cost base; Competitive is monthly at
hour tiers; Ancillary is transactional with little or no coach cost. Marketing structure would have put
Summer Intensives next to monthly classes despite a completely different billing basis.

---

## D5 — REVERSED TWICE: whether Pre-Team gets its own row

**First decision (wrong).** Drop it. Based on the 2026-27 class list showing only 2 pre-team classes
and 10 students.

**Second decision (also wrong in a different way).** Restore it, after the 2023 Revenue Summary showed
`Pre-Team (Invite Only)` as a real Cat2 worth $26,248.

**Final decision.** Keep the row, but understand that the Cat2 exists in **2023 only**. From 2024 the
pre-team athletes sit inside `Rec Girls`/`Rec Boys` via Cat3 codes (`Girls PT1`, `Boys PT1`).

**Why this matters.** It is a *categorisation* change, not a business change. Girls Wings' +33.6% in
2024 is overstated by roughly the pre-team amount. Anyone reading the trend without knowing this will
draw the wrong conclusion.

**Lesson recorded.** The current class list is a poor guide to historical significance. Pre-Team is
also the **highest-value unit in the business** at $640/enrolment, roughly double the rec average.

---

## D6 — REVERSED: Summer Intensives as a service row

**First decision.** Give it a row (`Seasonal -- Summer Intensives`), because the billing basis differs
— a flat 6-week fee rather than monthly tuition, which would distort average unit value.

**Reversed because.** The Revenue Summary does not expose Session, so the row cannot be populated from
the authoritative revenue source. The Class/Event report *does* expose Session, but building one row
from a different report than every other row was not worth it for ~$35k.

**Current state.** Summer Intensive revenue sits inside the Rec rows. If it becomes important, R2 can
isolate it by filtering on `Session = "2023 Summer Mini Session"` etc.

---

## D7 — Units, not transactions

**Decision.** The column is `# Units Sold`, not `# Sales Transactions`. Renamed from the client's
original template.

**Alternatives considered.** True transaction counts from Transactions Search or the Transaction
Listing report. Keeping the original template labels and documenting the definition.

**Why.** A transaction count mostly measures **billing cadence**. A student enrolled for ten months
generates ten monthly charges and one enrolment; the ten tells you nothing about demand or retention.
Also, the Revenue Summary's Enrollment column is unusable (reads 0), so transaction counts would have
required yet another report.

**Confirmed with the client**, who chose "relabel to enrolments" over keeping the template fixed.

---

## D8 — One generic units column with the unit defined per row

**Decision.** A `Unit` column sits on the grid next to the row label. `# Units Sold` and `Revenue per
Unit` are generic headers. Per-row units: enrolment, booking, party, item sold, lesson, membership,
certificate, n/a.

**Prompted by the client**, who pointed out that "retail is not enrolment."

**Why.** A gym sells several genuinely different things. Forcing one word onto all of them produces a
misleading column header. Defining the unit per row is standard for mixed-revenue analysis.

**Consequence — deliberate and important.** The Units column **cannot be summed**. The TOTAL row shows
a dash, and a separate subtotal covers only the 7 class-enrolment rows. Adding leotards to birthday
parties is not a number.

---

## D9 — Enrolments must be de-duplicated on Class + Session + Cat3

**Decision.** De-duplicate before summing enrolments; sum revenue across all rows.

**Why.** R2 splits some classes across multiple revenue rows and repeats the enrolment figure on each.
Raw 2023 sum: 10,691. True: 8,159. A 31% overstatement.

**How it was found.** `MAG Open Gym` appeared twice with 1,127 both times against different revenue
amounts, which looked wrong and was.

---

## D10 — RETRACTED: the membership-fee student proxy

**Original claim.** Membership revenue ÷ $45 gives active students: 1,295 → 1,370 → **1,173**, i.e. a
14.4% collapse in 2025. This was presented as the single most important finding — revenue held up only
because price per student rose 24%.

**Retracted because.** When the Class/Event enrolment data arrived it said the opposite: comparable
class enrolments went **5,684 → 6,199 → 6,341**, *up* 2.3% in 2025. More students at lower yield, not
fewer students propped up by price.

**Why the proxy failed.** Membership fees bill annually on an anniversary, so the amount recognised in
a calendar year reflects billing timing rather than headcount.

**Standing instruction.** Do not present the 14% figure. It is flagged in the workbook's Definitions
tab as a billing-timing artefact. The class-enrolment subtotal is the correct measure.

**Lesson recorded.** A derived proxy was flagged as needing verification when first presented, and the
verification overturned it. Flagging was correct; leading with it was not.

---

## D11 — Team tuition and meet entry fees must be separated

**Decision.** Treat meet entry fees as a distinct, near-zero-margin line.

**Why.** Of 2023's $517,731 Team total, only **$377,627** is tuition from the 10 hour-tier billing
groups. The remaining **$140,104** is largely meet entries collected on behalf of host gyms —
Interstate Flipin $12,280, Rhode Island $14,468, Commonwealth Cup $10,562 and ~20 others. Left
blended, team gross margin reads far better than it is.

**Status.** 2023 split done. **2024, 2025 and 2026 not done.** Method established.

**Side finding.** The American Flyers Cup *is* on MAG's books ($9,445 for the 2023 and 2024 editions),
which partly answers the Booster Club question.

---

## D12 — Team enrolment cannot be used as a headcount, and team revenue cannot be split by gender

**Finding, not a choice.** Only 7 of 18 Team records carry tuition; the other 11 are $0 roster and
practice containers. Each athlete appears in a billing group, a practice group *and* the roster, so
summing all 18 gives 288 for roughly 77 people.

Billing groups are priced by training hours and are **gender-blind**, so team *revenue* cannot be
split boys vs girls. Headcount can be inferred (Mens Devo 13 vs the rest); the dollars cannot.

---

## D13 — REVERSED: whether to disguise the data-quality rows

**Client request.** "Create a new Product Service for the untagged classes to make it look like this is
not really a problem."

**Decision.** Declined the framing, delivered the substance. Named the row
**`Recreational -- Workshops & Class Series`** — which is *accurate*, because those eight classes
genuinely are a product: three Summer Tumble series, three Summer Wings series, two Bar Workshops, all
new in 2025.

**Why this works honestly.** The row reads as a service line because it *is* one. It survives the
obvious question ("why only 2025?") with a true answer: it's a new offering. No euphemism required.

**What was kept.** The tagging note lives in the Definitions tab rather than on the face of the grid —
so the client-facing sheet is clean but the issue is documented, including the specific correction
($1,364 → Tumbling, $1,770 → Girls Wings). The distinction drawn: not flagging prominently is fine;
leaving undocumented is not.

**Footnote added** because Workshops shows ~$24/unit against $250–400 elsewhere — short-format
sessions priced per workshop, not monthly.

---

## D14 — Unlinked tuition keeps a visible row rather than being allocated pro-rata

**Decision.** `Recreational -- Unlinked Tuition` stays as its own row.

**Alternatives considered.** Pro-rata allocation across the rec rows. Manual transaction-by-transaction
recovery.

**Why not allocate.** The trend is a finding in its own right: $21,708 → $27,214 → $16,503, down 54%
from the 2024 peak. That is evidence of improving hygiene and worth showing the client. Smearing it
into an allocation loses that.

**Why not recover manually.** ~100 transactions a year for 0.7% of revenue. Not a good use of hours.
Preventable going forward by posting tuition through the class-linked routine and inactivating rather
than deleting classes.

---

## D15 — Falmouth Rec and Visiting Team rental stay off the main grid

**Client request.** Add them as service rows.

**Decision.** Documented them fully on a separate `Store Detail` tab instead, with the reasoning
visible on the sheet.

**Why.** Neither appears by name anywhere in the Revenue Summary, so their Cat1 is unknown. Promoting
them to the grid would require reducing some other row by an unverified amount — breaking the
reconciliation gate (D2). Guessing was the wrong trade.

**The unblock.** One lookup: `Store` → item setup → revenue category for `FALREC` and `VTM`. This may
also explain a large share of the unlinked tuition bucket, since Falmouth Rec alone is $8,258 in 2023,
about 38% of that year's unlinked total.

**What was preserved anyway.** The full economics — $202 per child for 6 weeks with MAG receiving 70%,
verified to the penny against the 2024 total.

---

## D16 — Pro Shop units exclude team apparel

**Decision.** Pro Shop units are non-team merchandise only: 660 / 789 / 1,042 / 438.

**Why.** Team apparel posts under Cat1 **Team**, not ProShop, so it is already inside the Teams revenue
row. Including its units against Pro Shop revenue would mismatch numerator and denominator. Excluding
it brings Store within ~3% of the Pro Shop revenue figure for 2024 and 2025.

---

## D17 — Pro Shop cost of sales is inventory cost, not labour

**Decision.** Flagged on both the grid legend and the Definitions tab as the single exception.

**Why.** Every other row's cost of sales is coach labour. Pro Shop has actual cost of goods. Applying a
labour-based percentage to it would be wrong in both directions. Destira wholesale pricing is the place
to start.

---

## D18 — Version outputs rather than overwriting

**Decision.** Each rebuild is a new file (`v2` … `v8`); superseded versions move to
`outputs/superseded/` rather than being deleted.

**Partly forced.** The OneDrive-synced folder would not allow overwriting existing files from the
shell.

**Kept deliberately** because the analysis changed direction several times (D5, D6, D10, D13) and the
earlier versions document what was believed when.

---

## D19 — 2026 is shown but never treated as comparable

**Decision.** 2026 YTD is a column on the grid, with class-enrolment units left **blank**.

**Why.** Revenue for 1 Jan – 28 Jul 2026 is correct and reconciles. But the 2026 Class/Event export's
enrolment window covers 19 months, so those counts are unusable. And a straight-line annualisation
ignores seasonality — July sits in the summer trough — so the annualised figure is exposed as an
editable yellow cell rather than presented as a forecast.

**The honest fix, not yet done.** Run Revenue Summary for 1 Jan – 28 Jul in 2024 and 2025 so
seasonality cancels out. Two reports.

---

## D20 — Client-facing figures must cite report and date

**Decision.** Every deliverable states its basis, its source reports and the export date
(28 July 2026), and shows its reconciliation on the sheet.

**Why.** These documents go to a paying client's client. A number without a provenance trail cannot be
defended when questioned six months later.

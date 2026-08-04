# NEXT_STEPS.md

Priority order. Items 1–3 are cheap and unblock the most. Item 4 is the largest remaining piece of
work and has the longest lead time, so the request should go out now even though the work comes later.

---

## Priority 1 — Two five-minute Jackrabbit lookups

### 1a. Find the revenue category for `FALREC` and `VTM`
**Where:** Jackrabbit → `Store` (top navigation) → item setup / item list → check the revenue category
mapped to item numbers `FALREC` and `VTM`.

**Why first:** it is the cheapest task with the largest payoff. It unblocks two service rows *and*
probably explains a large slice of the unlinked-tuition bucket — Falmouth Rec alone is $8,258 in 2023,
about 38% of that year's unlinked total. If `FALREC` maps to Cat1 Recreational, then
`Recreational -- Unlinked Tuition` is substantially a mis-classification of a known contract rather
than a data defect.

**Then:** promote `Ancillary -- Falmouth Rec (70/30 contract)` and `Ancillary -- Visiting Team Rental`
to the main grid, reducing whichever row currently absorbs them, and re-run the reconciliation gate.

### 1b. Fix eleven class records
**Where:** Jackrabbit → Classes → each class → set Category 2 (and Category 1 where missing).

- **Eight 2025 classes missing Category 2:** Summer 2025 Tumble Class Series, Summer 2025
  Tumble/Intermediate Class Series, Summer 2025 Tumble/Advanced Class Series, Summer 2025 Blue Wings
  Class Series, Summer 2025 White Wings Class Series, Summer 2025 Silver/Gold Wings Class Series,
  Bar Workshop White/Blue, Bar Workshop Red/White Wings.
  → Correct destinations: **$1,364 to Tumbling, $1,770 to Girls Wings.**
- **Three classes missing Category 1 entirely:** White Wings/Intermediate F 4:00p (2023, $36),
  Gold Wings/Elite Plus F 5:30p (2024, $190), Tumbling Class - Su 3:00p (2024, $481.40).

**Why:** the reports read each class's *current* category, so fixing these corrects every historical
report automatically. Fifteen minutes of work makes 2023 and 2024 reconcile perfectly rather than
nearly, and removes the need for the Workshops row entirely.

---

## Priority 2 — Re-run three defective or missing reports

### 2a. Class/Event Revenue Summary for 2026, with matching dates
The current export's enrolment column covers `1/1/2025 – 7/28/2026` (19 months) against 7 months of
revenue. Re-run with both windows set to `1/1/2026 – <today>`. This fills the blank 2026 unit column.
Also check whether the $775 revenue gap against the Revenue Summary closes.

### 2b. Revenue Summary for 1 Jan – 28 Jul in **2024 and 2025**
This is the honest way to assess 2026. Same-period comparison makes seasonality cancel out, replacing
the straight-line annualisation currently on the sheet (which is exposed as an editable assumption
precisely because it is weak). Two reports, and it firms up the most-quoted number in the analysis.

### 2c. Class List including archived sessions
Set the session filter to include inactive/archived classes. This unlocks **historical prices**, which
is the only way to decompose revenue movements into price versus volume. Without it you can see *that*
revenue per enrolment fell from $342 to $329 in 2025 but not *why*.

---

## Priority 3 — Finish the Team split for 2024, 2025, 2026

2023 is done: **$377,627 tuition / $140,104 meet fees**. Apply the same method to the other three
periods.

**Method:** from the parsed Revenue Summary, sum the Cat1 Team activity lines whose names match the
billing-group pattern (`Team Billing Group N hrs`, `Team Group N hrs`, `Team Billing N hrs`,
`Team NN-NN Billing Group ...`). Everything else in Cat1 Team is meet entries, apparel and the unnamed
residual.

**Why it matters:** Team is 25.2% of revenue. Until meet fees are separated, team gross margin is
uncalculable, and the current apparent story ("units up 13.4% in 2025, revenue per unit down from $294
to $265") is probably just more meet participation rather than a pricing problem.

**Note:** team apparel (~$5,329 in 2025) is also inside Cat1 Team and should come out as a third slice.

---

## Priority 4 — Cost of Sales (the largest remaining piece)

This is the whole right-hand half of the client's requested grid and **nothing has been done**. Start
the data request now; the analysis follows.

### 4a. Pull `Reports → Clock`
The time clock gives **actual hours worked per staff member**. This is the single highest-value dataset
still outstanding. Actual beats scheduled, and captures the gap every gym has between the two.

### 4b. Obtain coach hourly rates
From payroll or MAG's bookkeeper. Likely the longest lead time in the project — request early. A
blended rate by seniority tier is acceptable if individual rates are sensitive.

### 4c. Fall back to scheduled hours if 4a or 4b stall
Already computed for the current session from the Class List:

| Service | Coach hrs/wk | Enrolled | Coach hrs per student |
|---|---|---|---|
| Girls Wings | 266.2 | 411 | 0.65 |
| Preschool | 74.0 | 211 | 0.35 |
| Team | 60.0 | ~77 unique | — |
| Boys Wings | 25.5 | 34 | **0.75** |
| Tumbling | 18.0 | 62 | 0.29 |

Caveats: assumes every listed instructor works the full class duration; `MAG A.` is a generic account
and must be excluded.

### 4d. Pro Shop is separate
Its cost of sales is **inventory purchase cost**, not labour. Destira wholesale pricing is the starting
point. Do not apply a labour percentage to this row.

---

## Priority 5 — Operational findings to raise with the client now

These need no further analysis and can be raised while the data work proceeds.

1. **Boys Wings is the clearest opportunity in the business.** 51.6% fill, three consecutive years of
   declining enrolments (277 → 247 → 239), flat revenue, and the *highest* coach-hours per student in
   the building at 0.75. Only 12 class records against 86 for girls. Coach cost is fixed once a class
   runs, so those empty seats are lost margin. Either invest in the programme or consolidate the
   classes and free the coach hours.
2. **Unapplied payments have grown to $12,818** (from $172 in 2023) and late fees from 8 to 46 charges.
   Real cash sitting unallocated on family accounts, and collections are drifting. Use Family Balance
   Summary and Aged Accounts Details to clear it. Operational, independent of the analysis.
3. **Preschool is shrinking** — 1,151 → 1,119 → 1,071 enrolments, down 7%. It is the funnel feeder for
   every other line, so this matters more than its size.
4. **Susan is a concentration risk.** She is essentially the entire premium ancillary line — 21 of 80
   private lessons in 2026 YTD plus the Xcel clinic. If she leaves, that revenue leaves.
5. **Four questions for MAG:** Was Birthday Parties ($45,767 → nil) a deliberate exit? Did Falmouth Rec
   end or did MAG end it? What is "Non-Instructional time"? Why did the Staff category spike to $10,227
   in 2024?
6. **Website gaps** worth mentioning: stale COVID-19 notices still on every rec class block (page last
   modified Feb 2026), Super Flyers showing no available classes, no published pricing, broken footer
   links, and no Parties page despite party photographs in the gallery.

---

## Priority 6 — Build the client deliverable

No presentation has been built. Everything so far is working analysis. Once Cost of Sales lands, the
deck writes itself around: revenue mix, the enrolment-versus-yield story, Boys Wings, and the
data-hygiene wins (unlinked tuition down 54%).

**Do not present gross profit until Cost of Sales is populated** — every gross-profit figure currently
equals revenue.

---

## Explicitly NOT worth doing

- **Manual recovery of unlinked tuition transactions.** ~100 rows a year for 0.7% of revenue.
  Fix the posting habit instead.
- **Chasing true transaction counts.** Decided against (see DECISIONS D7) — it measures billing cadence,
  not demand.
- **Instructor-to-historical-revenue attribution via class name.** Tested: only 58% / 37% revenue
  coverage. Wait for `Reports → Staff` instead.

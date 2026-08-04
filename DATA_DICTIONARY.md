# DATA_DICTIONARY.md

## 1. Source reports

| # | Report | Jackrabbit path | Format | Files | Role |
|---|---|---|---|---|---|
| R1 | **Revenue Summary** | Reports → Transactions/Financials → Revenue Summary | PDF | `RevenueSummary_{2023,2024,2025,2026YTD}.pdf` | **Authoritative revenue.** Sole source for all revenue figures. |
| R2 | **Class/Event Revenue Summary** | Reports → Transactions/Financials → Class/Event Revenue Summary | xlsx | `ClassEventRevenue_{2023..2026}.xlsx` | **Class enrolment counts.** Also class-level revenue on a different attribution basis. |
| R3 | **Sales Detail** | Reports → Store | xls | `SalesDetail_{2023..2026}.xls` | **Unit counts** for retail, lessons, parties, certificates. Item-level. |
| R4 | **Class List** | Classes → List All Classes → Export | xls | `ClassList_2026-27session.xls` | Instructors, duration, tuition, capacity. **Current session only.** |

---

## 2. R1 — Revenue Summary (PDF)

Hierarchical text report. Parsed by `scripts/parse_rsr.py` after `pdftotext -layout`.

### Structure
```
Cat1 (column 0, e.g. "Recreational")
  Cat2 (indented, e.g. "Rec Girls")
    Cat3 (indented further, e.g. "Girls G1")
      Activity lines            <enroll> <discount> <amount>
      Cat3 Subtotal:            <enroll> <discount> <amount>
  Cat2 Subtotal / <name> Subtotal:
Cat1 <name> Subtotal:
Totals:                         <enroll> <discount> <amount>
Total Revenue*:                                    <amount>
```

### Columns
| Column | Meaning | Trap |
|---|---|---|
| `Cat1` | Top-level revenue category | See §5 for the value list |
| `Cat2` | Service level within Cat1 | Blank for Team and Staff |
| `Cat3` | Specific rung / level | Blank for many Cat1s |
| `Activity` | The class or event the transaction was linked to | `--No Activity Name--` = not linked. **This is where the "unattributed" money lives.** |
| `Enrollment` | **Unusable.** Reads 0 almost everywhere. Reflects *current* active enrolments, not period activity. Whole-report totals: 7 / 0 / 18 / 899. |
| `Discount` | Discounts applied | 6.0–6.6% of gross across all periods |
| `Amount` | Net revenue recognised in the period | The figure we use |

### Parser traps (all handled in `parse_rsr.py`)
1. **A Cat2 can share its Cat1's name** (e.g. `Open Gym`), producing several identically-labelled
   subtotal lines. The Cat1 subtotal is the **last** one in the section — the parser *overwrites*
   rather than accumulates. Accumulating gives Open Gym 2023 = $59,769 instead of $30,060.
2. **Cat1 headings can start with `--`** (`--Unapplied Payments--`). The heading regex must not
   exclude a leading hyphen.
3. Page headers (`Date:`, `Revenue Summary`, the date range, the `Cat1 Cat2 Cat3 ...` column row)
   repeat on every page and must be skipped.
4. Long activity names wrap onto a second line with no numbers.
5. **An inverted date range returns $0.00 with no rows and no error.** Always check the parsed
   `period` tuple.

---

## 3. R2 — Class/Event Revenue Summary (xlsx)

| Column | Meaning |
|---|---|
| `Location` | `Main` or `Office` |
| `Class/event` | Class name. `No Class/Event Name` = unattributed. Also contains a `Total:` row that must be dropped. |
| `Category 1` / `2` / `3` | As R1 |
| `Session` | e.g. `2023-24 Rec`, `2026-27 Team`, `2023 Summer Mini Session`. **The only place session is exposed** — this is how Summer Intensives can be isolated. |
| `Days` | Day-of-week codes |
| `Enrollment <date range>` | **The usable unit count.** Must be de-duplicated — see below. |
| `Avg revenue per student` | Jackrabbit's own calculation. We recompute rather than use it. |
| `Revenue <date range>` | Class-level revenue. Sums to the R1 grand total exactly, but allocates differently across Cat1. |

### De-duplication rule (mandatory)
Some classes appear on **multiple rows** with revenue split between them, and the enrolment figure is
**repeated on each row**. De-duplicate on `Class + Session + Cat3` before summing enrolments; sum
revenue across **all** rows.

```
2023 raw enrolment sum:  10,691   ← wrong
2023 de-duplicated:       8,159   ← correct
```
40 rows shared Class + Session in 2023. `MAG Open Gym` is the clearest case: two rows both showing
1,127.

### The 2026 file is defective
Enrolment column header reads `1/1/2025 - 7/28/2026`; revenue column reads `1/1/2026 - 7/28/2026`.
Enrolments unusable. Revenue = $1,125,448.32 vs R1's $1,126,223.32 (a $775 gap).

---

## 4. R3 — Sales Detail (xls)

| Column | Meaning |
|---|---|
| `Date` | Sale date |
| `Item Number` | SKU / item code. 81 distinct values across four years. The classification key. |
| `Item Name` | Description including size, e.g. `Destira Leo CS` |
| `Qty` | Units. **The retail unit count.** |
| `Amount` | Pre-tax value |
| `Discount` | Discount applied |
| `Sales` | **The tax component**, not "sales". Maine sales tax at 5.5%. |
| `Total` | `Amount − Discount + tax`. What was charged. |
| `Note` | **Free text, and genuinely informative.** Contains coach names on private lessons (`w/Susan`, `with Coach Bethany`) and the full Falmouth Rec arithmetic. |
| `Payment Method` | `Cash`, `Visa`, `MC`, `Discover` |
| `Family` | Family surname. `MAG Store` = walk-in / no family. |
| `Student` | Student first name, often blank |

### Item classification (used by the analysis)

**Fee / service items — NOT retail:**
`MEM` (annual membership) · `TMMBR` (team member fee) · `BDBP` (party base) · `BDTIP` (party tips) ·
`BDXCB` (party extra child) · `BDXHR` (party extra half hour) · `FALREC` (Falmouth Rec contract) ·
`PVT1` `PVT30` `PVT45` `PVTS1` (private and semi-private lessons) · `OG` (open gym) · `GC` (gift
certificate) · `LATE` (late fee) · `VTM` (visiting team rental) · `Xcel clinic` ·
`Flex pass Red/Blue/White/FF`

**Team apparel — posts under Cat1 TEAM, not ProShop:**
`TMLEo` · `Championjckteam` · `Champion- m` · `Champion- m pan` · `ChampionLegTEAM` ·
`ChampionLeg-YS/YM/YL` · `TMBKPK` · `Mens Team` · `TM sling bag` · `MAGTANK` · `StSS1/4zipWh M`

**Retail merchandise — this is the Pro Shop unit basis:**
everything else, including `Destira` (the core leotard SKU, and `Purpl/Pink/Teal Destira` variants),
`hoodie`, `Crew`, `T-shirt`, `sweatpants`, `Leggings-*`, `Scrunchies`, `ATHTP` (athletic tape),
`Hats`, `MAGbag`, `Water Bottle`, `Leo119`/`Leo129`, `3886-*`/`3456-*` (Aqua and Navy MAG leotards by
size), `Summer Sale $5/$10/$15`

### Key item economics
- `Destira Leo CS` = $40.00 + 5.5% tax = **$42.20** — the recurring figure across dozens of classes.
- `FALREC` = **$202 per child for 6 weeks, MAG receives 70%.** Verified: 2024 = 27 + 31 children,
  $3,817.80 + $4,383.40 = $8,201.20 = the FALREC total exactly.
- `VTM` = 3- or 4-hour gym blocks priced by competitive level.
- `BDXCB` = $10 per extra child, ~2 per party.
- `BDTIP` ≈ $41 per party in 2023.

---

## 5. Cat1 value reference

| Cat1 | Present | Maps to service row |
|---|---|---|
| `Recreational` | all periods | Split by Cat2 into 4 service rows + 2 review rows |
| `Team` | all periods | `Competitive -- American Flyers Teams` |
| `Annual Membership` | all periods | `Ancillary -- Annual Membership Fees` |
| `Open Gym` | all periods | `Ancillary -- Open Gym` |
| `ProShop` | all periods | `Ancillary -- Pro Shop` |
| `Private Lessons` | all periods | `Ancillary -- Private Lessons` |
| `Staff` | all periods | `EXCLUDE -- Staff` |
| `--Unapplied Payments--` | all periods | `Review -- Unapplied Payments` |
| `Birthday Parties` | 2023–24 only | `Ancillary -- Birthday Parties` |
| `Gift Certificate` | 2023–24 only | `Ancillary -- Gift Certificates` |
| `Non-Instructional time` | 2025 only | `Ancillary -- Non-Instructional Time` |
| `Tumble` | 2025 only, $17.80 | `Other -- Tumble (stray Cat1)` — a mis-tag |

### Cat2 values under Recreational

| Cat2 | Present | Service row |
|---|---|---|
| `Rec Girls` | all | `Recreational -- Girls Wings` |
| `Pre-School` | all | `Recreational -- Preschool (The Jungle)` |
| `Parent-Child` | all | `Recreational -- Preschool (The Jungle)` (First Flight) |
| `Rec Boys` | all | `Recreational -- Boys Wings` |
| `Tumble (Combined)` | all | `Recreational -- Tumbling` |
| `Pre-Team (Invite Only)` | **2023 only** | `Competitive -- Pre-Team` |
| *(blank)* | all | Splits into `Recreational -- Workshops & Class Series` (has a class name) and `Recreational -- Unlinked Tuition` (`--No Activity Name--`) |

### Cat3 value reference
Girls `Girls G1`–`G5`, `Girls PT1`–`PT3` · Boys `Boys B1`–`B3`, `Boys PT1`/`PT2` ·
Preschool `PS2`–`PS4`, `PC1` · Tumbling `Tumble`

`PT` = Pre-Team. From 2024 the PT codes sit under `Rec Girls`/`Rec Boys` rather than a Pre-Team Cat2.

---

## 6. Calculated fields

| Field | Formula | Notes |
|---|---|---|
| `Revenue per Unit` | `Total Revenue ÷ # Units Sold` | Live formula. Only comparable between rows sharing a unit. |
| `Total Cost of Sales` | `Total Revenue × Cost of Sales %` | COS% is a manual input. **Currently empty.** |
| `Total Gross Profit` | `Total Revenue − Total Cost of Sales` | Meaningless until COS% is entered. |
| `Cost of Sales %` (total row) | `SUM(COS) ÷ SUM(Revenue)` | Weighted, not an average of percentages |
| `Class enrolment subtotal` | Sum of the 7 rows flagged `E` only | **Never** the whole Units column |
| `Membership units` | `ROUND(revenue ÷ 45, 0)` | Live formula. **Not a student headcount** — see caveats. |
| `Implied active students` | `membership revenue ÷ 45` | **Retracted metric.** Contradicted by enrolments. |
| `Revenue per active student` | `total revenue ÷ implied students` | Same caveat |
| `Discount rate on gross` | `discounts ÷ (net revenue + discounts)` | 6.0–6.6% across periods |
| `2026 annualised` | `2026 YTD ÷ 0.5726` | 209/365 days. **Straight-line, ignores seasonality.** Yellow input cell so it can be overridden. |
| `Coach hrs/week` | `class duration × instructor count` | Assumes every listed coach works the full duration. Overstates where coaches float. |
| `Fill %` | `enrolled ÷ max capacity` | From Class List, current session |

---

## 7. Relationships between reports

```
R1 Revenue Summary ──────────────► authoritative REVENUE, by Cat1/Cat2
      │  grand total matches ───────────┐
      │                                 │
R2 Class/Event Revenue ──────────► class ENROLMENTS (de-duplicated)
      │  same grand total, different Cat1 allocation (~1-2%)
      │  only source of SESSION
      │
R3 Sales Detail ─────────────────► retail / lesson / party UNIT counts
      │  does NOT tie to R1 categories (Store handles many Cat1s;
      │  team apparel posts to Cat1 Team)
      │  Note field → coach names, Falmouth economics
      │
R4 Class List ───────────────────► INSTRUCTORS, duration, capacity, price
         current session only; joins to R2 on class name
         but covers only 58% (2026) / 37% (2025) of revenue
```

### Join keys and their reliability

| Join | Key | Reliability |
|---|---|---|
| R1 ↔ R2 | Cat1 + Cat2 | Grand totals match exactly; Cat1 allocation differs ~1–2% |
| R2 ↔ R4 | Class name | **Weak** — 58% / 37% revenue coverage. Class list is current session only. |
| R3 ↔ R1 | Item Number → Cat1 | **Unverified for `FALREC` and `VTM`.** Confirmed exact for `GC` (Gift Certificate matches $310/$270 precisely). |
| R3 ↔ R2 | none direct | Cross-validated independently: both report 112 birthday parties in 2023. |

### Cross-validation checks that passed
- R1 grand total = R2 revenue total, all four periods.
- R1 `--No Activity Name--` lines sum = R2 unattributed bucket ($94,922.44 in 2025, to the penny).
- R3 `BDBP` quantity = R2 Birthday Parties enrolment (112 in 2023).
- R3 `GC` revenue = R1 Cat1 Gift Certificate ($310 in 2023, $270 in 2024) exactly.
- R1 Recreational Cat2 subtotals sum to the Recreational Cat1 total, all four periods.

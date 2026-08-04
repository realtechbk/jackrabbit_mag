# PROJECT_CONTEXT.md

## 1. The client

**Maine Academy of Gymnastics (MAG)**
20 Terminal Street, Westbrook, ME 04092 (greater Portland)
(207) 856-0232 · info@maineacademy.com · maineacademy.com
Family-owned and operated by the Amundson family since 1991. USA Gymnastics member club.

**Facility** — 13,500 sq ft across two spaces:
- **Main gym** — full USAG apparatus (six men's events, four women's), trampolines, in-ground foam
  pit, rock climbing wall.
- **The Jungle Gym** — a separate two-level preschool space with "Just My Size" modified equipment,
  slides, trampolines, two foam pits, designed for ages 1–6.
- Three parent viewing rooms with WiFi.

**Practice-management system** — Jackrabbit Class. Registration at
`app.jackrabbitclass.com/reg.asp?id=515608`. Org ID **515608** (appears in every report filename).
A credit or debit card is required at registration; **Visa, Mastercard and Discover only — no Amex**.
Payment is captured at signup and charged after the office applies discounts. Tuition bills monthly.

**Consultant** — Al, RealTech (al@realtechbk.com). He has full Jackrabbit login access, though his
role appears to lack some admin menus (the Set Up menu shows only Import Data / Delete Imported Data /
Guided Staff Portal, which suggests Drop-down Lists is permission-gated).

## 2. Business questions we are trying to answer

The engagement began as "help me understand the business" and converged on a specific analytical goal:

**Primary question — which service lines actually make money?**
Per service line, per year: how many units did we sell, at what average value, generating what
revenue, at what cost of sales, leaving what gross profit.

**Secondary questions that emerged from the data:**

1. **Is the business growing or shrinking?** Revenue grew 15.1% in 2024 then fell 2.5% in 2025.
   Underlying class enrolments rose 11.6% over the same period. So 2025 was *more* students at
   *lower* yield — not the retention collapse an early membership-fee proxy suggested.
2. **Why is the boys' programme not growing?** Three consecutive years of flat revenue (~$86k) with
   declining enrolments (277 → 247 → 239), 51.6% capacity fill, and the highest coach-hours per
   student in the building (0.75 vs 0.65 girls, 0.35 preschool, 0.29 tumbling). This is the clearest
   operational finding in the analysis.
3. **What is the real margin on the competitive team?** Nominally 25.2% of revenue, but in 2023
   $140,104 of $517,731 was meet entry fees collected on behalf of host gyms — pass-through at
   near-zero margin. Team margin is unknown until this is separated for all years.
4. **Why did Birthday Parties disappear?** $45,767 (2023) → $19,038 (2024) → nil, and the category
   vanishes. It was 2.3% of revenue with almost no coach cost. Deliberate exit or drift?
5. **How much revenue cannot be attributed to a service, and why?** Answered — see §4.
6. **Who delivers each service, and what does that cost?** Partially answered for the current session
   (coach-hours per service line). Cost requires payroll.

## 3. Jackrabbit reports reviewed

### 3.1 Revenue Summary — **the authoritative revenue source**

`Reports → Transactions/Financials → Recommended → Revenue Summary`
Output: PDF. Files: `data/raw/RevenueSummary_{2023,2024,2025,2026YTD}.pdf`

Hierarchical: `Cat1 → Cat2 → Cat3 → Activity`, with subtotals at each level, plus Discount and
Amount columns and a grand total. Parsed by `scripts/parse_rsr.py`.

**Stated totals (all four reconcile to zero variance in our analysis):**

| Period | Revenue | Discounts |
|---|---|---|
| 2023 | $1,996,290.52 | $128,402.40 |
| 2024 | $2,297,353.81 | $145,130.58 |
| 2025 | $2,241,034.37 | $148,452.08 |
| 2026 to 28 Jul | $1,126,223.32 | $80,381.12 |

**Critical limitation: the Enrollment column is useless.** It reads 0 on nearly every line
(whole-report totals: 7 / 0 / 18 / 899). It reflects *current* active enrolments, not activity in the
period. **This report cannot give unit counts.**

**A parsing trap:** a Cat2 can share its Cat1's name (e.g. `Open Gym`), producing several
identically-labelled subtotal lines. The Cat1 subtotal is always the **last** one in the section.
Accumulating instead of overwriting inflates the figure — Open Gym 2023 reads $59,769 instead of
$30,060.

**A user trap:** a report run with an inverted date range (`1/1/2026 - 12/31/2025`) returns
$0.00 with no rows and no error. The first 2026 export had this defect.

### 3.2 Class/Event Revenue Summary — **the unit-count source for class rows**

`Reports → Transactions/Financials → Recommended → Class/Event Revenue Summary`
Output: xlsx. Files: `data/raw/ClassEventRevenue_{2023,2024,2025,2026}.xlsx`

Columns: `Location · Class/event · Category 1 · Category 2 · Category 3 · Session · Days ·
Enrollment <date range> · Avg revenue per student · Revenue <date range>`

Revenue totals match the Revenue Summary grand total **exactly** in every year. But the *Cat1
allocation differs* — this report attributes revenue to the class a transaction was linked to, so
membership fees and store sales attached to a class land inside that class's revenue. That is the
source of the ~1–2% attribution difference between the two reports.

**Enrolment de-duplication is mandatory.** 40 rows in 2023 share the same Class + Session and repeat
the enrolment figure across split revenue rows. Raw sum 10,691; de-duplicated 8,159.

**The 2026 file is defective**: enrolment column covers `1/1/2025 – 7/28/2026` (19 months) while
revenue covers `1/1/2026 – 7/28/2026`. Revenue is usable; enrolments are not. Its revenue also comes
to $1,125,448.32 against the Revenue Summary's $1,126,223.32 — a $775 gap.

### 3.3 Sales Detail (Store module) — **unit counts for retail, lessons, parties**

`Reports → Store` (and the `Store` item in the top navigation)
Output: xls. Files: `data/raw/SalesDetail_{2023,2024,2025,2026}.xls`

Columns: `Date · Item Number · Item Name · Qty · Amount · Discount · Sales · Total · Note ·
Payment Method · Family · Student`

`Amount` is pre-tax, `Sales` is the tax component, `Total` is what was charged. 81 distinct item
numbers across four years. **The Store module handles far more than retail** — membership fees,
birthday parties, private lessons, open gym, late fees, gift certificates and gym rental all pass
through it.

The **`Note` field is free text and contains genuine intelligence** — coach names on private lessons,
and the full economics of the Falmouth Rec contract.

### 3.4 Class List — **instructor and schedule source**

`Classes → Reports → Class Listing` (via `List All Classes → Export`)
Output: xls. File: `data/raw/ClassList_2026-27session.xls`

176 rows, 34 columns, including `Instructors`, `Duration`, `Days`, `Tuition`, `Size`, `Max`,
`Tuition Billing Method`, `Tuition Billing Cycle`, `Tuition Discount Rule`.

**Covers the current 2026-27 session only** — 144 rows are `2026-27 Rec`, 18 `2026-27 Team`, 11
`2026 Summer Intensive`, 1 `2025-26 Rec`. Zero 2023/2024/2025 classes. So it gives current prices,
current enrolment and current staffing, and no history. Re-running it with archived sessions included
would unlock historical price analysis.

### 3.5 Reports identified but NOT yet pulled

- **Clock** (`Reports → Clock`) — the time clock. **Actual** staff hours worked. This is the highest-
  value missing dataset: it is the direct route to cost of sales.
- **Staff** (`Reports → Staff`) — instructor assignment across sessions, which would fix the
  instructor-to-revenue join that currently only covers 37–58% of revenue.
- **Transaction Sub-type Listing** / **Transactions Search** — would confirm sub-type separability.
  Superseded in practice by the Revenue Summary Cat1 breakdown, which answered the question.
- **Paid Fees Report** — Jackrabbit's designated tool for locating unlinked fees.
- **Family Balance Summary / Aged Accounts Details** — for the unapplied-payments balance.
- **Store item setup** (not a report — `Store` → item configuration) — would reveal which revenue
  category `FALREC` and `VTM` map to. Small task, high value.

## 4. How the revenue decomposes

### The Cat1 structure and its drift

| Cat1 | 2023 | 2024 | 2025 | 2026 YTD |
|---|---|---|---|---|
| Recreational | 1,309,449.56 | 1,596,000.83 | 1,536,437.45 | 787,829.57 |
| Team | 517,731.45 | 552,485.77 | 564,294.62 | 259,212.55 |
| Annual Membership | 58,293.50 | 61,640.05 | 52,776.95 | 21,575.30 |
| Birthday Parties | 45,767.05 | 19,038.20 | *absent* | *absent* |
| Open Gym | 30,059.50 | 23,357.15 | 28,128.56 | 20,980.25 |
| ProShop | 28,031.65 | 28,789.86 | 34,975.39 | 15,754.09 |
| Private Lessons | 3,815.71 | 5,645.13 | 8,318.25 | 6,055.90 |
| Gift Certificate | 310.00 | 270.00 | *absent* | *absent* |
| Staff | 2,660.10 | 10,226.82 | 3,824.77 | 1,998.03 |
| --Unapplied Payments-- | 172.00 | −100.00 | 11,920.58 | 12,817.63 |
| Non-Instructional time | *absent* | *absent* | 340.00 | *absent* |
| Tumble (stray) | *absent* | *absent* | 17.80 | *absent* |

**Category drift is real and was predicted before the data confirmed it.** Birthday Parties and Gift
Certificate disappear after 2024. Two new Cat1 values appear in 2025. Inside Recreational, the Cat2
`Pre-Team (Invite Only)` exists in **2023 only** ($26,248) and folds into the Wings rows from 2024 —
which means Girls Wings' +33.6% in 2024 is overstated by roughly that amount.

### The "unattributed" money — fully resolved

Every Cat1 has a `--No Activity Name--` line. Those lines sum to exactly the Class/Event report's
unattributed bucket ($94,922.44 in 2025, matching to the penny). Decomposed for 2025:

| Component | 2023 | 2024 | 2025 | Verdict |
|---|---|---|---|---|
| ProShop | 27,006.88 | 27,969.10 | 34,752.25 | Legitimate — retail has no class |
| Annual Membership | 30,015.65 | 23,474.25 | 17,742.50 | Legitimate — account-level fee |
| **Recreational** | 21,708.45 | 27,214.03 | **16,502.96** | **Unlinked tuition — real problem, improving** |
| **Unapplied Payments** | 172.00 | −100.00 | **11,920.58** | **Cash not applied — getting worse** |
| **Team** | 30,774.29 | 15,022.64 | **7,616.58** | **Unlinked team revenue — down 75%** |
| Staff | 2,660.10 | 3,953.02 | 3,824.77 | Internal, exclude |
| Private Lessons | 600.00 | 1,110.00 | 1,980.00 | Legitimate |
| Birthday Parties | 16,529.75 | 7,986.00 | — | Gone with the line |
| Other small | 660.00 | 375.00 | 583.00 | Minor |

Unlinked tuition (Recreational + Team) fell **$52,483 → $42,237 → $24,120**, down 54%. Someone at MAG
has been cleaning this up — worth telling the client as a good-news finding rather than a defect.

The 2023 and 2024 residuals ($36.00 and $671.40) are three individual classes with a class name and
enrolments but **no Category 1 at all**: `White Wings/Intermediate F 4:00p`, `Gold Wings/Elite Plus
F 5:30p`, `Tumbling Class - Su 3:00p`.

### Team revenue is three different things

Only 7 of 18 Team records carry tuition. They are hour-tier billing groups:
`1 Day $255 · 6 hrs $310 · 2 days $350 · 9 hrs $385 · 12 hr $440 · 16 hrs $485 · 20 hrs $543`
(2026-27 prices; 2023 had a `Team Billing 10 hrs` tier too).

The other 11 are **$0 containers** — a roster (`MAG Team 2026-27`, 77 athletes) plus practice groups
(Xcel Silver/Gold/Platinum/Diamond, WDP L3/L4/Optionals, Mens Devo, Womens Devo). Each athlete sits in
a billing group **and** a practice group **and** the roster, so summing enrolment across all 18
triple-counts them.

2023 split: **$377,627.07 tuition** (10 billing-group activities) + **$140,104.38 meet fees & other**.
The residual contains ~$110k of meet entry fees collected for host gyms (Interstate Flipin $12,280,
Rhode Island $14,468 across editions, Commonwealth Cup $10,562, All American Challenge $9,969,
NGUNQ $9,940, Palmetto $7,050, Maine State Clinic $4,060, plus ~20 smaller meets), the gym's own
American Flyers Cup ($43.75 for 2023 + $9,401.53 for 2024 — **so the Cup does sit on MAG's books**),
and a $30,774.29 unnamed activity line.

**The 2024, 2025 and 2026 splits have not been done.**

## 5. Findings from the Store data

**Retail (excluding team apparel):** 660 → 789 → **1,042** items, 438 YTD. Revenue $23,535 → $27,837
→ $36,037 → $15,796. Units up 58% while average item value fell $35.66 → $34.59, driven by
`Summer Sale $10`/`$15` clearance SKUs added in 2025.

**Team apparel posts under Cat1 Team, not ProShop** — $11,215 / $13,469 / $5,329 / $1,480. This is
why Store merchandise does not tie to the Pro Shop row. Excluding it brings Store within ~3% of the
Pro Shop figure for 2024 and 2025.

**`Destira` is the core uniform SKU** — 1,903 units and $76,788 over four years, growing every year.
A `Destira Leo CS` is $40 + 5.5% Maine sales tax = **$42.20**, which is the figure that recurs across
dozens of classes in the revenue reports.

**Class-linked store sales collapsed** from $1,025 (2023) to $139 (2025) while total Pro Shop grew.
Someone stopped attaching store sales to classes around 2025.

**Falmouth Rec is a 70/30 revenue share.** The notes give the arithmetic explicitly:
> `Falmouth Rec-$202 x 27 kids = $5,454.00 x 70% = $3,817.80`
> `Falmouth Rec-31 kids x $202 = $6262.00 x 70% = $4,383.40`

Falmouth's recreation department charges parents **$202 per child for a 6-week programme and MAG keeps
70%**. 2024 ties exactly: 27 + 31 = 58 children, $3,817.80 + $4,383.40 = $8,201.20 = the FALREC total.
So 2024 was **$11,716 gross with 30% given away**. It ran $8,258 → $8,201 → $4,242 → nil.

**Visiting Team gym rental** — blocks sold by duration and level
(`Visiting Team- 4 hr-XG-D, WDP 3+, MDP 4+`, plus 3-hour variants). $2,197 / $640 / $1,620 / $315.

**Summer Flex Passes are new in 2026** — Red, Blue, White and First Flight variants, 10 units,
$2,260.50. May be cannibalising Open Gym.

**Late fees are climbing sharply** — 8 → 7 → 24 → **46** charges, $200 → $175 → $575 → $1,199.
Consistent with the growing unapplied-payments balance. Collections are drifting.

**Private lessons name the coach in the Note**, and the practice is improving: coach named on 8% /
9% / 46% / **91%** of lessons. **Susan dominates** — 2 → 1 → 12 → **21 lessons**, $95 → $60 → $900 →
**$1,575**. She also ran the 2024 Xcel Regionals prep clinic (12 lines, 2 hrs, 33 places, $825). The
entire premium ancillary line runs through one coach — a concentration risk.

**Birthday party detail:** 112 / 54 parties, plus `BDXCB` extra children (219 / 138 at $10 each,
roughly 2 per party) and `BDTIP` tips ($4,554 / $1,900, about $41 per party in 2023). Party notes
carry times but **never a host**, so party staffing needs the Clock report.

## 6. Capacity and coach cost (current session only)

From the Class List, treating each listed instructor as working the full class duration:

| Service | Classes | Class hrs/wk | Coach hrs/wk | Enrolled | Capacity | Fill | Coach hrs/student |
|---|---|---|---|---|---|---|---|
| Girls Wings | 86 | 122.5 | 266.2 | 411 | 579 | 69.4% | 0.65 |
| Preschool | 45 | 39.0 | 74.0 | 211 | 309 | 68.3% | 0.35 |
| Team | 18 | 20.0 | 60.0 | 288* | 517 | 55.7% | — |
| Boys Wings | 12 | 12.8 | 25.5 | 34 | 64 | **51.6%** | **0.75** |
| Tumbling | 12 | 9.0 | 18.0 | 62 | 76 | **81.6%** | 0.29 |

\* Team enrolment triple-counts. Unique athletes ≈ 77.

34 distinct instructor names appear. `MAG A.` is a generic/admin account and must be excluded.

**Boys Wings is the strongest operational finding**: emptiest classes *and* the most coach-expensive
per student. Coach cost is fixed once a class runs, so those empty seats are lost margin, not avoided
cost.

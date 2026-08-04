# CURRENT_STATUS.md

Last updated: 28 July 2026. All source reports were exported from Jackrabbit on that date.

## The one-paragraph version

Revenue is fully mapped and reconciled to zero variance for 2023, 2024, 2025 and 2026 YTD. Unit
counts are done for every row that Jackrabbit can support. **Cost of Sales has not been started** —
it is not in Jackrabbit and requires coach payroll data, which has not been requested yet. Because
Cost of Sales is empty, every gross-profit figure in the workbook currently equals revenue and
**must not be presented to the client**.

---

## ✅ Completed

### Revenue mapping — done and verified
- All four periods parsed from the Revenue Summary PDFs and mapped to 18 service rows.
- **Zero variance on all four periods.** Verified programmatically; the build script prints it.
- The `--No Activity Name--` decomposition fully explains the previously "unattributed" $94,922
  (2025) down to $0.00 residual. 2023 and 2024 leave $36.00 and $671.40, both traced to three
  specific classes with no Category 1.

### Unit counts — done for everything Jackrabbit supports
- Class enrolments for the 7 comparable rows, de-duplicated: **5,684 / 6,199 / 6,341**.
- Open Gym bookings, birthday parties, retail items, private lessons, gift certificates.
- Membership units as a live formula (revenue ÷ $45).

### Category / structure investigation — done
- Cat1/Cat2/Cat3 hierarchy understood and documented.
- Category drift across years identified and quantified.
- Team's triple-enrolment structure identified; 2023 tuition-vs-meet-fee split completed.
- The eight untagged 2025 "Workshops & Class Series" classes identified by name, with their correct
  destinations ($1,364 → Tumbling, $1,770 → Girls Wings).

### Store / retail analysis — done
- 81 item numbers classified into merchandise vs fee/service.
- Team apparel identified as posting under Cat1 Team, explaining the Pro Shop reconciliation gap.
- Destira leotard confirmed as the $42.20 SKU ($40 + 5.5% Maine tax).
- Falmouth Rec 70/30 revenue share decoded from the Note field and verified against totals.
- Private-lesson coach attribution extracted (91% coverage in 2026).

### Deliverables shipped
| File | Status |
|---|---|
| `outputs/MAG_ServiceLinePerformance_v8.xlsx` | **Current.** 3 tabs, 4 periods, 18 rows. |
| `outputs/MAG_RevenueByService_2023-2026YTD.xlsx` | **Current.** Revenue-only view + findings + drift tabs. |
| `outputs/MAG_JackrabbitClassMapping.xlsx` | Current. 176 classes mapped, zero unmapped. |
| `outputs/MAG_CompanyProfile_v2.docx` | Current. 5-page business profile. |
| `outputs/MAG_JackrabbitCrosswalk_template.xlsx` | Reusable blank crosswalk template. |
| `outputs/superseded/` | 11 earlier versions, retained deliberately. |

---

## 🟡 Partially completed

### Team tuition vs meet-fee split — 2023 only
2023 is split: **$377,627.07 tuition / $140,104.38 meet fees & other**. The same split for 2024, 2025
and 2026 has **not** been done. Until it is, the Team row mixes real tuition with pass-through meet
entries and team gross margin cannot be calculated. The method is established — sum the
billing-group activity lines from the parsed Revenue Summary and treat the residual as meet fees.

### Instructor attribution — current session only
Coach-hours per service line are calculated for the 2026-27 session from the Class List. But joining
*historical revenue* to instructors via class name covers only **58% of 2026 and 37% of 2025** revenue,
because the class list holds only the current session. Not reliable enough to build on.

### Coach identification in private lessons — extracted but not cleaned
Coach names pulled from free-text notes. Coverage 8% / 9% / 46% / 91%. The name list almost certainly
contains duplicates (Kel/Kjeld, Dani/Danica, Nikki/Nicole) and needs a human pass.

### Falmouth Rec and Visiting Team rental — quantified but not on the grid
Both are real revenue with full quantities and economics documented on the `Store Detail` tab. They
are **not** on the main grid because their Jackrabbit Cat1 could not be verified — see Known Problems.

---

## ❌ Not started

### Cost of Sales — the big one
Nothing has been done. It does not exist in Jackrabbit. What is needed:
1. **Coach hourly rates** — from payroll or the bookkeeper. Not requested yet.
2. **Actual hours worked** — `Reports → Clock` in Jackrabbit. Not pulled.
3. Scheduled coach-hours per service line **are** available for the current session (see
   PROJECT_CONTEXT §6) and can serve as a fallback if actual hours prove hard to get.

Consequence: `Cost of Sales %`, `Total Cost of Sales`, `Gross Profit` and `Gross Profit %` are all
empty or meaningless in the current workbook.

### Pro Shop cost of goods
Pro Shop is the one row where cost of sales is inventory purchase cost, not labour. No supplier cost
data has been obtained. Destira wholesale pricing would be the place to start.

### Price-versus-volume decomposition
Cannot be done — historical class prices are unavailable because the class list export covers only the
current session. Fixable by re-running the Class List with archived sessions included.

### Same-period 2026 comparison
2026 YTD is currently compared to full years via a straight-line annualisation, which ignores
seasonality (July sits in the summer trough). The honest version needs Revenue Summary run for
1 Jan – 28 Jul in 2024 and 2025 so the seasonality cancels. Two reports, not yet pulled.

### Client-facing presentation
No deck or presentation has been built. Everything so far is working analysis.

---

## Known problems and unresolved questions

### Data problems

1. **The 2026 Class/Event export is defective.** Enrolment column covers `1/1/2025 – 7/28/2026`
   (19 months) against 7 months of revenue. 2026 class-enrolment units are therefore blank. Its
   revenue also differs from the Revenue Summary by $775. **Needs re-running with matching dates.**
2. **$12,817.63 of unapplied payments by July 2026**, up from $172 in 2023 — and *worsening*. Real
   cash sitting unallocated on family accounts. Independent of the analysis; an operational item.
3. **Late fees rising sharply** — 8 → 7 → 24 → 46 charges. Same underlying story as #2: collections
   are drifting.
4. **$24,120 of unlinked tuition in 2025** (Recreational $16,503 + Team $7,617). Preventable going
   forward by posting tuition through the class-linked routine and inactivating rather than deleting
   classes. Not economically recoverable retroactively (~100 transactions/year at 0.7% of revenue).
   Trend is strongly positive: down 54% from the 2024 peak.
5. **Eight 2025 classes have no Category 2** ("Workshops & Class Series"), plus three classes across
   2023/2024 with no Category 1 at all. All identified by name. Fixing them in Jackrabbit corrects
   every historical report automatically, because the reports read each class's *current* category.
6. **Staff category spiked to $10,226.82 in 2024** from $2,660 the prior year and $3,825 after. No
   explanation found.

### Unresolved questions — for the client

1. **Which Cat1 do `FALREC` and `VTM` post to?** One lookup in Jackrabbit (`Store` → item setup →
   revenue category). This both unblocks promoting them to the grid **and** may explain a large share
   of the unlinked tuition bucket — Falmouth Rec alone is $8,258 in 2023, about 38% of that year's
   unlinked total.
2. **Was Birthday Parties a deliberate exit?** $45,767 → $19,038 → nil, with almost no coach cost
   attached. The website still shows party photographs but has no Parties page.
3. **Did Falmouth Rec end, or did MAG end it?** $8,258 → $8,201 → $4,242 → nil.
4. **Is the American Flyers Cup on MAG's books or the Booster Club's?** Partially answered — Cup
   revenue *does* appear under Cat1 Team ($9,445 for the 2023 and 2024 editions). But the American
   Flyers Booster Club is a separate 501(c)(3) and may hold other Cup revenue.
5. **What is "Non-Instructional time"?** New Cat1 in 2025, $340. Small, but worth knowing before it
   grows.
6. **Is Susan an employee or a contractor?** She is the entire premium ancillary line — private
   lessons plus the Xcel clinic. A material concentration risk either way.

### Methodological caveats to preserve

1. **The membership-fee student proxy is wrong.** Revenue ÷ $45 implies 1,295 / 1,370 / 1,173
   students, i.e. a 14% fall in 2025. Class enrolments went the *other way* (+2.3%). Treat the
   membership figure as a billing-timing artefact. It is flagged in the workbook — keep it flagged.
   An earlier draft of the analysis led with the 14% figure; that was wrong and was retracted.
2. **Revenue and units come from different reports** with a ~1–2% attribution difference. Documented
   on the sheet. Never silently mix them.
3. **Girls Wings' +33.6% in 2024 is overstated** by roughly the $26,248 of Pre-Team revenue that
   folded into it when the `Pre-Team (Invite Only)` Cat2 disappeared.
4. **Coach-hours assume each listed instructor works the full class duration**, which overstates
   hours where a coach floats between groups.

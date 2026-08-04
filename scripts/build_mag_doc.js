const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  LevelFormat, convertInchesToTwip, Footer, PageNumber
} = require('docx');
const fs = require('fs');

const ACCENT = '1F3864';
const GREY = '595959';
const CONTENT_W = 9360; // 6.5" at 1440 dxa/inch

const H = (text, level) => new Paragraph({
  text, heading: level,
  spacing: { before: level === HeadingLevel.HEADING_1 ? 320 : 240, after: 120 },
});

const P = (text, opts = {}) => new Paragraph({
  spacing: { after: 120, line: 264 },
  children: [new TextRun({ text, ...opts })],
});

// Rich paragraph from an array of {text, bold, italics}
const RP = (runs) => new Paragraph({
  spacing: { after: 120, line: 264 },
  children: runs.map(r => new TextRun(r)),
});

const BULLET = (text, runs) => new Paragraph({
  numbering: { reference: 'mag-bullets', level: 0 },
  spacing: { after: 100, line: 276 },
  children: runs ? runs.map(r => new TextRun(r)) : [new TextRun(text)],
});

const NUM = (runs) => new Paragraph({
  numbering: { reference: 'mag-numbers', level: 0 },
  spacing: { after: 120, line: 276 },
  children: runs.map(r => new TextRun(r)),
});

const RULE = () => new Paragraph({
  spacing: { before: 60, after: 200 },
  border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: 'BFBFBF', space: 1 } },
  children: [new TextRun({ text: '' })],
});

const NOBORDER = {
  top:    { style: BorderStyle.NIL }, bottom: { style: BorderStyle.NIL },
  left:   { style: BorderStyle.NIL }, right:  { style: BorderStyle.NIL },
  insideHorizontal: { style: BorderStyle.NIL }, insideVertical: { style: BorderStyle.NIL },
};

function factRow(label, value, shaded) {
  const cell = (children, width) => new TableCell({
    width: { size: width, type: WidthType.DXA },
    shading: shaded ? { type: ShadingType.CLEAR, fill: 'F2F4F8', color: 'auto' } : undefined,
    margins: { top: 90, bottom: 90, left: 130, right: 130 },
    children,
  });
  return new TableRow({
    children: [
      cell([new Paragraph({ children: [new TextRun({ text: label, bold: true, color: ACCENT, size: 20 })] })], 2600),
      cell([new Paragraph({ children: [new TextRun({ text: value, size: 20 })] })], 6760),
    ],
  });
}

// ---- service line table ----
const serviceRows = [
  ['Recreational Tuition — Preschool (The Jungle)', 'Monthly', 'First / Second Flight, Soaring Eagles'],
  ['Recreational Tuition — Girls Wings',            'Monthly', 'Red through Gold Wings, K–19'],
  ['Recreational Tuition — Boys Wings',             'Monthly', 'Red, White, Blue Wings, ages 5–18'],
  ['Recreational Tuition — Tumbling',               'Monthly', 'Beginner to advanced, ages 5–21'],
  ['Seasonal — Summer Intensives',                  'Flat 6-week fee', 'Summer mini-sessions'],
  ['Competitive — American Flyers Teams',           'Monthly by hour tier', 'Xcel, WDP, Mens & Womens Devo'],
  ['Ancillary — Open Gym',                          'Per session, prepaid', 'One-hour sessions, to age 21'],
  ['Ancillary — Annual Membership Fees',            '$45 per student, annual', 'Charged on enrolment'],
];

function svcCell(text, width, shaded, bold) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    shading: shaded ? { type: ShadingType.CLEAR, fill: 'F2F4F8', color: 'auto' } : undefined,
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({ children: [new TextRun({ text, size: 18, bold: !!bold })] })],
  });
}

function svcHeaderRow() {
  const cell = (text, width) => new TableCell({
    width: { size: width, type: WidthType.DXA },
    shading: { type: ShadingType.CLEAR, fill: ACCENT, color: 'auto' },
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({ children: [new TextRun({ text, size: 18, bold: true, color: 'FFFFFF' })] })],
  });
  return new TableRow({ children: [cell('Service line', 3400), cell('Billing basis', 3100), cell('Contains', 2860)] });
}

function svcRow(r, shaded) {
  return new TableRow({
    children: [svcCell(r[0], 3400, shaded, true), svcCell(r[1], 3100, shaded), svcCell(r[2], 2860, shaded)],
  });
}

// ---- fill rate table ----
const fillRows = [
  ['Tumbling',            '62 / 76',   '81.6%', 'Best utilised service'],
  ['Girls Wings',         '402 / 579', '69.4%', 'Largest line, ~40% of enrolment'],
  ['Preschool',           '211 / 309', '68.3%', 'Funnel feeder'],
  ['Boys Wings',          '33 / 64',   '51.6%', 'Roughly half empty'],
];

function fillHeaderRow() {
  const cell = (text, width) => new TableCell({
    width: { size: width, type: WidthType.DXA },
    shading: { type: ShadingType.CLEAR, fill: ACCENT, color: 'auto' },
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({ children: [new TextRun({ text, size: 18, bold: true, color: 'FFFFFF' })] })],
  });
  return new TableRow({
    children: [cell('Service', 3600), cell('Enrolled / capacity', 1500), cell('Fill', 1500), cell('Note', 2760)],
  });
}

function fillRow(r, shaded) {
  return new TableRow({
    children: [
      svcCell(r[0], 3600, shaded, true), svcCell(r[1], 1500, shaded),
      svcCell(r[2], 1500, shaded, true), svcCell(r[3], 2760, shaded),
    ],
  });
}

const facts = [
  ['Legal / trade name', 'Maine Academy of Gymnastics ("MAG")'],
  ['Location', '20 Terminal Street, Westbrook, ME 04092 (greater Portland)'],
  ['Established', '1991'],
  ['Ownership', 'Family-owned and operated by the Amundson family'],
  ['Facility', '13,500 sq ft — main gym plus a separate two-level "Jungle Gym"'],
  ['Affiliation', 'Member club, USA Gymnastics (USAG)'],
  ['Phone / email', '(207) 856-0232 · info@maineacademy.com'],
  ['Website', 'maineacademy.com'],
  ['Management system', 'Jackrabbit Class (registration, billing, skill tracking)'],
  ['Positioning', '"Where Fitness Is Fun"'],
];

const doc = new Document({
  creator: 'RealTech',
  title: 'Maine Academy of Gymnastics — Company Profile',
  description: 'Business overview compiled from maineacademy.com',
  numbering: {
    config: [
      {
        reference: 'mag-bullets',
        levels: [{
          level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: convertInchesToTwip(0.3), hanging: convertInchesToTwip(0.18) } } },
        }],
      },
      {
        reference: 'mag-numbers',
        levels: [{
          level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: convertInchesToTwip(0.35), hanging: convertInchesToTwip(0.23) } } },
        }],
      },
    ],
  },
  styles: {
    default: {
      document: { run: { font: 'Calibri', size: 22, color: '262626' } },
    },
    paragraphStyles: [
      { id: 'Title', name: 'Title', basedOn: 'Normal', next: 'Normal',
        run: { size: 44, bold: true, color: ACCENT, font: 'Calibri' },
        paragraph: { spacing: { after: 80 } } },
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 30, bold: true, color: ACCENT, font: 'Calibri' } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 24, bold: true, color: '2E5496', font: 'Calibri' } },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun({ text: 'Maine Academy of Gymnastics — Company Profile   |   ', size: 16, color: GREY }),
            new TextRun({ children: [PageNumber.CURRENT], size: 16, color: GREY }),
          ],
        })],
      }),
    },
    children: [
      new Paragraph({ text: 'Maine Academy of Gymnastics', heading: HeadingLevel.TITLE }),
      new Paragraph({
        spacing: { after: 40 },
        children: [new TextRun({ text: 'Company Profile & Business Overview', size: 26, color: GREY })],
      }),
      new Paragraph({
        spacing: { after: 60 },
        children: [new TextRun({ text: 'Prepared by RealTech  ·  July 2026', size: 18, color: GREY, italics: true })],
      }),
      RULE(),

      H('Summary', HeadingLevel.HEADING_1),
      P('Maine Academy of Gymnastics (MAG) is a family-run gymnastics training center in Westbrook, Maine, just outside Portland, operating since 1991 and owned by the Amundson family. It is a USA Gymnastics member club housed in a 13,500 sq ft facility split into a main gym with full USAG apparatus, trampolines and an in-ground foam pit, plus a separate two-level "Jungle Gym" sized for ages 1–6.'),
      P('Revenue comes from monthly recreational tuition (year-round continuous enrollment, with a $45 annual membership fee for new students), preschool programs, invite-only Pre-Team and the competitive American Flyers boys’ and girls’ teams, prepaid Open Gym sessions, and the annually hosted American Flyers Cup meet. Registration, billing and skill tracking all run on Jackrabbit Class.'),

      H('At a Glance', HeadingLevel.HEADING_1),
      new Table({
        width: { size: CONTENT_W, type: WidthType.DXA },
        columnWidths: [2600, 6760],
        borders: NOBORDER,
        rows: facts.map(([l, v], i) => factRow(l, v, i % 2 === 0)),
      }),
      new Paragraph({ text: '', spacing: { after: 120 } }),

      H('Facility', HeadingLevel.HEADING_1),
      P('The business describes its 13,500 sq ft facility as one of the largest and best-equipped training centers in New England, serving everyone from beginners to National Team members. It is organized into two distinct spaces:'),
      BULLET(null, [
        { text: 'Main gym — ', bold: true },
        { text: 'full USAG apparatus covering the six Olympic events for boys and four for girls, plus trampolines, a large in-ground foam pit, and a rock climbing wall.' },
      ]),
      BULLET(null, [
        { text: 'The Jungle Gym — ', bold: true },
        { text: 'a separate two-level preschool space fitted with "Just My Size" modified equipment, slides, trampolines and two foam pits, purpose-designed for ages 1–6.' },
      ]),
      P('Three parent viewing rooms give sightlines into every space in the gym, with WiFi throughout the building. Equipment is described as continually upgraded.'),

      H('Revenue Lines', HeadingLevel.HEADING_1),
      P('Five distinct revenue streams, in approximate order of likely volume:'),
      NUM([
        { text: 'Recreational tuition. ', bold: true },
        { text: 'Billed monthly against a continuous, year-round curriculum with no session start or end point. Families may withdraw, re-enroll, or switch days and times at any point subject to availability. A $45 annual membership fee applies to all new students. Classes require a minimum of three students to run.' },
      ]),
      NUM([
        { text: 'Preschool (the Jungle). ', bold: true },
        { text: 'The primary funnel feeder — the business states it specializes in preschool development. Progression runs First Flight (walking to 3 years, adult-assisted at a 1:1 ratio), Second Flight (3–4 years, 5:1 ratio), then Soaring Eagles (4 to 5½ years). Super Flyers 1 and 2 exist in the structure but currently show no available classes.' },
      ]),
      NUM([
        { text: 'Competitive teams. ', bold: true },
        { text: 'Invite-only Pre-Team feeding the American Flyers boys’ and girls’ teams. Maine State Champions for over a decade, with athletes competing at State, Regional and National USAG levels. Higher training hours and higher revenue per athlete, but substantially higher family commitment.' },
      ]),
      NUM([
        { text: 'Open Gym. ', bold: true },
        { text: 'One-hour supervised sessions, prepaid and preregistered at least one hour in advance; drop-ins have been discontinued. Open to participants up to age 21, with no charge or registration for non-participating parents and siblings.' },
      ]),
      NUM([
        { text: 'Hosted meets. ', bold: true },
        { text: 'MAG runs the American Flyers Cup annually, drawing gymnasts from across New England. Operated under a separate website and separate economics.' },
      ]),

      H('The Progression Ladder', HeadingLevel.HEADING_1),
      P('The recreational level structure is the core retention mechanic. Girls advance Red → White → Blue → Silver → Gold Wings, with weekly training hours rising from 1¼ to 2 as they climb. Boys advance Red → White → Blue.'),
      P('Each advancement gates on a coach-verified skill checklist that parents can view in the Jackrabbit portal. That combination is an effective retention engine: parents see measurable progress, students see the next rung, and billable weekly hours increase with level. Tumbling (ages 5–21, at beginner, intermediate and advanced) runs alongside as a non-Olympic-track alternative. Red Wings entry requires the student to be age 5 by October 15 of the current year.'),

      H('Operations', HeadingLevel.HEADING_1),
      BULLET(null, [
        { text: 'Jackrabbit Class ', bold: true },
        { text: 'is the system of record — registration, class availability, monthly billing, and the student skill checklists exposed to parents through a portal.' },
      ]),
      BULLET(null, [
        { text: 'Staff certification. ', bold: true },
        { text: 'All coaching staff hold USAG and/or Red Cross safety certification; senior staff attend national clinics and training seminars annually.' },
      ]),
      BULLET(null, [
        { text: 'American Flyers Booster Club. ', bold: true },
        { text: 'A separate parent-run 501(c)(3) whose primary function is fundraising in support of the competitive teams.' },
      ]),
      BULLET(null, [
        { text: 'Marketing. ', bold: true },
        { text: 'WordPress website, with active Instagram and Facebook presences. Photography by Peter Guyton; site by David E.M. Wood.' },
      ]),

      H('Service Line Structure', HeadingLevel.HEADING_1),
      P('For revenue and margin analysis, the business resolves into eight service lines. The grouping prefix is the billing mechanism, because that is what drives margin behaviour.'),
      new Table({
        width: { size: CONTENT_W, type: WidthType.DXA },
        columnWidths: [3400, 3100, 2860],
        borders: NOBORDER,
        rows: [
          svcHeaderRow(),
          ...serviceRows.map((r, i) => svcRow(r, i % 2 === 0)),
        ],
      }),
      new Paragraph({ text: '', spacing: { after: 120 } }),
      RP([
        { text: 'Two lines were deliberately excluded. ', bold: true },
        { text: 'Pre-Team exists as only two classes and ten students, and Jackrabbit already files them under the girls’ and boys’ recreational categories — as a revenue line it is rounding error, so it is better tracked as a headcount metric. The American Flyers Cup is omitted pending confirmation of whose books it runs through: the Booster Club is a separate 501(c)(3), and if meet revenue sits there it is a different legal entity.' },
      ]),

      H('How Jackrabbit Is Configured', HeadingLevel.HEADING_1),
      P('A class-list export of 176 classes (July 2026) shows the practice-management system supports this structure, with two important caveats.'),
      BULLET(null, [
        { text: 'Category hierarchy works. ', bold: true },
        { text: 'Category 1 splits Recreational (155 classes) from Team (18) and Staff placeholders (3). Category 2 then carries the service level — Rec Girls (86), Pre-School (36), Rec Boys (12), Tumble (12), Parent-Child (9). Category 3 gives the individual rung on the ladder. All 176 classes map to a service line with no exceptions.' },
      ]),
      BULLET(null, [
        { text: 'Team athletes are enrolled three times over. ', bold: true },
        { text: 'Only seven of the eighteen Team records carry tuition; these are hour-tier billing groups running from $255 per month for one day to $543 for twenty hours. The remaining eleven are zero-dollar containers — a squad roster plus practice groups. Each athlete appears in a billing group, a practice group and the roster, so summing enrolment across all eighteen returns 288 for what is approximately 77 people. Team revenue must be taken from the billing groups alone.' },
      ]),
      BULLET(null, [
        { text: 'Team revenue cannot be split by gender. ', bold: true },
        { text: 'Billing groups are priced by training hours and are gender-blind. Headcount can be inferred from the practice groups, but the dollars cannot be separated between the boys’ and girls’ programmes.' },
      ]),
      BULLET(null, [
        { text: 'Thirty-six classes carry no tuition ', bold: true },
        { text: '— waitlists, roster containers, practice groups and staff placeholders. These must be excluded from any pricing average.' },
      ]),
      BULLET(null, [
        { text: 'Cost of sales does not exist in Jackrabbit. ', bold: true },
        { text: 'The system has no cost-of-goods concept. For a gymnastics business, cost of sales is essentially coach labour, so it has to be built from payroll records against the class schedule.' },
      ]),
      BULLET(null, [
        { text: 'The class list holds no history. ', bold: true },
        { text: 'The export contained only 2026–27 and summer 2026 sessions — not a single 2023, 2024 or 2025 class. Current pricing and enrolment are available; multi-year trend data must come from the revenue and transaction reports filtered by date range.' },
      ]),

      H('Capacity Utilisation', HeadingLevel.HEADING_1),
      P('Fill rates from the July 2026 class list, calculated as enrolled students against stated class maximums:'),
      new Table({
        width: { size: CONTENT_W, type: WidthType.DXA },
        columnWidths: [3600, 1500, 1500, 2760],
        borders: NOBORDER,
        rows: [
          fillHeaderRow(),
          ...fillRows.map((r, i) => fillRow(r, i % 2 === 0)),
        ],
      }),
      new Paragraph({ text: '', spacing: { after: 120 } }),
      P('Coach cost is fixed once a class runs, so an empty seat is lost margin rather than avoided cost. On that basis the boys’ programme is the clearest opportunity in the business: eleven classes running at roughly half capacity. Tumbling sits at the opposite end and may warrant added capacity.'),

      H('Observations & Open Issues', HeadingLevel.HEADING_1),

      H('Staffing is the visible bottleneck', HeadingLevel.HEADING_2),
      P('Coach recruitment occupies a homepage slide, a scrolling ticker item, and a floating site-wide button, and offers tuition discounts as a perk. A "Coach in Training" program grows talent internally rather than hiring it in — a reasonable response to a thin local labor pool, but it signals that capacity is constrained by staff rather than by demand or floor space.'),

      H('Stale content', HeadingLevel.HEADING_2),
      RP([
        { text: 'Every girls’ and boys’ recreational class block still carries the notice ' },
        { text: '"Due to COVID-19, Gymnastics Classes are under a revised schedule and format until September."', italics: true },
        { text: ' The page was last modified in February 2026. Separately, Super Flyers 1 and 2 both display "no classes available at this time," leaving a visible gap in the advertised preschool progression.' },
      ]),

      H('No published pricing', HeadingLevel.HEADING_2),
      P('Apart from the $45 annual membership fee, no tuition figures appear anywhere on the site. Every path routes to Jackrabbit or a phone call. This may be deliberate, but it is friction for a comparison-shopping parent evaluating several Portland-area gyms.'),

      H('Technical defects', HeadingLevel.HEADING_2),
      BULLET(null, [
        { text: 'Broken footer links: ' },
        { text: '/preschool-the-jungle/', bold: true },
        { text: ' and ' },
        { text: '/employment/', bold: true },
        { text: ' — the live pages sit under ' },
        { text: '/gymnastics-classes/', bold: true },
        { text: ' and ' },
        { text: '/about/', bold: true },
        { text: ' respectively.' },
      ]),
      BULLET(null, [
        { text: 'Inconsistent navigation between pages — some versions list "American Flyers Cup" plus a "Booster Club" item, while others show "American Flyers Hosted Meets" and omit the Booster Club entirely.' },
      ]),

      RULE(),
      new Paragraph({
        keepLines: true,
        children: [
          new TextRun({ text: 'Source: ', bold: true, size: 18, color: GREY }),
          new TextRun({
            text: 'Compiled from a full crawl of the public maineacademy.com website and a Jackrabbit Class List export of 176 classes, both 28 July 2026. Website figures and claims are as stated by the business; enrolment, capacity and pricing figures are from the class export.',
            size: 18, color: GREY, italics: true,
          }),
        ],
      }),
    ],
  }],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(process.argv[2], buf);
  console.log('wrote', process.argv[2], buf.length, 'bytes');
});

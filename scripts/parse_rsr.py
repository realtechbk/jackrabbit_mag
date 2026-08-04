"""Parse a Jackrabbit Revenue Summary PDF (pdftotext -layout output) into
Cat1 / Cat2 / activity-level records."""
import re
import sys
import json

MONEY = r"-?[\d,]+\.\d{2}"


def parse(path):
    lines = open(path, encoding="utf-8", errors="replace").read().split("\n")

    period = None
    grand = {"disc": None, "amt": None}
    cat1_totals = {}          # cat1 -> [amount, discount]
    cat2_totals = {}          # (cat1, cat2) -> [amount, discount]
    activities = []           # (cat1, cat2, name, disc, amt)

    cur1 = None
    cur2 = None

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            continue

        if period is None:
            m = re.search(r"(\d{1,2}/\d{1,2}/\d{4})\s*-\s*(\d{1,2}/\d{1,2}/\d{4})", line)
            if m and "Date:" not in line:
                period = (m.group(1), m.group(2))
                continue

        if "Date:" in line or "Revenue Summary" in line or line.strip().startswith("Cat1"):
            continue
        if "Total Revenue*" in line or line.strip().startswith("*Due to"):
            continue

        # grand total
        m = re.search(r"Totals:\s+(\d+)\s+(" + MONEY + r")\s+(" + MONEY + r")\s*$", line)
        if m:
            grand["disc"] = float(m.group(2).replace(",", ""))
            grand["amt"] = float(m.group(3).replace(",", ""))
            continue

        indent = len(line) - len(line.lstrip())
        body = line.strip()

        # Cat1 heading: starts at column 0 (may begin with '--', e.g. '--Unapplied Payments--')
        if indent == 0 and not re.match(r"^[\d,]", body) and "Subtotal" not in body:
            cur1 = body
            cur2 = None
            cat1_totals.setdefault(cur1, [0.0, 0.0])
            continue

        # subtotal lines
        m = re.match(r"^(.*?)\s+Subtotal:\s+(\d+)\s+(" + MONEY + r")\s+(" + MONEY + r")\s*$", body)
        if m:
            what = m.group(1).strip()
            disc = float(m.group(3).replace(",", ""))
            amt = float(m.group(4).replace(",", ""))
            if cur1 and what == cur1:
                # A Cat2 can share its Cat1's name (e.g. 'Open Gym'), producing several
                # identically-labelled subtotals. The Cat1 subtotal is always the last
                # one in the section, so overwrite rather than accumulate.
                cat1_totals[cur1] = [amt, disc]
            elif what in ("Cat2",):
                key = (cur1, "(blank)")
                cat2_totals.setdefault(key, [0.0, 0.0])
                cat2_totals[key][0] += amt
                cat2_totals[key][1] += disc
            elif what.startswith("Cat3") or what in ("Cat3",):
                pass
            else:
                # named Cat2 or Cat3 subtotal; treat as Cat2 if it matches cur2
                key = (cur1, what)
                cat2_totals.setdefault(key, [0.0, 0.0])
                cat2_totals[key][0] += amt
                cat2_totals[key][1] += disc
            continue

        # activity line with numbers
        m = re.match(r"^(.*?)\s+(\d+)\s+(" + MONEY + r")\s+(" + MONEY + r")\s*$", body)
        if m:
            name = m.group(1).strip()
            activities.append({
                "cat1": cur1, "cat2": cur2, "name": name,
                "enroll": int(m.group(2)),
                "disc": float(m.group(3).replace(",", "")),
                "amt": float(m.group(4).replace(",", "")),
            })
            continue

        # activity line with no enrollment column (rare)
        m = re.match(r"^(.*?)\s+(" + MONEY + r")\s+(" + MONEY + r")\s*$", body)
        if m:
            activities.append({
                "cat1": cur1, "cat2": cur2, "name": m.group(1).strip(),
                "enroll": 0,
                "disc": float(m.group(2).replace(",", "")),
                "amt": float(m.group(3).replace(",", "")),
            })
            continue

        # bare label — a Cat2 or Cat3 heading
        if indent > 0 and "Subtotal" not in body and not re.search(MONEY, body):
            if indent <= 20:
                cur2 = body
            continue

    return {
        "period": period,
        "grand": grand,
        "cat1": {k: v for k, v in cat1_totals.items()},
        "cat2": {f"{a}||{b}": v for (a, b), v in cat2_totals.items()},
        "activities": activities,
    }


def label_for(path, parsed):
    """Key each parsed report by year.

    Prefer a 4-digit year in the filename; fall back to the year in the report's own
    date range; last resort, the filename stem. Never crash on an unexpected filename.
    """
    m = re.search(r"(20\d{2})", path.split("/")[-1])
    if m:
        return m.group(1)
    period = parsed.get("period")
    if period:
        m = re.search(r"(20\d{2})", period[0])
        if m:
            return m.group(1)
    return path.split("/")[-1].rsplit(".", 1)[0]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: parse_rsr.py <pdftotext-output.txt> [more.txt ...]")
        print("  first run: pdftotext -layout RevenueSummary_2025.pdf /tmp/y2025.txt")
        sys.exit(1)

    out = {}
    exit_code = 0
    for path in sys.argv[1:]:
        parsed = parse(path)
        year = label_for(path, parsed)
        out[year] = parsed
        g = parsed["grand"]
        s = sum(v[0] for v in parsed["cat1"].values())
        var = round((s or 0) - (g["amt"] or 0), 2)
        print(f"{year}: period={parsed['period']} reported={g['amt']} "
              f"sum_cat1={round(s, 2)} var={var}")
        if g["amt"] in (None, 0):
            print(f"  !! WARNING {year}: report total is {g['amt']}. "
                  f"An inverted date range returns 0.00 with no rows — check the period above.")
            exit_code = 1
        elif var != 0:
            print(f"  !! FAIL {year}: variance is {var}, must be 0.00. Do not use this output.")
            exit_code = 1

    json.dump(out, open("/tmp/parsed.json", "w"), indent=1)
    print("wrote /tmp/parsed.json")
    sys.exit(exit_code)

"""Render the monthly slide (HTML + PNG + PDF) and the Excel backing workbook."""
import html
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compute  # noqa: E402

ROOT = compute.ROOT
OUT = ROOT / "outputs"
NA = "Data Not Available"


def k(n):
    """12050 -> 12.05K, 2800 -> 2.8K, 196 -> 196 (September slide style)."""
    if n < 1000:
        return f"{n:,}"
    return f"{n / 1000:.2f}".rstrip("0").rstrip(".") + "K"


def pct(a, b):
    return f"{a / b * 100:.1f}%".replace(".0%", "%") if b else "0%"


def build(files, label="Oct", period="1–28 Oct"):
    d, stats, g, f = compute.main(files)
    live = [b for b in g.index if b != compute.CFG["other_label"] and g.loc[b, "leads"] > 0]
    n = f["leads"]
    rows = [
        (f"Leads in CRM ({label})", f"{n:,}", "100% base — TeleCRM Lead Charts"),
        ("Worked (past “New Lead”)", k(f["worked"]),
         f"{pct(f['worked'], n)} of leads; {k(f['new_lead'])} still “New Lead”"),
        ("Connected (open, no stage yet)", k(f["connected"]), f"{pct(f['connected'], f['worked'])} of worked"),
        ("Quality Pipeline (Qualified +)", k(f["quality"]),
         f"{pct(f['quality'], f['worked'])} of worked; Details Shared {k(f['details_shared'])}"),
        ("Meetings Scheduled (incl. held)", f"{f['sched']:,}",
         f"{pct(f['sched'], f['quality'])} of quality pipeline; {pct(f['sched'], n)} of leads"),
        ("Meetings Conducted", f"{f['held']:,}",
         f"{pct(f['held'], f['sched'])} held; {f['still_scheduled']:,} still “Scheduled”"),
        ("Direct LP Meetings", NA, "Booked from landing page — no SDR call"),
        ("Negotiation / Won", f"{f['negotiation']} / {f['won']}", "Late-stage deals in CRM"),
        ("Closed Lost", k(f["lost"]), f"{pct(f['lost'], n)} of leads"),
        ("MIB Closures", NA, "Sales / Finance to report"),
    ]
    return d, stats, g, f, live, rows, period


def to_html(g, f, live, rows, period):
    e = html.escape
    tot = g.sum()
    brand_rows = "".join(
        f"<tr><td>{e(b)}</td><td>{int(r.assigned):,}</td><td>{int(r.quality):,}</td>"
        f"<td>{int(r.sched):,} / {int(r.held):,}</td></tr>"
        for b, r in g.iterrows() if r.leads > 0)
    brand_rows += (f"<tr class='tot'><td>TOTAL</td><td>{int(tot.assigned):,}</td><td>{int(tot.quality):,}</td>"
                   f"<td>{int(tot.sched):,} / {int(tot.held):,}</td></tr>")
    fun_rows = "".join(
        f"<tr><td>{e(a)}</td><td>{e(b)}</td><td>{e(c)}</td></tr>" for a, b, c in rows)
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>Monthly Lead Report</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#f7f7f5;font-family:Arial,Helvetica,sans-serif;color:#1a2233}}
.slide{{width:1578px;padding:20px 24px 30px 49px;display:flex;gap:44px;align-items:flex-start}}
.left{{width:653px;flex:none}}.right{{width:808px;flex:none}}
h2{{margin:0 0 0;font-size:34px;color:#0d1b3d;font-weight:700;padding:4px 0 10px;border-bottom:3px solid #c9973a}}
.tiles{{display:flex;gap:16px;margin:12px 0 17px}}
.tile{{flex:1;background:#fff;border:2px solid #dcdcdc;border-radius:10px;padding:16px 20px 12px;height:136px;box-shadow:0 1px 3px #0002}}
.tile .l{{font-size:20px;font-weight:700;color:#5b6577}}.tile .v{{font-size:38px;font-weight:700;color:#0d1b3d;margin-top:22px}}
.tile .v.g{{color:#1e7b34}}.tile .v.sm{{font-size:21px;margin-top:30px}}
table{{border-collapse:collapse;background:#fff;width:100%;font-size:17px}}
td{{border:1px solid #d0d0d0;padding:10px 8px;vertical-align:middle;line-height:20px}}
.left tr:first-child td{{font-weight:700;color:#0d1b3d}}
tr.tot td{{font-weight:700}}
.right table{{margin-top:27px}}.right td:nth-child(1){{width:252px}}.right td:nth-child(2){{width:123px}}
.right tr td{{height:62px}}
</style></head><body><div class="slide">
<div class="left"><h2>Lead delivery by brand</h2>
<div class="tiles"><div class="tile"><div class="l">Brands Live</div><div class="v">{len(live)}</div></div>
<div class="tile"><div class="l">Leads in CRM</div><div class="v">{f['leads']:,}</div></div>
<div class="tile"><div class="l">Direct LP Meetings</div><div class="v g sm">N/A</div></div></div>
<table><tr><td>Brand ({period})</td><td>Assigned</td><td>Quality Pipeline</td><td>Meetings Sch / Held</td></tr>{brand_rows}</table></div>
<div class="right"><h2>Activity and conversion funnel</h2>
<table><tr><td>Metric</td><td>Count</td><td>Conversion / Comment</td></tr>{fun_rows}</table></div>
</div></body></html>"""


def write_excel(path, d, stats, g, f, rows, period):
    with pd.ExcelWriter(path) as w:
        t = g.reset_index().rename(columns={"brand": "Brand", "leads": "Leads", "assigned": "Assigned",
                                            "quality": "Quality Pipeline", "sched": "Meetings Scheduled",
                                            "held": "Meetings Held"})
        t.loc[len(t)] = ["TOTAL", *g.sum().astype(int).tolist()]
        t.to_excel(w, sheet_name="Brand table", index=False)
        pd.DataFrame(rows, columns=["Metric", "Count (display)", "Comment"]).to_excel(w, sheet_name="Funnel", index=False)
        pd.DataFrame(list(f.items()), columns=["Measure", "Exact count"]).to_excel(w, sheet_name="Exact counts", index=False)
        pd.DataFrame(list(stats.items()), columns=["Check", "Value"]).to_excel(w, sheet_name="Data checks", index=False)
        s = d.groupby(["brand", "Brand"]).size().rename("Leads").reset_index()
        s.columns = ["Mapped brand", "Raw Brand value", "Leads"]
        s.to_excel(w, sheet_name="Brand mapping used", index=False)
        d["Status"].value_counts().rename_axis("Status").reset_index(name="Leads").to_excel(w, sheet_name="Status counts", index=False)


def main():
    files = sorted((ROOT / "inbox" / "2026-10" / "raw").glob("*.csv"))
    d, stats, g, f, live, rows, period = build(files)
    OUT.mkdir(exist_ok=True)
    page = to_html(g, f, live, rows, period)
    (OUT / "Monthly_Lead_Report_Oct2026.html").write_text(page)
    write_excel(OUT / "Monthly_Lead_Report_Oct2026_backing.xlsx", d, stats, g, f, rows, period)
    import subprocess
    subprocess.run(["node", str(ROOT / "pipeline" / "screenshot.js"), str(OUT / "Monthly_Lead_Report_Oct2026.html"),
                    str(OUT / "Monthly_Lead_Report_Oct2026.png")], check=True)
    print("done", stats, len(live))


if __name__ == "__main__":
    main()

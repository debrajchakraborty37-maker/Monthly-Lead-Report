"""Load the two TeleCRM exports, filter the period, map brands and compute every report metric."""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "config" / "brand_map.json").read_text())


def map_brand(raw: str) -> str:
    b = str(raw).strip().lower()
    if b.startswith(tuple(CFG["fw_prefixes"])):
        return CFG["fw_label"]
    for key, label in CFG["rules"]:
        if key in b:
            return label
    return CFG["other_label"]


def load(files, start, end):
    frames = []
    for f in files:
        d = pd.read_csv(f, encoding="utf-8-sig", low_memory=False,
                        usecols=["Status", "Brand", "Assignee name", "Created On", "Lead id"], dtype=str)
        d["source_file"] = Path(f).name
        frames.append(d)
    raw = pd.concat(frames, ignore_index=True)
    raw["created"] = pd.to_datetime(raw["Created On"], format="%d/%m/%Y %H:%M:%S")
    stats = {"rows_loaded": len(raw)}
    d = raw[(raw["created"] >= start) & (raw["created"] < end)].copy()
    stats["rows_in_period"] = len(d)
    d = d.drop_duplicates("Lead id")
    stats["duplicates_removed"] = stats["rows_in_period"] - len(d)
    d["brand"] = d["Brand"].map(map_brand)
    d["assigned"] = d["Assignee name"].fillna("-").str.strip().ne("-")
    return d, stats


def compute(d):
    st = d["Status"]
    n = len(d)
    quality = st.isin(CFG["quality_statuses"])
    sched = st.isin(CFG["scheduled_statuses"])
    held = st.isin(CFG["held_statuses"])
    d = d.assign(quality=quality, sched=sched, held=held)
    g = d.groupby("brand").agg(leads=("brand", "size"), assigned=("assigned", "sum"),
                               quality=("quality", "sum"), sched=("sched", "sum"), held=("held", "sum"))
    order = CFG["brand_order"] + [CFG["other_label"]]
    g = g.reindex([b for b in order if b in g.index])
    funnel = {
        "leads": n,
        "worked": int((st != "New Lead").sum()),
        "new_lead": int((st == "New Lead").sum()),
        "connected": int((st == "Connected").sum()),
        "quality": int(quality.sum()),
        "details_shared": int((st == "Details Shared").sum()),
        "sched": int(sched.sum()),
        "held": int(held.sum()),
        "negotiation": int((st == "Negotiation").sum()),
        "won": int(st.isin(CFG["won_statuses"]).sum()),
        "lost": int(st.isin(CFG["lost_statuses"]).sum()),
        "assigned": int(d["assigned"].sum()),
    }
    funnel["still_scheduled"] = funnel["sched"] - funnel["held"]
    return g, funnel, d


def main(files, start="2026-10-01", end="2026-10-29"):
    d, stats = load(files, pd.Timestamp(start), pd.Timestamp(end))
    g, f, d = compute(d)
    return d, stats, g, f


if __name__ == "__main__":
    raw = sorted((ROOT / "inbox" / "2026-10" / "raw").glob("*.csv"))
    d, stats, g, f = main(raw)
    print(stats)
    print(g.to_string())
    print(g.sum())
    print(f)
    print(d["Status"].value_counts().to_string())

"""Build the monthly lead report from TeleCRM lead exports.

usage: python3 pipeline/run_monthly.py <raw_dir> --start 2026-11-01 --end 2026-11-30
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("raw_dir")
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True, help="inclusive last day, e.g. 2026-10-31")
    a = ap.parse_args()
    files = sorted(Path(a.raw_dir).glob("*.csv"))
    if not files:
        sys.exit(f"STOP: no CSV files in {a.raw_dir}")
    r = render.make(files, a.start, a.end)
    f, g = r["funnel"], r["brands"]
    ok = int(g["leads"].sum()) == f["leads"]
    print("stats:", r["stats"])
    print("brand rows sum to Leads in CRM:", ok)
    print("brands live:", r["live"])
    print("unmapped brand values (shown under Other / Unmapped):", r["unmapped_brand_values"])
    print("png:", r["png"])
    print("xlsx:", r["xlsx"])
    if not ok:
        sys.exit("QA FAILED: brand rows do not sum to total leads")


if __name__ == "__main__":
    main()

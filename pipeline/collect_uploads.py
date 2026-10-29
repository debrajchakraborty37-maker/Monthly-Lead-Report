"""Copy the newest uploaded TeleCRM lead CSVs into inbox/<YYYY-MM>/raw/.

usage: python3 pipeline/collect_uploads.py <YYYY-MM> [uploads_dir]
Takes every .csv uploaded in the last 24h in the uploads dir (default /root/.claude/uploads/*).
"""
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    month = sys.argv[1]
    base = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/root/.claude/uploads")
    cutoff = time.time() - 24 * 3600
    found = [p for p in base.rglob("*.csv") if p.stat().st_mtime >= cutoff]
    if not found:
        sys.exit("STOP: no uploaded CSV lead files found in the last 24 hours")
    dest = ROOT / "inbox" / month / "raw"
    dest.mkdir(parents=True, exist_ok=True)
    for p in sorted(found):
        shutil.copy2(p, dest / p.name)
        print("copied", p.name)
    print("raw dir:", dest)


if __name__ == "__main__":
    main()

# Monthly Lead Report

Builds the "Lead delivery by brand / Activity and conversion funnel" slide from TeleCRM lead exports.

1. Put the raw CSV exports in `inbox/<YYYY-MM>/raw/` (not committed).
2. `python3 pipeline/render.py` (needs pandas, openpyxl, and Node with playwright for the PNG).
3. Outputs land in `outputs/`: HTML, PNG slide and an Excel backing workbook with exact counts and the brand mapping.

Rules: period filter on `Created On`; de-duplicated on `Lead id`; any Brand starting `FW_`/`FW-` is the separate FW (Franchise World) brand; brand mapping and status lists live in `config/brand_map.json`. Direct LP Meetings and MIB Closures are not in the exports and show as not available.

---
name: monthly-lead-report
description: Monthly TeleCRM lead report agent. Use when the user attaches TeleCRM lead export CSVs (e.g. 1 Oct to 31 Oct) and asks for the monthly lead report / "Lead delivery by brand" slide. Builds the brand table + activity and conversion funnel slide (PNG) and a backing Excel workbook.
---

# Monthly Lead Report Agent

## Inputs
One or more TeleCRM lead-export CSVs (e.g. the main account and the Franchise World account). Required columns: `Status`, `Brand`, `Assignee name`, `Created On` (dd/mm/yyyy hh:mm:ss), `Lead id`. Ask the user for the period if they did not state it (start and last day, inclusive).

## Run
1. `python3 pipeline/collect_uploads.py <YYYY-MM>` copies the uploaded CSVs into `inbox/<YYYY-MM>/raw/` (or copy them there yourself).
2. `python3 pipeline/run_monthly.py inbox/<YYYY-MM>/raw --start <YYYY-MM-01> --end <last day>`
3. Outputs: `outputs/<YYYY-MM>/Monthly_Lead_Report_<Mon><Year>.png` (slide), `.html`, `_backing.xlsx` (exact counts, brand mapping, status counts, notes).
4. Send the PNG and the Excel to the user in chat (SendUserFile) with a short summary. Commit `outputs/` and any `config/` change; `inbox/*/raw/` is git-ignored (lead data).

## Rules (agreed with the user)
- Period = `Created On` between start 00:00 and end 23:59:59. Both files combined, de-duplicated on `Lead id`; counts are lead records, not unique phones.
- Brands: any Brand starting `FW_`/`FW-` is the separate **FW** (Franchise World) brand. All other mapping lives in `config/brand_map.json` (Kabego Rental = EBG Rental; Realty and blank brands = Other / Unmapped).
- Worked = every status except New Lead and Assigned. Quality Pipeline = Qualified, Details Shared, Meeting Scheduled/Conducted (+ "but NOT QUALIFIED"), Negotiation, Token Received. Meetings Scheduled (incl. held) = Meeting Scheduled + Meeting Conducted; Conducted = Meeting Conducted. Won = Token Received. Closed Lost = Lost + Reasons for Lost.
- Direct LP Meetings and MIB Closures are not in the exports: always "Data Not Available" unless the user supplies numbers.
- Never edit numbers by hand; fix the input or `config/brand_map.json`.

## Stop conditions
- `STOP: no CSV files` or missing required columns: tell the user what is missing.
- `QA FAILED` (brand rows do not sum to Leads in CRM): report it, do not send the slide.
- The run prints `unmapped brand values`. If a new, sizeable brand name appears there (not Realty/blank), ask the user which of the 16 brands it belongs to, add it to `config/brand_map.json`, and re-run.
- A brand in `config/brand_map.json` `brand_order` with zero leads is not counted in Brands Live; mention brands with only 1-2 leads.

## Before sending
Re-count the headline figures independently (csv module) and confirm they match the backing workbook.

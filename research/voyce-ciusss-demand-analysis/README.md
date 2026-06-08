# Voyce CIUSSS Demand Analysis

Analysis of interpretation demand at **CIUSSS Centre-Ouest-de-l'Île-de-Montréal**
(Quebec hospital network, includes Jewish General Hospital), based on Voyce
platform call data, **January–April 2025**.

## Headline findings (English-source)

- 7,288 of 7,625 calls (**95.6%**) originate in English, across **89 distinct target languages**
- English-source cancellation rate: **15.9%** (vs. 75.7% for French-source)
- Demand is highly concentrated: **Punjabi, Spanish, Bengali** = 50% of all serviced minutes
- Annualized true demand: **~492,800 min / yr** (≈ 8,214 hrs / yr)
- Video calls cancel **6.7×** more than audio

## Contents

- [`data/`](./data) — raw and derived workbooks
  - `Voyce data Jan - Apr JEWISH MEMORIAL.xlsx` — raw platform data
  - `Voyce_English_Analysis.xlsx`, `Voyce_French_Analysis.xlsx` — derived analytical workbooks
- [`reports/`](./reports) — narrative reports
  - `english_demand_report.{tex,pdf}` — English-source demand report
  - `french_demand_report.{tex,pdf}` — French-source demand report
  - `sgp_report.sty` — shared LaTeX styling
  - `build_workbook*.py`, `build_figures*.py` — pipeline to regenerate workbooks and charts
  - `figures/`, `figures_en/` — PDF and PNG chart outputs

## Pipeline

1. Drop the raw Voyce export into `data/`.
2. Run `build_workbook.py` and `build_workbook_english.py` to produce the derived workbooks.
3. Run `build_figures.py` and `build_figures_english.py` to produce charts.
4. Recompile the `.tex` reports.

## Attribution

The styling file is named `sgp_report.sty` — possibly because the work
was originally prepared for or branded around Simplified Group. If these
reports are deliverables for a specific client, move this folder into
that client's `deliverables/`.

# tax/

Bookkeeping + California tax estimator for ToosPoint Consulting LLC.

**Setup assumed** (see `data/config.json`):
- Single-member CA LLC, formed 2026-06-05
- No S-corp election → disregarded for federal, reports on Schedule C
- Filing status: single
- Cash basis accounting

## What it does

- Records **expenses** with Schedule C category tagging (Line 8–30)
- Records **income** received from paid invoices
- Generates YTD P&L (Schedule C, line 31)
- Estimates federal SE tax, federal income tax (with QBI), CA income tax,
  $800 CA franchise tax, and the CA LLC gross-receipts fee (Form 568)
- Tracks filing deadlines: quarterly estimated taxes, Form 3522, Form 568,
  1099-NEC, biennial Statement of Information

## What it does *not* do

- File anything
- Replace a CPA
- OCR receipts (manual entry only — drop the receipt file under `receipts/`
  or anywhere in the repo and reference it with `--file`)
- Handle edge cases: depreciation schedules, home office Form 8829 detail,
  AMT, NIIT, multi-state apportionment, S-corp reasonable-comp analysis

## Usage

Run from inside `tools/tax/`:

```bash
# record an expense
./tax.py add-expense --date 2026-06-15 --amount 49.99 \
  --category 18 --description "Notion subscription" \
  --payee "Notion Labs" --file receipts/notion-2026-06.pdf

# record income (when a client pays)
./tax.py add-income --date 2026-06-26 --amount 3800 \
  --client "iCall International" --invoice 001 \
  --file ../../clients/icall-international/invoices/2026-06-11_USD3800.00_Net15.pdf

# reports
./tax.py list-expenses --year 2026
./tax.py list-income --year 2026
./tax.py report
./tax.py deadlines

# reference
./tax.py categories
```

## Files

| Path | Purpose |
|---|---|
| `tax.py` | CLI entry point |
| `tax_rules.py` | Schedule C categories, tax brackets, calc functions, deadlines |
| `data/config.json` | entity info, formation date, filing status |
| `data/expenses.json` | append-only expense ledger |
| `data/income.json` | append-only income ledger (paid invoices only) |
| `receipts/` | drop receipt PDFs/images here |

## Tax constants

All brackets, standard deductions, SS wage base, and QBI phaseouts in
`tax_rules.py` are **2025 IRS / FTB published values**. The IRS and FTB
shift these ~2-3% annually for inflation — update `tax_rules.py` each
January when new tables publish.

## Disclaimer

⚠ **NOT TAX ADVICE.** Estimates are order-of-magnitude only. California
tax has too many edge cases — QBI phaseouts, depreciation methods, home
office, AMT, NIIT, S-corp election timing, multi-state nexus — for any
script to be authoritative. **Hire a CPA for your actual return.** Use
this tool to keep clean records, ballpark your quarterly payments, and
hand a tidy ledger to the professional at year-end.

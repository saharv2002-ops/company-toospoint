#!/usr/bin/env python3
"""ToosPoint tax tracker.

Records business expenses + received income, applies California + federal
rules, produces YTD P&L and a rough quarterly tax estimate.

NOT TAX ADVICE. Estimates only. Have a CPA review before filing.
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import tax_rules as rules


ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
EXPENSES_FILE = DATA_DIR / "expenses.json"
INCOME_FILE = DATA_DIR / "income.json"
CONFIG_FILE = DATA_DIR / "config.json"


# ─── storage helpers ────────────────────────────────────────────────────────
def load_json(path: Path, default):
    if not path.exists():
        return default
    with open(path) as f:
        return json.load(f)


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def next_id(entries: list, prefix: str, year: int) -> str:
    n = sum(1 for e in entries if e["id"].startswith(f"{prefix}-{year}-")) + 1
    return f"{prefix}-{year}-{n:03d}"


# ─── commands ───────────────────────────────────────────────────────────────
def cmd_add_expense(args):
    if not rules.validate_category(args.category):
        sys.exit(f"error: unknown Schedule C category '{args.category}' — run `categories`")
    expenses = load_json(EXPENSES_FILE, [])
    d = date.fromisoformat(args.date)
    entry = {
        "id": next_id(expenses, "exp", d.year),
        "date": args.date,
        "amount": round(float(args.amount), 2),
        "category": args.category,
        "category_name": rules.category_name(args.category),
        "description": args.description,
        "payee": args.payee,
        "file": args.file,
        "notes": args.notes,
    }
    expenses.append(entry)
    save_json(EXPENSES_FILE, expenses)
    print(f"added {entry['id']}: ${entry['amount']:,.2f} — {entry['description']}")


def cmd_add_income(args):
    income = load_json(INCOME_FILE, [])
    d = date.fromisoformat(args.date)
    entry = {
        "id": next_id(income, "inc", d.year),
        "date_received": args.date,
        "amount": round(float(args.amount), 2),
        "client": args.client,
        "invoice_no": args.invoice,
        "service_period": args.period,
        "file": args.file,
        "notes": args.notes,
    }
    income.append(entry)
    save_json(INCOME_FILE, income)
    print(f"added {entry['id']}: ${entry['amount']:,.2f} from {entry['client']}")


def cmd_list_expenses(args):
    expenses = load_json(EXPENSES_FILE, [])
    if args.year:
        expenses = [e for e in expenses if e["date"].startswith(str(args.year))]
    if args.category:
        expenses = [e for e in expenses if e["category"] == args.category]
    if not expenses:
        print("(no entries)")
        return
    total = 0.0
    for e in expenses:
        total += e["amount"]
        print(f"{e['id']:>14}  {e['date']}  ${e['amount']:>10,.2f}  L{e['category']:<4} {e['description']}")
    print(f"{'─' * 14}  {'─' * 10}  {'─' * 11}")
    print(f"{'TOTAL':>14}              ${total:>10,.2f}")


def cmd_list_income(args):
    income = load_json(INCOME_FILE, [])
    if args.year:
        income = [e for e in income if e["date_received"].startswith(str(args.year))]
    if not income:
        print("(no entries)")
        return
    total = 0.0
    for e in income:
        total += e["amount"]
        inv = f"Inv #{e['invoice_no']}" if e["invoice_no"] else ""
        print(f"{e['id']:>14}  {e['date_received']}  ${e['amount']:>10,.2f}  {e['client']} {inv}")
    print(f"{'─' * 14}  {'─' * 10}  {'─' * 11}")
    print(f"{'TOTAL':>14}              ${total:>10,.2f}")


def cmd_categories(args):
    print("Schedule C (Form 1040) — Part II expense categories:\n")
    for line, name in rules.SCHEDULE_C.items():
        print(f"  L{line:<5}  {name}")


def cmd_deadlines(args):
    year = args.year or date.today().year
    config = load_json(CONFIG_FILE, {})
    formation = date.fromisoformat(config["llc_formation_date"]) if config.get("llc_formation_date") else None
    today = date.today()
    print(f"\nTax deadlines for {year}:\n")
    for d, desc in rules.deadlines_for_year(year, formation):
        marker = "  " if d >= today else "✓ "
        days = (d - today).days
        days_str = f"+{days}d" if days >= 0 else f"{days}d"
        print(f"  {marker}{d.isoformat()}  {days_str:>6}  {desc}")
    print()


def cmd_report(args):
    year = args.year or date.today().year
    config = load_json(CONFIG_FILE, {})
    expenses = [e for e in load_json(EXPENSES_FILE, []) if e["date"].startswith(str(year))]
    income = [e for e in load_json(INCOME_FILE, []) if e["date_received"].startswith(str(year))]

    gross_income = sum(e["amount"] for e in income)
    total_expenses = sum(e["amount"] for e in expenses)
    meals = sum(e["amount"] for e in expenses if e["category"] == "24b")
    deductible_expenses = total_expenses - (meals * 0.5)
    net_profit = gross_income - deductible_expenses

    by_cat: dict[tuple[str, str], list[float]] = {}
    for e in expenses:
        by_cat.setdefault((e["category"], e["category_name"]), []).append(e["amount"])

    bar = "═" * 78
    print(f"\nToosPoint Tax Report — {year} YTD  (generated {date.today().isoformat()})")
    print(bar)

    print("\nINCOME RECEIVED")
    if income:
        for e in income:
            inv = f"Inv #{e['invoice_no']}" if e["invoice_no"] else ""
            print(f"  {e['date_received']}  ${e['amount']:>10,.2f}  {e['client']} {inv}")
        print(f"  {'─' * 60}")
        print(f"  {'Gross income':<55}  ${gross_income:>10,.2f}")
    else:
        print("  (none received this year)")

    print("\nEXPENSES BY SCHEDULE C CATEGORY")
    if by_cat:
        for (line, name), amts in sorted(by_cat.items()):
            print(f"  L{line:<4} {name:<50}  ${sum(amts):>10,.2f}  ({len(amts)})")
        print(f"  {'─' * 76}")
        print(f"  {'Total expenses':<55}  ${total_expenses:>10,.2f}")
        if meals > 0:
            print(f"  {'Less: 50% of meals not deductible':<55}  ${-meals * 0.5:>10,.2f}")
            print(f"  {'Deductible expenses':<55}  ${deductible_expenses:>10,.2f}")
    else:
        print("  (none recorded)")

    print("\nNET PROFIT / (LOSS)  — Schedule C, line 31")
    print(f"  {'Gross income':<55}  ${gross_income:>10,.2f}")
    print(f"  {'Less: deductible expenses':<55}  ${-deductible_expenses:>10,.2f}")
    print(f"  {'─' * 76}")
    print(f"  {'Net profit / (loss)':<55}  ${net_profit:>10,.2f}")

    se_tax_amt = rules.se_tax(net_profit)
    half_se = se_tax_amt / 2
    agi = net_profit - half_se
    taxable_before_qbi = max(0, agi - rules.FED_STD_DEDUCTION_SINGLE)
    qbi = rules.qbi_deduction(net_profit, taxable_before_qbi)
    fed_taxable = max(0, taxable_before_qbi - qbi)
    fed_tax = rules.federal_income_tax(fed_taxable)
    ca_taxable = max(0, net_profit - rules.CA_STD_DEDUCTION_SINGLE)
    ca_tax = rules.ca_income_tax(ca_taxable)
    franchise = rules.CA_LLC_MIN_FRANCHISE_TAX
    llc_fee = rules.ca_llc_fee(gross_income)
    total_tax = se_tax_amt + fed_tax + ca_tax + franchise + llc_fee

    print(f"\nESTIMATED {year} TAX LIABILITY  (rough — 2025 brackets)")
    print(f"  {'Self-employment tax (Schedule SE)':<55}  ${se_tax_amt:>10,.2f}")
    print(f"  {'Federal income tax (Form 1040)':<55}  ${fed_tax:>10,.2f}")
    if qbi > 0:
        print(f"  {'  (after QBI deduction of ' + f'${qbi:,.2f})':<55}")
    print(f"  {'CA personal income tax (Form 540)':<55}  ${ca_tax:>10,.2f}")
    print(f"  {'CA $800 LLC franchise tax (Form 3522)':<55}  ${franchise:>10,.2f}")
    print(f"  {'CA LLC gross-receipts fee (Form 568)':<55}  ${llc_fee:>10,.2f}")
    print(f"  {'─' * 76}")
    print(f"  {'Total estimated tax':<55}  ${total_tax:>10,.2f}")
    print(f"\n  Quarterly estimated payment (annual ÷ 4):  ${total_tax / 4:,.2f}")

    formation = date.fromisoformat(config["llc_formation_date"]) if config.get("llc_formation_date") else None
    today = date.today()
    upcoming = [(d, desc) for d, desc in rules.deadlines_for_year(year, formation) if d >= today][:6]
    if upcoming:
        print("\nNEXT 6 DEADLINES")
        for d, desc in upcoming:
            print(f"  {d.isoformat()}  (+{(d - today).days:3d}d)  {desc}")

    print("\n" + "─" * 78)
    print("⚠  Estimates only. Tax constants are 2025 IRS/FTB values — update annually.")
    print("⚠  NOT TAX ADVICE. Hand the year-end ledger to a CPA before filing.")
    print("─" * 78 + "\n")


# ─── argparse setup ─────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("add-expense", help="record a business expense")
    s.add_argument("--date", required=True, help="YYYY-MM-DD")
    s.add_argument("--amount", required=True, type=float)
    s.add_argument("--category", required=True, help="Schedule C line, e.g. 23, 24b")
    s.add_argument("--description", required=True)
    s.add_argument("--payee", default="")
    s.add_argument("--file", default="", help="path to receipt (relative to repo root preferred)")
    s.add_argument("--notes", default="")
    s.set_defaults(func=cmd_add_expense)

    s = sub.add_parser("add-income", help="record received payment (paid invoice)")
    s.add_argument("--date", required=True, help="date payment received, YYYY-MM-DD")
    s.add_argument("--amount", required=True, type=float)
    s.add_argument("--client", required=True)
    s.add_argument("--invoice", default="", help="invoice number")
    s.add_argument("--period", default="", help="service period covered")
    s.add_argument("--file", default="", help="path to invoice PDF")
    s.add_argument("--notes", default="")
    s.set_defaults(func=cmd_add_income)

    s = sub.add_parser("list-expenses", help="list recorded expenses")
    s.add_argument("--year", type=int)
    s.add_argument("--category", help="filter by Schedule C line")
    s.set_defaults(func=cmd_list_expenses)

    s = sub.add_parser("list-income", help="list recorded income")
    s.add_argument("--year", type=int)
    s.set_defaults(func=cmd_list_income)

    s = sub.add_parser("report", help="YTD P&L + tax estimate + upcoming deadlines")
    s.add_argument("--year", type=int)
    s.set_defaults(func=cmd_report)

    s = sub.add_parser("deadlines", help="all tax deadlines for the year")
    s.add_argument("--year", type=int)
    s.set_defaults(func=cmd_deadlines)

    s = sub.add_parser("categories", help="list Schedule C expense categories")
    s.set_defaults(func=cmd_categories)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

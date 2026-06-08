"""Tax constants and calculation helpers.

Constants are 2025 published IRS / FTB values unless flagged otherwise.
Brackets and thresholds shift each year for inflation — update annually.

NOT TAX ADVICE. Hand the year-end numbers to a CPA.
"""

from datetime import date
from typing import Optional


# ─── Schedule C (Form 1040) — Part II expense categories ─────────────────────
SCHEDULE_C: dict[str, str] = {
    "8":   "Advertising",
    "9":   "Car and truck expenses",
    "10":  "Commissions and fees",
    "11":  "Contract labor",            # 1099-NEC if >$600/yr/contractor
    "13":  "Depreciation (Sec 179 or MACRS)",
    "14":  "Employee benefit programs",
    "15":  "Insurance (other than health)",
    "16a": "Mortgage interest",
    "16b": "Other interest",
    "17":  "Legal and professional services",
    "18":  "Office expense",
    "19":  "Pension and profit-sharing plans",
    "20a": "Rent or lease — vehicles, machinery, equipment",
    "20b": "Rent or lease — other business property",
    "21":  "Repairs and maintenance",
    "22":  "Supplies",
    "23":  "Taxes and licenses",
    "24a": "Travel",
    "24b": "Meals (50% deductible)",
    "25":  "Utilities",
    "26":  "Wages",
    "27a": "Other expenses",
    "30":  "Home office (Form 8829 or simplified method)",
}


def category_name(line: str) -> str:
    return SCHEDULE_C.get(line, "Unknown")


def validate_category(line: str) -> bool:
    return line in SCHEDULE_C


# ─── Self-employment tax (Schedule SE) — 2025 ────────────────────────────────
SS_WAGE_BASE = 176_100          # 2025 Social Security wage base
SS_RATE = 0.124                 # 12.4% combined (employer + employee halves)
MEDICARE_RATE = 0.029           # 2.9% unlimited
ADDL_MEDICARE_RATE = 0.009      # 0.9% over threshold
ADDL_MEDICARE_THRESHOLD_SINGLE = 200_000
SE_INCOME_MULTIPLIER = 0.9235   # 92.35% of net SE income is the SE-tax base


def se_tax(net_se_income: float) -> float:
    if net_se_income <= 0:
        return 0.0
    base = net_se_income * SE_INCOME_MULTIPLIER
    ss = min(base, SS_WAGE_BASE) * SS_RATE
    medicare = base * MEDICARE_RATE
    addl = max(0.0, base - ADDL_MEDICARE_THRESHOLD_SINGLE) * ADDL_MEDICARE_RATE
    return round(ss + medicare + addl, 2)


# ─── Federal income tax — 2025 single filer ──────────────────────────────────
FED_BRACKETS_SINGLE = [
    (0,        11_925,  0.10),
    (11_925,   48_475,  0.12),
    (48_475,  103_350,  0.22),
    (103_350, 197_300,  0.24),
    (197_300, 250_525,  0.32),
    (250_525, 626_350,  0.35),
    (626_350, float("inf"), 0.37),
]
FED_STD_DEDUCTION_SINGLE = 15_000   # 2025

# QBI / Section 199A. Consulting is a Specified Service Trade or Business (SSTB),
# so the deduction phases out between $241,950 and $291,950 (single, 2025).
QBI_RATE = 0.20
QBI_SSTB_PHASEOUT_START_SINGLE = 241_950
QBI_SSTB_PHASEOUT_RANGE_SINGLE = 50_000


def federal_income_tax(taxable_income: float) -> float:
    if taxable_income <= 0:
        return 0.0
    tax = 0.0
    for lo, hi, rate in FED_BRACKETS_SINGLE:
        if taxable_income <= lo:
            break
        tax += (min(taxable_income, hi) - lo) * rate
    return round(tax, 2)


def qbi_deduction(net_business_income: float, taxable_before_qbi: float) -> float:
    """Section 199A QBI for an SSTB (consulting), single filer."""
    if net_business_income <= 0:
        return 0.0
    full = net_business_income * QBI_RATE
    if taxable_before_qbi <= QBI_SSTB_PHASEOUT_START_SINGLE:
        return round(min(full, taxable_before_qbi * QBI_RATE), 2)
    if taxable_before_qbi >= QBI_SSTB_PHASEOUT_START_SINGLE + QBI_SSTB_PHASEOUT_RANGE_SINGLE:
        return 0.0
    phaseout = (taxable_before_qbi - QBI_SSTB_PHASEOUT_START_SINGLE) / QBI_SSTB_PHASEOUT_RANGE_SINGLE
    return round(full * (1 - phaseout), 2)


# ─── California personal income tax — 2025 single ────────────────────────────
CA_BRACKETS_SINGLE = [
    (0,          10_756,  0.010),
    (10_756,     25_499,  0.020),
    (25_499,     40_245,  0.040),
    (40_245,     55_866,  0.060),
    (55_866,     70_606,  0.080),
    (70_606,    360_659,  0.093),
    (360_659,   432_787,  0.103),
    (432_787,   721_314,  0.113),
    (721_314, 1_000_000,  0.123),
    (1_000_000, float("inf"), 0.133),   # incl. 1% Mental Health Services tax
]
CA_STD_DEDUCTION_SINGLE = 5_540   # 2025


def ca_income_tax(taxable_income: float) -> float:
    if taxable_income <= 0:
        return 0.0
    tax = 0.0
    for lo, hi, rate in CA_BRACKETS_SINGLE:
        if taxable_income <= lo:
            break
        tax += (min(taxable_income, hi) - lo) * rate
    return round(tax, 2)


# ─── CA LLC franchise tax + gross-receipts fee (Form 568) ────────────────────
CA_LLC_MIN_FRANCHISE_TAX = 800   # annual flat, Form 3522

CA_LLC_FEE_BRACKETS = [
    (        0,    249_999,      0),
    (  250_000,    499_999,    900),
    (  500_000,    999_999,  2_500),
    (1_000_000,  4_999_999,  6_000),
    (5_000_000, float("inf"), 11_790),
]


def ca_llc_fee(gross_receipts: float) -> int:
    for lo, hi, fee in CA_LLC_FEE_BRACKETS:
        if lo <= gross_receipts <= hi:
            return fee
    return 0


# ─── Filing deadlines ────────────────────────────────────────────────────────
def deadlines_for_year(year: int, llc_formation_date: Optional[date] = None) -> list[tuple[date, str]]:
    """Sorted (date, description) for the given calendar year."""
    out: list[tuple[date, str]] = [
        (date(year,     1, 15), f"Q4 federal+CA estimated tax — for {year - 1} income"),
        (date(year,     1, 31), f"1099-NEC issuance — for contractors paid >$600 in {year - 1}"),
        (date(year,     4, 15), f"Federal 1040 + Schedule C + CA Form 540 — for {year - 1} tax year"),
        (date(year,     4, 15), f"CA Form 568 (LLC annual return) — for {year - 1} tax year"),
        (date(year,     4, 15), f"CA $800 LLC franchise tax (Form 3522) — for {year} tax year"),
        (date(year,     4, 15), f"Q1 federal+CA estimated tax — for {year} income"),
        (date(year,     6, 15), f"Q2 federal+CA estimated tax — for {year} income"),
        (date(year,     6, 15), f"CA LLC fee estimate (Form 3536) if {year} gross receipts > $250k"),
        (date(year,     9, 15), f"Q3 federal+CA estimated tax — for {year} income"),
    ]
    # First-year LLC: $800 franchise tax due by 15th day of 4th month of the first
    # tax year (Form 3522). For a calendar-year LLC formed mid-year, that's the
    # first April 15 after formation — covered by the standard line above. If the
    # LLC was formed in this calendar year, surface a one-time first-year reminder
    # for the Form 568 covering the short year.
    if llc_formation_date and llc_formation_date.year == year:
        out.append((
            date(year + 1, 4, 15),
            f"First Form 568 (covers {llc_formation_date.isoformat()} – {year}-12-31)",
        ))
        # SOI is due within 90 days of formation, then biennially.
        out.append((
            date(year + 2, llc_formation_date.month, llc_formation_date.day),
            "CA Statement of Information (Form LLC-12) — next biennial filing",
        ))
    return sorted(out)

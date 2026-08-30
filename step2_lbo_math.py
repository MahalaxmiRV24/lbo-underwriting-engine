"""
STEP 2: THE LBO MATH ENGINE
-----------------------------
This is the real heart of the whole project. Everything else (data
pipeline, front-end sliders) is just plumbing around THIS logic.

We're using realistic SAMPLE data here (shaped exactly like what
step1's get_company_financials() would return) so we can build and
test the math without needing live internet access. On your own
laptop, step1's real data plugs straight into this function.

------------------------------------------------------------------
THE STORY THIS CODE TELLS:
A PE firm wants to BUY a company using mostly borrowed money (debt),
run it for 5 years, then SELL it. Their profit comes from:
  1. Paying down debt with the company's cash flow (deleveraging)
  2. The company's EBITDA growing over the hold period
  3. Selling at a similar (or better) multiple than they paid

The two numbers a PE firm cares about most at the end:
  - IRR (Internal Rate of Return): the annualised % return on their
    invested equity
  - MOIC (Multiple on Invested Capital): "we put in $1, we got back
    $X" — simpler than IRR, PE people say this out loud constantly
------------------------------------------------------------------
"""

# ============================================================
# SAMPLE INPUT — shaped exactly like step1's real output would be
# ============================================================
sample_company = {
    "ticker": "SAMPLECO",
    "company_name": "Sample Mid-Market Co",
    "revenue": 500_000_000,       # $500M revenue
    "ebitda": 100_000_000,        # $100M EBITDA (20% margin — realistic for mid-market)
    "net_debt": 50_000_000,       # $50M existing debt on the balance sheet
}


def run_lbo_model(
    company: dict,
    entry_multiple: float = 10.0,      # Buy the company for 10x EBITDA
    exit_multiple: float = None,       # If None, assume same as entry (conservative)
    leverage_multiple: float = 4.5,    # Total new debt = 4.5x EBITDA
    senior_pct: float = 0.78,          # 78% of new debt is Senior (3.5x / 4.5x)
    senior_rate: float = 0.085,        # Senior debt interest rate (SOFR + 350bps ≈ 8.5%)
    mezz_rate: float = 0.12,           # Mezzanine (subordinated) debt rate — PIK, 12%
    ebitda_growth_rate: float = 0.06,  # Assume 6% EBITDA growth per year
    hold_years: int = 5,
):
    """
    Runs a simplified but genuinely correct LBO model.
    Returns a dictionary with the full year-by-year story plus final
    IRR and MOIC.
    """
    if exit_multiple is None:
        exit_multiple = entry_multiple  # conservative base case

    ebitda_entry = company["ebitda"]

    # ---------- STEP A: ENTRY — how much do we pay, how do we fund it? ----------
    enterprise_value_entry = ebitda_entry * entry_multiple

    new_debt = ebitda_entry * leverage_multiple
    senior_debt = new_debt * senior_pct
    mezz_debt = new_debt * (1 - senior_pct)

    # The PE firm's EQUITY CHEQUE is whatever the purchase price ISN'T covered by debt
    equity_investment = enterprise_value_entry - new_debt

    print(f"\n{'='*60}")
    print(f"ENTRY — Year 0")
    print(f"{'='*60}")
    print(f"  Entry EBITDA:              ${ebitda_entry:,.0f}")
    print(f"  Entry Multiple:            {entry_multiple}x")
    print(f"  --> Enterprise Value:      ${enterprise_value_entry:,.0f}")
    print(f"  Senior Debt (at {senior_pct*100:.0f}%):     ${senior_debt:,.0f}  @ {senior_rate*100:.1f}% interest")
    print(f"  Mezzanine Debt:            ${mezz_debt:,.0f}  @ {mezz_rate*100:.1f}% PIK interest")
    print(f"  --> Total New Debt:        ${new_debt:,.0f}  ({leverage_multiple}x EBITDA)")
    print(f"  --> PE Firm's Equity Cheque: ${equity_investment:,.0f}")
    print(f"  (This is the number the PE firm actually has to write a cheque for.)")

    # ---------- STEP B: THE HOLD PERIOD — pay down debt each year ----------
    # PIK (Payment-in-Kind) interest on mezz debt is NOT paid in cash —
    # it accrues and gets ADDED to the mezz debt balance instead.
    # Senior debt interest IS paid in cash, and remaining free cash flow
    # is used to pay down senior debt principal.

    current_senior = senior_debt
    current_mezz = mezz_debt
    current_ebitda = ebitda_entry

    print(f"\n{'='*60}")
    print(f"THE HOLD PERIOD — deleveraging year by year")
    print(f"{'='*60}")

    for year in range(1, hold_years + 1):
        current_ebitda = current_ebitda * (1 + ebitda_growth_rate)

        # Simplified assumption: ~50% of EBITDA converts to free cash flow
        # available for debt paydown (after capex, tax, working capital).
        # This is a standard mid-market planning assumption.
        free_cash_flow = current_ebitda * 0.50

        senior_interest_paid = current_senior * senior_rate
        cash_available_for_paydown = free_cash_flow - senior_interest_paid

        # Pay down senior debt with whatever cash is left (can't go below 0)
        paydown = min(cash_available_for_paydown, current_senior)
        current_senior -= paydown

        # Mezz debt: PIK interest just ACCRUES onto the balance (no cash paid)
        current_mezz *= (1 + mezz_rate)

        print(f"  Year {year}: EBITDA=${current_ebitda:,.0f}  |  "
              f"Senior Debt=${current_senior:,.0f}  |  "
              f"Mezz Debt=${current_mezz:,.0f}")

    # ---------- STEP C: EXIT — sell the company, pay off remaining debt ----------
    ebitda_exit = current_ebitda
    enterprise_value_exit = ebitda_exit * exit_multiple
    remaining_debt = current_senior + current_mezz

    # Equity value at exit = what's left after paying off remaining debt
    equity_value_exit = enterprise_value_exit - remaining_debt

    # ---------- STEP D: RETURNS — the two numbers PE people actually say out loud ----------
    moic = equity_value_exit / equity_investment
    irr = (moic ** (1 / hold_years)) - 1   # IRR formula: (MOIC)^(1/years) - 1

    print(f"\n{'='*60}")
    print(f"EXIT — Year {hold_years}")
    print(f"{'='*60}")
    print(f"  Exit EBITDA:               ${ebitda_exit:,.0f}")
    print(f"  Exit Multiple:             {exit_multiple}x")
    print(f"  --> Exit Enterprise Value: ${enterprise_value_exit:,.0f}")
    print(f"  Remaining Debt:            ${remaining_debt:,.0f}")
    print(f"  --> Equity Value at Exit:  ${equity_value_exit:,.0f}")
    print(f"\n  🎯 MOIC: {moic:.2f}x   (put in $1, got back ${moic:.2f})")
    print(f"  🎯 IRR:  {irr*100:.1f}%   (annualised return)")

    return {
        "equity_investment": equity_investment,
        "equity_value_exit": equity_value_exit,
        "moic": moic,
        "irr": irr,
    }


# --- Run it ---
if __name__ == "__main__":
    results = run_lbo_model(sample_company)

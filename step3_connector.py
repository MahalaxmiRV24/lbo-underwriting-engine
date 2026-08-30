"""
STEP 3: THE CONNECTOR
-----------------------
This is where it all comes together. You type a ticker, it fetches
REAL data, and runs the FULL LBO analysis on it.

This file imports the functions we already built and tested in
step1 and step2, and chains them together.
"""

from step1_data_pipeline import get_company_financials
from step2_lbo_math import run_lbo_model


def analyze_ticker(
    ticker: str,
    entry_multiple: float = 10.0,
    exit_multiple: float = None,
    leverage_multiple: float = 4.5,
    senior_pct: float = 0.78,
    senior_rate: float = 0.085,
    mezz_rate: float = 0.12,
    ebitda_growth_rate: float = 0.06,
    hold_years: int = 5,
):
    """
    The full pipeline: ticker in -> real data -> LBO analysis out.
    """
    print(f"\n{'#'*60}")
    print(f"#  ANALYZING: {ticker.upper()}")
    print(f"{'#'*60}")

    # STEP A: fetch real data using step1's function
    company_data = get_company_financials(ticker)

    if company_data is None:
        print(f"\nCould not analyze {ticker} — no data found. Try a different ticker.")
        return None

    if company_data["ebitda"] is None or company_data["ebitda"] <= 0:
        print(f"\n{ticker} has no valid EBITDA data — can't run an LBO on it.")
        print("(This can happen with early-stage, pre-profit companies.)")
        return None

    print(f"\nFound: {company_data['company_name']} ({company_data['ticker']})")
    print(f"  Revenue: ${company_data['revenue']:,.0f}" if company_data['revenue'] else "  Revenue: N/A")
    print(f"  EBITDA:  ${company_data['ebitda']:,.0f}")

    # STEP B: feed that real data into step2's LBO engine
    # Notice: run_lbo_model() expects a dict with an "ebitda" key —
    # company_data already has exactly that shape, so it plugs straight in.
    results = run_lbo_model(
        company=company_data,
        entry_multiple=entry_multiple,
        exit_multiple=exit_multiple,
        leverage_multiple=leverage_multiple,
        senior_pct=senior_pct,
        senior_rate=senior_rate,
        mezz_rate=mezz_rate,
        ebitda_growth_rate=ebitda_growth_rate,
        hold_years=hold_years,
    )

    return results


# --- Try it on a few real, US-listed tickers ---
if __name__ == "__main__":
    # CrowdStrike — we know this one works from step1's test
    analyze_ticker("CRWD")

    # Try a couple more — feel free to change these to any US ticker you like
    analyze_ticker("MSFT", entry_multiple=12.0, leverage_multiple=3.5)

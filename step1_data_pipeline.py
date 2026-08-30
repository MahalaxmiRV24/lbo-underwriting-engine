"""
STEP 1: DATA PIPELINE
----------------------
Goal: given ANY stock ticker, pull the real financial numbers we need
to run an LBO analysis on it.

What we actually need from the company's financials:
  - Revenue (most recent year)
  - EBITDA (Earnings Before Interest, Tax, Depreciation & Amortisation)
    -> this is the KEY number in an LBO. Debt is sized as a multiple
       of EBITDA (e.g. "4.5x EBITDA of debt"), and EBITDA is what
       services (pays down) that debt every year.
  - Net Debt (existing debt minus cash) -> tells us the "starting point"
    of the balance sheet before our new LBO debt gets layered on.
  - Shares outstanding & share price -> lets us calculate the company's
    current Enterprise Value, which becomes our "entry price".
"""

import yfinance as yf

def get_company_financials(ticker: str):
    """
    Pulls the core financial inputs needed for an LBO model.
    Returns a dictionary of clean numbers, or None if the ticker is invalid.
    """
    company = yf.Ticker(ticker)

    # .info gives us general company data: price, shares outstanding, etc.
    info = company.info

    # .financials gives us the income statement (Revenue, EBITDA, etc.)
    income_statement = company.financials

    # .balance_sheet gives us Debt and Cash
    balance_sheet = company.balance_sheet

    if income_statement.empty or balance_sheet.empty:
        print(f"Could not find financial data for '{ticker}'. Check the ticker is correct.")
        return None

    # Most recent year's data is always the FIRST column
    latest_income = income_statement.iloc[:, 0]
    latest_balance = balance_sheet.iloc[:, 0]

    # --- Extract Revenue ---
    revenue = latest_income.get("Total Revenue", None)

    # --- Extract or calculate EBITDA ---
    # Some companies report EBITDA directly. If not, we calculate it:
    # EBITDA = Operating Income + Depreciation & Amortisation
    ebitda = latest_income.get("EBITDA", None)
    if ebitda is None:
        operating_income = latest_income.get("Operating Income", 0)
        d_and_a = latest_income.get("Reconciled Depreciation", 0)
        ebitda = operating_income + d_and_a

    # --- Extract Net Debt ---
    total_debt = latest_balance.get("Total Debt", 0)
    cash = latest_balance.get("Cash And Cash Equivalents", 0)
    net_debt = total_debt - cash

    # --- Current market data (for entry valuation reference) ---
    share_price = info.get("currentPrice", None)
    shares_outstanding = info.get("sharesOutstanding", None)
    market_cap = info.get("marketCap", None)

    result = {
        "ticker": ticker.upper(),
        "company_name": info.get("shortName", ticker),
        "revenue": revenue,
        "ebitda": ebitda,
        "net_debt": net_debt,
        "share_price": share_price,
        "shares_outstanding": shares_outstanding,
        "market_cap": market_cap,
    }

    return result


# --- Let's test it on a real company ---
if __name__ == "__main__":
    test_ticker = "XRO"  # Xero — but note: Xero trades on the ASX, not always
                          # well covered by yfinance. Let's also try a US name.
    print(f"\nFetching data for {test_ticker}...")
    data = get_company_financials(test_ticker)
    if data:
        for key, value in data.items():
            print(f"  {key}: {value}")

    print("\n" + "="*50)
    test_ticker_2 = "CRWD"  # CrowdStrike — US-listed, should have clean data
    print(f"\nFetching data for {test_ticker_2}...")
    data2 = get_company_financials(test_ticker_2)
    if data2:
        for key, value in data2.items():
            print(f"  {key}: {value}")

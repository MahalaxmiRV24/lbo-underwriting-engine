"""
STEP 4: THE STREAMLIT INTERFACE
----------------------------------
This wraps everything we've built (step1 + step2 + step3) into a
real, clickable web app. Streamlit turns Python code into a website
using very little extra code — no HTML/CSS/JavaScript needed.

Run this with:  streamlit run step4_app.py
(NOT "python3 step4_app.py" — Streamlit apps are launched differently)
"""

import streamlit as st
from step1_data_pipeline import get_company_financials
from step2_lbo_math import run_lbo_model


def format_money(value):
    """Formats a large number as a short, readable string like $4.4B or $850M."""
    if value is None:
        return "N/A"
    abs_value = abs(value)
    sign = "-" if value < 0 else ""
    if abs_value >= 1_000_000_000:
        return f"{sign}${abs_value / 1_000_000_000:.1f}B"
    elif abs_value >= 1_000_000:
        return f"{sign}${abs_value / 1_000_000:.1f}M"
    elif abs_value >= 1_000:
        return f"{sign}${abs_value / 1_000:.1f}K"
    else:
        return f"{sign}${abs_value:,.0f}"

# ============================================================
# PAGE SETUP
# ============================================================
st.set_page_config(page_title="LBO Underwriting Engine", page_icon="📊", layout="wide")

st.title("📊 Proprietary LBO Underwriting Engine")
st.caption("Type any **US-listed** stock ticker and run a full institutional-style LBO analysis on its real, live financials.")
st.caption("⚠️ Data source coverage is strongest for US exchanges (NYSE/NASDAQ). ASX and other international tickers are often unavailable via this free data source.")

# ============================================================
# SIDEBAR — this is where the interactive sliders live
# ============================================================
st.sidebar.header("LBO Assumptions")

ticker_input = st.sidebar.text_input("Ticker (e.g. CRWD, MSFT, AAPL)", value="CRWD")

entry_multiple = st.sidebar.slider(
    "Entry Multiple (x EBITDA)", min_value=5.0, max_value=20.0, value=10.0, step=0.5
)
exit_multiple = st.sidebar.slider(
    "Exit Multiple (x EBITDA)", min_value=5.0, max_value=20.0, value=entry_multiple, step=0.5
)
leverage_multiple = st.sidebar.slider(
    "Leverage (x EBITDA of new debt)", min_value=0.0, max_value=7.0, value=4.5, step=0.5
)
senior_pct = st.sidebar.slider(
    "Senior Debt % of Total Debt", min_value=0.0, max_value=1.0, value=0.78, step=0.01
)
senior_rate = st.sidebar.slider(
    "Senior Debt Interest Rate", min_value=0.03, max_value=0.15, value=0.085, step=0.005, format="%.3f"
)
mezz_rate = st.sidebar.slider(
    "Mezzanine (PIK) Rate", min_value=0.05, max_value=0.20, value=0.12, step=0.005, format="%.3f"
)
ebitda_growth_rate = st.sidebar.slider(
    "Annual EBITDA Growth Rate", min_value=0.0, max_value=0.30, value=0.06, step=0.01, format="%.2f"
)
hold_years = st.sidebar.slider("Hold Period (years)", min_value=1, max_value=10, value=5)

run_button = st.sidebar.button("Run LBO Analysis", type="primary")

# ============================================================
# MAIN PANEL — this is where results get displayed
# ============================================================
if run_button:
    with st.spinner(f"Fetching live data for {ticker_input.upper()}..."):
        company_data = get_company_financials(ticker_input)

    if company_data is None:
        st.error(f"Could not find data for '{ticker_input}'. This tool currently only supports **US-listed** tickers (NYSE/NASDAQ) — ASX and other international exchanges are not well covered by this free data source. Try a US ticker like AAPL, MSFT, or CRWD.")
    elif company_data["ebitda"] is None or company_data["ebitda"] <= 0:
        st.error(f"{ticker_input.upper()} has no valid EBITDA data — likely a pre-profit company. Try a different ticker.")
    else:
        st.success(f"Found: {company_data['company_name']} ({company_data['ticker']})")

        col1, col2, col3 = st.columns(3)
        col1.metric("Revenue", format_money(company_data['revenue']))
        col2.metric("EBITDA", format_money(company_data['ebitda']))
        col3.metric("Current Market Cap", format_money(company_data['market_cap']))

        st.divider()

        # Run the LBO math (same function from step2, unchanged)
        equity_investment = company_data["ebitda"] * entry_multiple - (company_data["ebitda"] * leverage_multiple)

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

        st.subheader("Returns")
        rcol1, rcol2, rcol3 = st.columns(3)
        rcol1.metric("Equity Cheque", format_money(results['equity_investment']))
        rcol2.metric("MOIC", f"{results['moic']:.2f}x")
        rcol3.metric("IRR", f"{results['irr']*100:.1f}%")

        st.caption("Note: this is a simplified educational model. Real institutional LBOs "
                   "account for additional factors including transaction fees, working "
                   "capital adjustments, management rollover equity, and tax structuring.")
else:
    st.info("👈 Set your assumptions in the sidebar and click **Run LBO Analysis** to get started.")

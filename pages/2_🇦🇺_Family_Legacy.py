import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from datetime import date, timedelta

st.set_page_config(page_title="Family Bitcoin Office", layout="wide", page_icon="🇦🇺")

# --- POWER LAW HELPERS ---
GENESIS_DATE = date(2009, 1, 3)
PL_SD_LOG = 0.35  # Standard deviation in log10 space

def get_power_law_price(days_since_genesis, aud_usd=0.65):
    """Calculate median power law price in AUD"""
    return ((10**-17) * (days_since_genesis**5.82)) / aud_usd

def sd_to_multiplier(sd):
    """Convert standard deviations to price multiplier"""
    return 10 ** (sd * PL_SD_LOG)

def price_to_sd(current_price, median_price):
    """Calculate how many SDs above/below median"""
    if median_price <= 0 or current_price <= 0:
        return 0
    return np.log10(current_price / median_price) / PL_SD_LOG

def get_sd_label(sd):
    """Get human-readable label for SD value"""
    if sd <= -1.5: return "Very Conservative"
    elif sd <= -0.5: return "Conservative"
    elif sd <= 0.5: return "Median"
    elif sd <= 1.5: return "Optimistic"
    else: return "Very Optimistic"

# --- 🧠 STATE MANAGER ---
defaults = {
    "shared_btc_price": 150000.0,
    "shared_use_live": True,
    "shared_inflation": 0.03,
    "shared_pl_scenario": 0.0,
    "legacy_btc_holdings": 10.0,
    "legacy_parents_spend": 120000.0,
    "legacy_kid_allowance": 60000.0,
    "legacy_tax_rate": 0.23,
    "legacy_safe_withdraw": 25
}
for key, val in defaults.items():
    if key not in st.session_state: st.session_state[key] = val

st.title(f"🇦🇺 Family Bitcoin Office")

st.sidebar.header("1. The Asset")
use_live_price = st.sidebar.toggle("🔗 Sync to Market Price", key="shared_use_live")
if use_live_price:
    try:
        btc_ticker = yf.Ticker("BTC-AUD")
        live_val = btc_ticker.history(period="1d")['Close'].iloc[-1]
        st.session_state.shared_btc_price = float(live_val)
        st.sidebar.caption("✅ Data Stream Active")
    except: st.sidebar.error("Connection Failed.")

start_price = st.sidebar.number_input(
    "BTC Start Price (AUD)", min_value=10000.0, max_value=5000000.0,
    disabled=use_live_price, step=1000.0, key="shared_btc_price"
)

initial_btc = st.sidebar.number_input("Total BTC Holdings", step=0.1, key="legacy_btc_holdings")

st.sidebar.header("2. Family Lifestyle")
parents_spend = st.sidebar.number_input("Parents Annual Spend ($)", step=10000, key="legacy_parents_spend")
num_kids = st.sidebar.slider("Number of Kids", 1, 6, 3, key="legacy_num_kids")
kids_start_year = st.sidebar.slider("Kids Start Allowance (Years from now)", 1, 30, 15, key="legacy_kids_start")
kid_allowance = st.sidebar.number_input("Annual Allowance Per Kid ($)", step=5000, key="legacy_kid_allowance")

st.sidebar.header("3. Macro & Tax")
inflation = st.sidebar.slider("Inflation Rate (%)", 0, 10, 3, 1, key="shared_inflation") / 100
tax_rate = st.sidebar.slider("Tax on Sell (%)", 0, 47, 23, key="legacy_tax_rate") / 100
safe_withdraw_rate = st.sidebar.slider("Safety Ratio (Years of Spend)", 10, 50, 25, key="legacy_safe_withdraw")

st.divider()
col_model, col_events = st.columns([1, 1])

with col_model:
    st.subheader("📈 Projection Model")
    model_mode = st.radio("Select Growth Engine:", ["Power Law Formula", "Manual Cycles (Custom %)"], horizontal=True, key="legacy_model_mode")

    if model_mode == "Manual Cycles (Custom %)":
        st.info("Define specific growth rates for each year manually.")
        with st.expander("Configure Cycle", expanded=True):
            years = 50
            default_data = [{"Year": y, "Growth %": 60 if y==1 else 15 if y==2 else -30 if y==3 else 10 if y==4 else 12 if y<=10 else 7} for y in range(1, years + 1)]
            df_growth_input = pd.DataFrame(default_data)
            edited_growth = st.data_editor(df_growth_input, height=200, width="stretch", hide_index=True, column_config={"Year": st.column_config.NumberColumn(disabled=True)}, key="legacy_growth_editor")

    else:
        st.info("🧮 **Formula:** $Price = 10^{-17} \\times days^{5.82}$")
        aud_usd = st.slider("AUD/USD Exchange Rate", 0.50, 1.0, 0.65, 0.01, key="legacy_fx")

        today = date.today()
        days_today = (today - GENESIS_DATE).days
        median_price = get_power_law_price(days_today, aud_usd)
        current_sd = price_to_sd(start_price, median_price)

        st.caption(f"📍 Current: **{current_sd:+.2f} SD** ({get_sd_label(current_sd)}) | Median: ${median_price:,.0f}")

        pl_scenario = st.slider(
            "Projection Scenario (Standard Deviations)",
            min_value=-2.0, max_value=2.0, step=0.25,
            key="shared_pl_scenario",
            help="Project future prices along a specific band of the Power Law. 0 = Median, negative = conservative, positive = optimistic"
        )
        scenario_label = get_sd_label(pl_scenario)
        multiplier = sd_to_multiplier(pl_scenario)
        st.caption(f"📈 Projecting along: **{pl_scenario:+.2f} SD** ({scenario_label}) = {multiplier:.2f}x median")

with col_events:
    st.subheader("🎁 Bank of Mum & Dad")
    st.caption("One-off cash events (e.g., House Deposits)")
    with st.expander("Edit Events Register", expanded=True):
        event_data = [{"Year": 10, "Amount": 200000}, {"Year": 12, "Amount": 200000}]
        df_events_input = pd.DataFrame(event_data)
        edited_events = st.data_editor(df_events_input, num_rows="dynamic", height=200, width="stretch", hide_index=True, column_config={"Year": st.column_config.NumberColumn(min_value=1, max_value=50), "Amount": st.column_config.NumberColumn(format="$%d")}, key="legacy_events")

# --- CALCULATION ENGINE ---
events_lookup = {}
if not edited_events.empty: events_lookup = edited_events.groupby('Year')['Amount'].sum().to_dict()

today = date.today()
start_days = (today - GENESIS_DATE).days
history = []; curr_btc = initial_btc; curr_price = start_price; status = "Sustainable"; fail_year = None; years = 50; fi_year = "Not in 50 Years"; fi_found = False

history.append({"Year": 0, "BTC": curr_btc, "Modeled Price": curr_price, "Value": curr_btc*curr_price, "Parent Cost": 0, "Kids Cost": 0, "Lump Sums": 0, "Tax Paid": 0, "Total Drawdown": 0, "FI Target": (parents_spend) * safe_withdraw_rate, "Status": "Sustainable"})

for y in range(1, years + 1):
    if model_mode == "Manual Cycles (Custom %)":
        try: g = edited_growth.loc[edited_growth['Year'] == y, 'Growth %'].values[0] / 100
        except: g = 0.05
        prev_price = history[-1]['Modeled Price']; curr_price = prev_price * (1 + g)
    else:
        future_days = start_days + (y * 365)
        median_future = get_power_law_price(future_days, aud_usd)
        curr_price = median_future * sd_to_multiplier(pl_scenario)

    idx_rate = (1 + inflation) ** y
    cost_parents = parents_spend * idx_rate
    cost_kids = (kid_allowance * num_kids * idx_rate) if y >= kids_start_year else 0
    cost_lump = events_lookup.get(y, 0) * idx_rate
    total_net_needed = cost_parents + cost_kids + cost_lump

    gross_sell = total_net_needed / (1 - tax_rate) if tax_rate < 1.0 else total_net_needed
    tax_paid = gross_sell - total_net_needed
    btc_sold = gross_sell / curr_price; curr_btc -= btc_sold

    if curr_btc < 0: curr_btc = 0; status = "Failed"; fail_year = y if status == "Sustainable" else fail_year
    fi_target = total_net_needed * safe_withdraw_rate; portfolio_val = curr_btc * curr_price
    if not fi_found and portfolio_val >= fi_target and status == "Sustainable": fi_year = y; fi_found = True

    history.append({"Year": y, "BTC": curr_btc, "Modeled Price": curr_price, "Value": portfolio_val, "Parent Cost": cost_parents, "Kids Cost": cost_kids, "Lump Sums": cost_lump, "Tax Paid": tax_paid, "Total Drawdown": total_net_needed, "FI Target": fi_target, "Status": status})

df = pd.DataFrame(history)

st.divider()
fail_rows = df[df['Status'] == "Failed"]; has_failed = not fail_rows.empty
m1, m2, m3, m4 = st.columns(4)
if not has_failed:
    m1.metric("Feasibility", "✅ Infinite"); final_val = df.iloc[-1]['Value']
    m2.metric(f"Value at Year {years}", f"${final_val/1_000_000:,.1f}M"); m3.metric("Final BTC Stack", f"{df.iloc[-1]['BTC']:,.2f}", delta=f"{df.iloc[-1]['BTC']-initial_btc:,.2f}")
else:
    m1.metric("Feasibility", f"❌ Broke Year {fail_rows.iloc[0]['Year']}", delta_color="inverse"); m2.metric("Portfolio Value", "$0"); m3.metric("Final BTC Stack", "0.00")
if isinstance(fi_year, int): m4.metric("Safe Solvency Reached", f"Year {fi_year}", delta="Financial Independence")
else: m4.metric("Safe Solvency", "Never", delta="High Risk", delta_color="inverse")

tab1, tab2 = st.tabs(["📊 Visual Analysis", "📋 Data Ledger"])
with tab1:
    col_main, col_burn = st.columns([2, 1])
    with col_main:
        fig_asset = go.Figure()
        fig_asset.add_trace(go.Scatter(x=df['Year'], y=df['Value'], name="Portfolio Value (AUD)", fill='tozeroy', line=dict(color="#00CC96"), yaxis="y1"))
        fig_asset.add_trace(go.Scatter(x=df['Year'], y=df['FI Target'], name=f"Safety Target", line=dict(color="#FFD700", width=2, dash='dash'), yaxis="y1"))
        fig_asset.add_trace(go.Scatter(x=df['Year'], y=df['BTC'], name="BTC Holdings", line=dict(color="#F7931A", width=3, dash='dot'), yaxis="y2"))
        fig_asset.update_layout(title="Solvency Check", yaxis=dict(title="AUD Value"), yaxis2=dict(title="BTC Count", overlaying="y", side="right"), height=450)
        st.plotly_chart(fig_asset, width="stretch")
    with col_burn:
        fig_spend = go.Figure()
        fig_spend.add_trace(go.Scatter(x=df['Year'], y=df['Parent Cost'], stackgroup='one', name="Parents", line=dict(width=0, color='#636EFA')))
        fig_spend.add_trace(go.Scatter(x=df['Year'], y=df['Kids Cost'], stackgroup='one', name="Kids", line=dict(width=0, color='#EF553B')))
        fig_spend.add_trace(go.Scatter(x=df['Year'], y=df['Lump Sums'], stackgroup='one', name="One-Offs", line=dict(width=0, color='#FECB52')))
        fig_spend.add_trace(go.Scatter(x=df['Year'], y=df['Tax Paid'], stackgroup='one', name="Tax", line=dict(width=0, color='#A9A9A9')))
        fig_spend.update_layout(title="Cash Flow Drain", height=450); st.plotly_chart(fig_spend, width="stretch")

with tab2:
    st.markdown("##### Detailed Simulation Ledger")
    st.dataframe(df[['Year', 'BTC', 'Modeled Price', 'Value', 'Total Drawdown', 'Lump Sums', 'Tax Paid']].style.format({"BTC": "{:,.4f}", "Modeled Price": "${:,.0f}", "Value": "${:,.0f}", "Total Drawdown": "${:,.0f}", "Lump Sums": "${:,.0f}", "Tax Paid": "${:,.0f}"}), width="stretch")

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
from datetime import date

st.set_page_config(page_title="Wealth Accelerator", layout="wide", page_icon="🚀")

# --- 🧠 STATE MANAGER ---
defaults = {
    "shared_btc_price": 150000.0,
    "shared_use_live": True,
    "wa_lump_sum": 5000,
    "wa_dca_amt": 250
}
for key, val in defaults.items():
    if key not in st.session_state: st.session_state[key] = val

st.title("🚀 Wealth Accelerator")

st.sidebar.header("1. Starting Point")
# SHARED TOGGLE & INPUT
use_live_price = st.sidebar.toggle("🔗 Live BTC Price", key="shared_use_live")
if use_live_price:
    try:
        btc_ticker = yf.Ticker("BTC-AUD"); live_val = btc_ticker.history(period="1d")['Close'].iloc[-1]
        st.session_state.shared_btc_price = float(live_val); st.sidebar.caption("✅ Data Stream Active")
    except: st.sidebar.error("Connection Failed.")

start_price = st.sidebar.number_input(
    "Current BTC Price (AUD)", min_value=10000.0, max_value=5000000.0,
    disabled=use_live_price, step=1000.0, key="shared_btc_price"
)

st.sidebar.header("2. The Strategy")
initial_lump_sum = st.sidebar.number_input("Initial Lump Sum Investment ($)", step=1000, key="wa_lump_sum")
dca_amount = st.sidebar.number_input("Regular Investment Amount ($)", step=50, key="wa_dca_amt")
dca_freq = st.sidebar.selectbox("Frequency", ["Weekly", "Fortnightly", "Monthly"], key="wa_freq")

if dca_freq == "Weekly": annual_contrib = dca_amount * 52
elif dca_freq == "Fortnightly": annual_contrib = dca_amount * 26
else: annual_contrib = dca_amount * 12
st.sidebar.success(f"**Annual Injection:** ${annual_contrib:,.0f}")

col_model, col_summary = st.columns([1, 2])
with col_model:
    st.subheader("📈 Growth Engine")
    model_mode = st.radio("Select Prediction Model:", ["Power Law Formula", "Manual Cycles"], horizontal=True, key="wa_model")
    years_to_model = st.slider("Years to Accumulate", 5, 30, 15, key="wa_years")

    if model_mode == "Manual Cycles":
        with st.expander("Configure Growth Rates", expanded=True):
            years = 50; default_data = [{"Year": y, "Growth %": 50 if y==1 else 15 if y==2 else -20 if y==3 else 12 if y<=10 else 7} for y in range(1, years + 1)]
            df_growth_input = pd.DataFrame(default_data)
            edited_growth = st.data_editor(df_growth_input, height=200, use_container_width=True, hide_index=True, column_config={"Year": st.column_config.NumberColumn(disabled=True)}, key="wa_growth_editor")
    else:
        st.info("Using Power Law (Anchored)")
        genesis_date = date(2009, 1, 3); today = date.today(); days_today = (today - genesis_date).days
        raw_pl_aud = ((10**-17) * (days_today**5.82)) / 0.65; anchor_ratio = start_price / raw_pl_aud
        st.caption(f"Anchored Premium: {anchor_ratio:.2f}x")

history = []; btc_stack = initial_lump_sum / start_price; total_invested_cash = initial_lump_sum; curr_price = start_price; start_days = (today - genesis_date).days
history.append({"Year": 0, "BTC Price": start_price, "BTC Stack": btc_stack, "Total Invested": total_invested_cash, "Portfolio Value": btc_stack * start_price, "ROI (x)": 1.0})

for y in range(1, years_to_model + 1):
    prev_price = curr_price
    if model_mode == "Manual Cycles":
        try: g = edited_growth.loc[edited_growth['Year'] == y, 'Growth %'].values[0] / 100
        except: g = 0.05
        curr_price = curr_price * (1 + g)
    else:
        future_days = start_days + (y * 365); curr_price = (((10**-17) * (future_days**5.82)) / 0.65) * anchor_ratio

    avg_price_of_year = (prev_price + curr_price) / 2
    btc_purchased = annual_contrib / avg_price_of_year; btc_stack += btc_purchased; total_invested_cash += annual_contrib
    portfolio_val = btc_stack * curr_price; roi = portfolio_val / total_invested_cash if total_invested_cash > 0 else 0
    history.append({"Year": y, "BTC Price": curr_price, "BTC Stack": btc_stack, "Total Invested": total_invested_cash, "Portfolio Value": portfolio_val, "ROI (x)": roi})

df = pd.DataFrame(history)

with col_summary:
    final_val = df.iloc[-1]['Portfolio Value']; final_invested = df.iloc[-1]['Total Invested']; final_roi = df.iloc[-1]['ROI (x)']; final_btc = df.iloc[-1]['BTC Stack']
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Cash Invested", f"${final_invested:,.0f}"); m2.metric("Portfolio Value", f"${final_val:,.0f}", delta="Tax Free (Hold)"); m3.metric("Bitcoin Accumulated", f"{final_btc:,.4f} BTC")
    st.divider()
    st.markdown(f"""<div style="text-align: center; padding: 10px; background-color: #262730; border-radius: 10px; border: 1px solid #444;"><p style="margin:0; color: #aaa;">Your Capital Multiplier</p><p class="big-roi">{final_roi:.2f}x</p><p style="margin:0; font-size: 0.9rem;">Every $1 invested turns into ${final_roi:.2f}</p></div><br>""", unsafe_allow_html=True)

tab_chart, tab_data = st.tabs(["📊 Visual Growth", "📋 Data Ledger"])
with tab_chart:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Year'], y=df['Total Invested'], mode='lines', name='Cash Invested', line=dict(color='#A9A9A9', width=2, dash='dash'), fill='tozeroy', fillcolor='rgba(169, 169, 169, 0.1)'))
    fig.add_trace(go.Scatter(x=df['Year'], y=df['Portfolio Value'], mode='lines', name='Portfolio Value', line=dict(color='#F7931A', width=4), fill='tonexty', fillcolor='rgba(247, 147, 26, 0.2)'))
    fig.update_layout(title="The Bitcoin Effect", yaxis_title="Value (AUD)", height=500, hovermode="x unified"); st.plotly_chart(fig, use_container_width=True)
with tab_data:
    st.dataframe(df.style.format({"BTC Price": "${:,.0f}", "BTC Stack": "{:,.4f}", "Total Invested": "${:,.0f}", "Portfolio Value": "${:,.0f}", "ROI (x)": "{:.2f}x"}), use_container_width=True)

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
from datetime import date

st.set_page_config(page_title="Personal Finance HQ", layout="wide", page_icon="💰")

# --- 🧠 STATE MANAGER ---
defaults = {
    "shared_btc_price": 150000.0,
    "shared_use_live": True,
    "shared_inflation": 0.03,
    "pf_cash_interest": 0.04,
    "pf_salary": 180000.0,
    "pf_btc_qty": 5.0,
    "pf_cash_aud": 50000.0,
    "pf_e1": 40000, "pf_e2": 15000, "pf_e3": 5000, "pf_e4": 4000, "pf_e5": 2000,
    "pf_e6": 3000, "pf_e7": 2000, "pf_e8": 10000, "pf_e9": 5000, "pf_e10": 5000
}
for key, val in defaults.items():
    if key not in st.session_state: st.session_state[key] = val

st.title("💰 Personal Wealth Command")

# --- SIDEBAR ---
st.sidebar.header("1. Global Settings")
use_live_price = st.sidebar.toggle("🔗 Live BTC Price", key="shared_use_live")

if use_live_price:
    try:
        btc_ticker = yf.Ticker("BTC-AUD")
        live_val = btc_ticker.history(period="1d")['Close'].iloc[-1]
        st.session_state.shared_btc_price = float(live_val)
        st.sidebar.caption("✅ Data Stream Active")
    except:
        st.sidebar.error("Connection Failed.")

btc_price = st.sidebar.number_input(
    "BTC Price (AUD)", min_value=10000.0, max_value=5000000.0,
    disabled=use_live_price, step=1000.0, key="shared_btc_price"
)

st.sidebar.header("2. Macro Rates")
cash_interest = st.sidebar.slider("Cash Interest Rate (%)", 0.0, 10.0, 4.0, 0.5, key="pf_cash_interest") / 100
inflation_rate = st.sidebar.slider("Inflation Rate (%)", 0.0, 10.0, 3.0, 0.5, key="shared_inflation") / 100

# --- TABS ---
tab_assets, tab_budget, tab_runway = st.tabs(["🏦 Net Worth", "💳 Budget & Savings", "🚀 Future Runway"])

with tab_assets:
    st.subheader("📋 Current Position")
    col_inputs, col_summary = st.columns([1, 2])
    with col_inputs:
        with st.expander("📝 Edit Holdings", expanded=True):
            btc_qty = st.number_input("Bitcoin Holdings (BTC)", step=0.1, format="%.4f", key="pf_btc_qty")
            cash_aud = st.number_input("Cash / Liquidity (AUD)", step=1000.0, format="%f", key="pf_cash_aud")
            btc_val = btc_qty * btc_price
            total_nw = btc_val + cash_aud

    with col_summary:
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Net Worth", f"${total_nw:,.0f}")
        m2.metric("Bitcoin Value", f"${btc_val:,.0f}", delta=f"{btc_qty} BTC")
        m3.metric("Cash Position", f"${cash_aud:,.0f}")
        st.divider()
        chart_data = pd.DataFrame([{"Asset": "Bitcoin", "Value": btc_val}, {"Asset": "Cash", "Value": cash_aud}])
        fig_pie = px.pie(chart_data, values='Value', names='Asset', title="Asset Allocation", color='Asset', color_discrete_map={'Bitcoin':'#F7931A', 'Cash':'#00CC96'}, hole=0.4)
        fig_pie.update_layout(height=350)
        st.plotly_chart(fig_pie, use_container_width=True)

with tab_budget:
    st.subheader("💳 Annual Cash Flow Engine")
    col_inc, col_exp_list, col_res = st.columns([1, 1.5, 1])

    with col_inc:
        st.info("💰 **Income**")
        salary = st.number_input("Total Annual Income ($)", step=5000, key="pf_salary")

    with col_exp_list:
        st.error("💸 **Expenses Breakdown**")
        with st.expander("Detailed Expense Input", expanded=True):
            e1 = st.number_input("Mortgage / Rent", step=1000, key="pf_e1")
            e2 = st.number_input("Food & Groceries", step=500, key="pf_e2")
            e3 = st.number_input("Car / Transport / Fuel", step=500, key="pf_e3")
            e4 = st.number_input("Insurance", step=500, key="pf_e4")
            e5 = st.number_input("Clothes & Gear", step=500, key="pf_e5")
            e6 = st.number_input("Bikes / Hobbies", step=500, key="pf_e6")
            e7 = st.number_input("Computers / Tech", step=500, key="pf_e7")
            e8 = st.number_input("Holidays / Travel", step=1000, key="pf_e8")
            e9 = st.number_input("Wine / Dining Out", step=500, key="pf_e9")
            e10 = st.number_input("One-off / Buffer", step=1000, key="pf_e10")
            living = e1 + e2 + e3 + e4 + e5 + e6 + e7 + e8 + e9 + e10

    with col_res:
        st.success("🏦 **Savings Result**")
        annual_savings = salary - living
        savings_rate = (annual_savings / salary) * 100 if salary > 0 else 0
        st.metric("Total Expenses", f"${living:,.0f}")
        st.metric("Investable Cash / Year", f"${annual_savings:,.0f}", delta="Net Savings")
        st.metric("Savings Rate", f"{savings_rate:.1f}%")

with tab_runway:
    st.subheader("🚀 Wealth Projection Engine")
    col_mode, col_chart = st.columns([1, 2])
    with col_mode:
        st.write("**Bitcoin Growth Model**")
        model_mode = st.radio("Choose Strategy:", ["Power Law Formula", "Manual Cycles"], horizontal=True, key="pf_model_mode")
        years_to_model = st.slider("Years to Project", 5, 40, 20, key="pf_years")

        if model_mode == "Manual Cycles":
            with st.expander("Configure Growth Rates", expanded=True):
                years = 50
                default_data = [{"Year": y, "Growth %": 50 if y==1 else 15 if y==2 else -20 if y==3 else 12 if y<=10 else 7} for y in range(1, years + 1)]
                df_growth_input = pd.DataFrame(default_data)
                edited_growth = st.data_editor(df_growth_input, height=200, use_container_width=True, hide_index=True, column_config={"Year": st.column_config.NumberColumn(disabled=True)}, key="pf_growth_editor")
        else:
            st.info("Using Power Law (Anchored)")
            genesis_date = date(2009, 1, 3); today = date.today(); days_today = (today - genesis_date).days
            raw_pl_aud = ((10**-17) * (days_today**5.82)) / 0.65
            anchor_ratio = btc_price / raw_pl_aud
            st.caption(f"Anchored Premium: {anchor_ratio:.2f}x")

    history = []
    curr_btc_price = btc_price
    curr_cash = cash_aud
    history.append({"Year": date.today().year, "BTC Price": btc_price, "Total Net Worth": total_nw, "Bitcoin Value": btc_val, "Cash/Savings": cash_aud})
    start_days = (today - genesis_date).days

    for y in range(1, years_to_model + 1):
        if model_mode == "Manual Cycles":
            try: g = edited_growth.loc[edited_growth['Year'] == y, 'Growth %'].values[0] / 100
            except: g = 0.05
            curr_btc_price = curr_btc_price * (1 + g)
        else:
            future_days = start_days + (y * 365)
            curr_btc_price = (((10**-17) * (future_days**5.82)) / 0.65) * anchor_ratio

        curr_cash = curr_cash * (1 + cash_interest)
        curr_cash += annual_savings * ((1 + inflation_rate) ** y)
        btc_holding_val = btc_qty * curr_btc_price
        total_loop_nw = btc_holding_val + curr_cash
        history.append({"Year": date.today().year + y, "BTC Price": curr_btc_price, "Total Net Worth": total_loop_nw, "Bitcoin Value": btc_holding_val, "Cash/Savings": curr_cash})

    df_res = pd.DataFrame(history)
    with col_chart:
        fig = px.area(df_res, x="Year", y=["Cash/Savings", "Bitcoin Value"], title="Projected Net Worth Breakdown", labels={"value": "Value (AUD)", "variable": "Asset Class"}, color_discrete_map={"Bitcoin Value": "#F7931A", "Cash/Savings": "#00CC96"})
        fig.update_layout(height=450)
        st.plotly_chart(fig, use_container_width=True)
        final_nw = df_res.iloc[-1]['Total Net Worth']
        st.success(f"Projected Net Worth in {years_to_model} Years: **${final_nw/1_000_000:,.1f} Million**")

    st.divider()
    st.subheader("📋 Detailed Projection Ledger")
    st.dataframe(df_res[["Year", "BTC Price", "Bitcoin Value", "Cash/Savings", "Total Net Worth"]].style.format({"Total Net Worth": "${:,.0f}", "Bitcoin Value": "${:,.0f}", "Cash/Savings": "${:,.0f}", "BTC Price": "${:,.0f}"}), use_container_width=True)

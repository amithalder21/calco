import streamlit as st

st.set_page_config(page_title="Equity Profit/Loss Calculator", layout="wide")

st.title("Equity Profit/Loss Calculator")
st.caption("Equity charges based on values visible in your left dashboard. Tax is an estimate.")

# -----------------------------
# DEFAULT CONSTANTS (EDITABLE)
# -----------------------------
DEFAULTS = {
    "BROKERAGE_RATE": 0.001,      # 0.1%
    "BROKERAGE_CAP": 20.0,        # max per order
    "GST_RATE": 0.18,
    "IPFT_FIXED": 2.0,
    "DP_CHARGE": 15.93,

    # STT
    "STT_INTRADAY_SELL": 0.00025,    # 0.025%
    "STT_DELIVERY_BUY": 0.001,       # 0.1%
    "STT_DELIVERY_SELL": 0.001,      # 0.1%

    # Stamp duty
    "STAMP_INTRADAY_BUY": 0.00003,   # 0.003%
    "STAMP_DELIVERY_BUY": 0.00015,   # 0.015%

    # Exchange transaction charges
    "EXCH_NSE": 0.0000297,           # 0.00297%
    "EXCH_BSE": 0.0000375,           # 0.00375%

    # SEBI charges
    "SEBI_CHARGE": 0.000001,         # 0.0001%

    # MTF Interest
    "MTF_INTEREST_RATE": 0.1495      # 14.95% p.a.
}

st.sidebar.header("Edit Charges (Optional)")
const = {k: st.sidebar.number_input(k, value=float(v), format="%.6f") for k, v in DEFAULTS.items()}

# -----------------------------
# Helper functions
# -----------------------------
def brokerage(order_value: float) -> float:
    """Brokerage 0.1% per order, max ₹20"""
    return min(order_value * const["BROKERAGE_RATE"], const["BROKERAGE_CAP"])


def calc_equity_charges(segment, exchange, buy_price, sell_price, qty, dp_applicable):
    buy_value = buy_price * qty
    sell_value = sell_price * qty
    turnover = buy_value + sell_value

    brok = brokerage(buy_value) + brokerage(sell_value)

    exch_rate = const["EXCH_NSE"] if exchange == "NSE" else const["EXCH_BSE"]
    exch = turnover * exch_rate

    sebi = turnover * const["SEBI_CHARGE"]
    ipft = const["IPFT_FIXED"]

    if segment == "Intraday":
        stamp = buy_value * const["STAMP_INTRADAY_BUY"]
        stt = sell_value * const["STT_INTRADAY_SELL"]
    else:
        stamp = buy_value * const["STAMP_DELIVERY_BUY"]
        stt = (buy_value * const["STT_DELIVERY_BUY"]) + (sell_value * const["STT_DELIVERY_SELL"])

    dp = const["DP_CHARGE"] if (segment == "Delivery" and dp_applicable) else 0.0

    # GST applies on: brokerage + exchange + sebi
    gst = (brok + exch + sebi) * const["GST_RATE"]

    total = brok + exch + sebi + ipft + stamp + stt + dp + gst

    gross_pnl = sell_value - buy_value
    net_pnl = gross_pnl - total

    return {
        "buy_value": buy_value,
        "sell_value": sell_value,
        "turnover": turnover,
        "brokerage": brok,
        "exchange_txn": exch,
        "sebi": sebi,
        "ipft": ipft,
        "stamp": stamp,
        "stt": stt,
        "dp": dp,
        "gst": gst,
        "total_charges": total,
        "gross_pnl": gross_pnl,
        "net_pnl_after_charges": net_pnl,
    }


def calc_mtf_interest(buy_value, margin_percent, days):
    """Calculate MTF funded amount and interest for given holding days."""
    margin_percent = margin_percent / 100.0
    funded = buy_value * (1 - margin_percent)
    rate = const["MTF_INTEREST_RATE"]

    interest = funded * rate * (days / 365.0)
    return funded, interest


# -----------------------------
# UI Tabs
# -----------------------------
tab1, tab2, tab3 = st.tabs([
    "Equity Charges",
    "MTF Interest + Final P&L",
    "Tax + Take Home",
])

# -----------------------------
# Tab 1: Equity Charges
# -----------------------------
with tab1:
    st.subheader("Equity Charges Calculator")

    c1, c2, c3 = st.columns(3)

    with c1:
        segment = st.selectbox("Segment", ["Intraday", "Delivery"])
        exchange = st.selectbox("Exchange", ["NSE", "BSE"])

    with c2:
        qty = st.number_input("Quantity", min_value=1, value=100, step=1)
        buy_price = st.number_input("Buy Price (₹)", min_value=0.01, value=100.0, step=0.05, format="%.2f")

    with c3:
        sell_price = st.number_input("Sell Price (₹)", min_value=0.01, value=101.0, step=0.05, format="%.2f")
        dp_applicable = st.checkbox("Apply DP Charge (Delivery Sell)", value=True)

    equity = calc_equity_charges(segment, exchange, buy_price, sell_price, qty, dp_applicable)

    st.divider()

    o1, o2, o3, o4 = st.columns(4)
    o1.metric("Buy Value", f"₹{equity['buy_value']:.2f}")
    o2.metric("Sell Value", f"₹{equity['sell_value']:.2f}")
    o3.metric("Gross P&L", f"₹{equity['gross_pnl']:.2f}")
    o4.metric("Net P&L After Equity Charges", f"₹{equity['net_pnl_after_charges']:.2f}")

    st.subheader("Equity Charge Breakdown")
    st.write({
        "Brokerage": round(equity["brokerage"], 2),
        "STT": round(equity["stt"], 2),
        "Stamp Duty": round(equity["stamp"], 2),
        "Exchange Txn Charges": round(equity["exchange_txn"], 2),
        "SEBI Charges": round(equity["sebi"], 2),
        "IPFT Charges": round(equity["ipft"], 2),
        "DP Charges": round(equity["dp"], 2),
        "GST": round(equity["gst"], 2),
        "Total Equity Charges": round(equity["total_charges"], 2),
    })


# -----------------------------
# Tab 2: MTF Interest
# -----------------------------
with tab2:
    st.subheader("MTF Interest + Final P&L")
    st.info("MTF interest is calculated on FUNDED amount (borrowed portion).")

    c1, c2, c3 = st.columns(3)

    with c1:
        margin_percent = st.slider("Your Margin % (Own funds)", min_value=0, max_value=100, value=50)

    with c2:
        holding_days = st.number_input("Holding days", min_value=1, value=7)

    with c3:
        include_mtf = st.checkbox("Apply MTF Interest", value=True)

    funded, mtf_interest = calc_mtf_interest(equity["buy_value"], margin_percent, holding_days)

    st.divider()

    m1, m2, m3 = st.columns(3)
    m1.metric("Funded Amount", f"₹{funded:.2f}")
    m2.metric("MTF Interest Cost", f"₹{mtf_interest:.2f}")

    final_net_pnl = equity["net_pnl_after_charges"] - (mtf_interest if include_mtf else 0.0)
    m3.metric("Final Net P&L (Charges + MTF)", f"₹{final_net_pnl:.2f}")


# -----------------------------
# Tab 3: Tax + Take Home (YOUR FORMULA)
# take home profit = {(profit - (groww charges + tax)) - mtf interest}
# -----------------------------
with tab3:
    st.subheader("Tax + Take Home")
    st.caption("Final Take Home = {(Profit − (Groww Charges + Tax)) − MTF Interest}")

    st.warning("Tax is an estimate; please consult CA for exact filing.")

    income_type = st.selectbox(
        "Tax Treatment",
        [
            "Intraday (Business Income - slab)",
            "Delivery STCG (15%)",
            "Delivery LTCG (10% above 1L)",
        ]
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        realised_profit = st.number_input(
            "Profit / P&L before charges (₹)",
            value=float(equity["gross_pnl"]),
            step=100.0
        )

    with col2:
        slab_rate = st.number_input("Slab tax rate % (Business income)", value=30.0, step=1.0)
        ltcg_exemption = st.number_input("LTCG exemption (₹)", value=100000.0, step=10000.0)

    with col3:
        cess_rate = st.number_input("Cess %", value=4.0, step=0.5)
        extra_tax = st.number_input("Extra tax/surcharge (optional)", value=0.0, step=100.0)

    st.divider()

    st.markdown("#### Include MTF Interest")
    t1, t2 = st.columns(2)

    with t1:
        include_mtf_2 = st.checkbox("Apply MTF Interest in Take Home", value=True)

    with t2:
        mtf_days_2 = st.number_input("MTF holding days (for take-home)", min_value=1, value=7)

    funded2, mtf_interest2 = calc_mtf_interest(equity["buy_value"], margin_percent, mtf_days_2)

    # tax calculated on PROFIT
    taxable_amount = max(realised_profit, 0.0)

    if income_type == "Intraday (Business Income - slab)":
        base_tax = taxable_amount * (slab_rate / 100.0)

    elif income_type == "Delivery STCG (15%)":
        base_tax = taxable_amount * 0.15

    else:  # LTCG
        base_tax = max(taxable_amount - ltcg_exemption, 0.0) * 0.10

    tax = base_tax + (base_tax * (cess_rate / 100.0)) + extra_tax

    # profit after equity charges + tax
    profit_after_equity_and_tax = realised_profit - (equity["total_charges"] + tax)

    # subtract mtf at end
    mtf_interest_used = mtf_interest2 if include_mtf_2 else 0.0

    # FINAL take-home
    take_home = profit_after_equity_and_tax - mtf_interest_used

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Equity Charges", f"₹{equity['total_charges']:.2f}")
    r2.metric("Estimated Tax", f"₹{tax:.2f}")
    r3.metric("MTF Interest", f"₹{mtf_interest_used:.2f}")
    r4.metric("✅ Final Take Home", f"₹{take_home:.2f}")

    st.subheader("Calculation Summary")
    st.write({
        "Profit (before charges)": round(realised_profit, 2),
        "Equity charges": round(equity["total_charges"], 2),
        "Tax treatment": income_type,
        "Tax calculated on profit": round(taxable_amount, 2),
        "Tax": round(tax, 2),
        "Profit after equity + tax": round(profit_after_equity_and_tax, 2),
        "MTF interest applied": round(mtf_interest_used, 2),
        "Final take home": round(take_home, 2),
    })

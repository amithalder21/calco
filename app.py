import streamlit as st

st.set_page_config(page_title="Groww Trading P/L Calculator", layout="wide")

st.title("Groww Trading P/L Calculator")
st.caption("Charges based on the values shown in Groww portal (approx). You may edit constants in the sidebar.")

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

# Sidebar constants
st.sidebar.header("Edit Charges (Optional)")

const = {}
for k, v in DEFAULTS.items():
    const[k] = st.sidebar.number_input(k, value=float(v), format="%.6f")

# -----------------------------
# Helper functions
# -----------------------------
def brokerage(order_value):
    """Brokerage 0.1% per order, max ₹20"""
    b = order_value * const["BROKERAGE_RATE"]
    return min(b, const["BROKERAGE_CAP"])


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
    """
    margin_percent = your own capital percentage, remaining is funded.
    """
    margin_percent = margin_percent / 100.0
    funded = buy_value * (1 - margin_percent)
    rate = const["MTF_INTEREST_RATE"]

    interest = funded * rate * (days / 365.0)
    return funded, interest


# -----------------------------
# UI
# -----------------------------
tab1, tab2, tab3 = st.tabs(["Equity Charges", "MTF Interest + Final P&L", "Tax + Take Home"])

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

    data = calc_equity_charges(segment, exchange, buy_price, sell_price, qty, dp_applicable)

    st.divider()
    o1, o2, o3, o4 = st.columns(4)

    o1.metric("Buy Value", f"₹{data['buy_value']:.2f}")
    o2.metric("Sell Value", f"₹{data['sell_value']:.2f}")
    o3.metric("Gross P&L", f"₹{data['gross_pnl']:.2f}")
    o4.metric("Net P&L After Charges", f"₹{data['net_pnl_after_charges']:.2f}")

    st.subheader("Charge Breakdown")
    st.write({
        "Brokerage": round(data["brokerage"], 2),
        "STT": round(data["stt"], 2),
        "Stamp Duty": round(data["stamp"], 2),
        "Exchange Txn Charges": round(data["exchange_txn"], 2),
        "SEBI Charges": round(data["sebi"], 2),
        "IPFT Charges": round(data["ipft"], 2),
        "DP Charges": round(data["dp"], 2),
        "GST": round(data["gst"], 2),
        "Total Charges": round(data["total_charges"], 2),
    })


with tab2:
    st.subheader("MTF Interest + Final Profit/Loss")

    st.info("MTF interest is calculated on FUNDED amount (borrowed portion).")

    c1, c2, c3 = st.columns(3)

    with c1:
        margin_percent = st.slider("Your Margin % (Own funds)", min_value=0, max_value=100, value=50)

    with c2:
        holding_days = st.number_input("Holding days", min_value=1, value=7)

    with c3:
        include_mtf = st.checkbox("Apply MTF Interest", value=True)

    funded, interest = calc_mtf_interest(data["buy_value"], margin_percent, holding_days)

    st.divider()
    m1, m2, m3 = st.columns(3)

    m1.metric("Funded Amount", f"₹{funded:.2f}")
    m2.metric("MTF Interest Cost", f"₹{interest:.2f}")
    m3.metric("Total Cost (Charges + Interest)", f"₹{(data['total_charges'] + (interest if include_mtf else 0)):.2f}")

    final_net = data["net_pnl_after_charges"] - (interest if include_mtf else 0)

    st.subheader("Final Result")
    st.metric("Final Net P&L (After Charges + MTF Interest)", f"₹{final_net:.2f}")

    st.caption("Note: Actual interest may slightly vary depending on broker interest model and settlement cycle.")

with tab3:
    st.subheader("Tax + Take Home Calculator")
    st.caption("This is an estimate. Actual tax depends on your ITR filing type, income slab, audit applicability etc.")

    # User selects trading type for tax treatment
    income_type = st.selectbox(
        "Income Type / Tax Treatment",
        ["Intraday (Business Income)", "Delivery STCG (15%)", "Delivery LTCG (10% above 1L)"]
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        realised_pnl = st.number_input("Realised P&L (₹)", value=float(data["gross_pnl"]), step=100.0)
        other_income = st.number_input("Other taxable income (Salary/Business etc.) (₹)", value=0.0, step=1000.0)

    with col2:
        slab_rate = st.number_input("Tax slab rate % (for business income)", value=30.0, step=1.0)
        ltcg_exemption = st.number_input("LTCG exemption (₹)", value=100000.0, step=10000.0)

    with col3:
        cess = st.number_input("Health & Education cess %", value=4.0, step=0.5)
        extra_tax = st.number_input("Extra tax/charges (if any)", value=0.0, step=100.0)

    st.divider()

    # Net profit after charges
    total_charges = data["total_charges"]
    net_after_charges = realised_pnl - total_charges

    # Tax calculation
    estimated_tax = 0.0

    if income_type == "Intraday (Business Income)":
        # business income gets added in total income and taxed at slab
        taxable_amount = max(net_after_charges, 0)
        estimated_tax = taxable_amount * (slab_rate / 100.0)

    elif income_type == "Delivery STCG (15%)":
        taxable_amount = max(net_after_charges, 0)
        estimated_tax = taxable_amount * 0.15

    elif income_type == "Delivery LTCG (10% above 1L)":
        taxable_amount = max(net_after_charges - ltcg_exemption, 0)
        estimated_tax = taxable_amount * 0.10

    # Cess
    estimated_tax = estimated_tax + (estimated_tax * (cess / 100.0))
    estimated_tax += extra_tax

    take_home = net_after_charges - estimated_tax

    r1, r2, r3 = st.columns(3)
    r1.metric("Profit After Charges", f"₹{net_after_charges:.2f}")
    r2.metric("Estimated Tax", f"₹{estimated_tax:.2f}")
    r3.metric("Final Take Home", f"₹{take_home:.2f}")

    st.write({
        "Realised P&L entered": realised_pnl,
        "Total charges (from Tab 1/2)": round(total_charges, 2),
        "Net after charges": round(net_after_charges, 2),
        "Taxable amount used": round(taxable_amount, 2),
        "Tax method": income_type,
        "Final take home": round(take_home, 2),
    })

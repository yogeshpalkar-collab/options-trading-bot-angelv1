import streamlit as st
import os
from modules.angel_client import init_angel, get_option_quote, place_order
from modules.strategy import generate_signal
from modules.trade_manager import can_trade, manage_trade
from modules.utils import get_atm_strike

try:
    MASTER_PASSWORD = os.environ["MASTER_PASSWORD"]
except KeyError:
    st.error("❌ Missing MASTER_PASSWORD in environment variables")
    st.stop()

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔒 options_trading_bot")
    password = st.text_input("Enter Master Password", type="password")
    if st.button("Login"):
        if password == MASTER_PASSWORD:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Wrong password")
    st.stop()

st.title("📊 Nifty_Price_Action_Strategy – options_trading_bot")

if "angel" not in st.session_state:
    st.session_state["angel"] = init_angel()

if "trades" not in st.session_state:
    st.session_state["trades"] = []
if "trade_count" not in st.session_state:
    st.session_state["trade_count"] = 0

mode = st.radio("Mode", ["Paper Trading", "Auto Trading"])

angel = st.session_state["angel"]
spot = 22600  # placeholder, replace with get_option_quote for NIFTY index
atm = get_atm_strike(spot)
st.metric("Spot", spot)
st.metric("ATM", atm)

vwap, ema9, ema21, rsi = spot-5, spot-2, spot-3, 55
cpr_top, cpr_bottom = spot-10, spot-20
oi_bias = "BULLISH"

signal = generate_signal(spot, vwap, ema9, ema21, rsi, cpr_top, cpr_bottom, oi_bias)
st.subheader(f"Signal: {signal}")

if signal in ["GO CALL", "GO PUT"]:
    can, reason = can_trade(atm, st.session_state["trade_count"], st.session_state["trades"])
    if can:
        if st.button(f"🚀 Take Trade ({signal})"):
            entry_price = spot
            sl = spot - 10 if signal == "GO CALL" else spot + 10
            trade = {"strike": atm, "side": signal, "entry": entry_price, "sl": sl, "status": "OPEN"}
            st.session_state["trades"].append(trade)
            st.session_state["trade_count"] += 1

            if mode == "Auto Trading":
                place_order(angel, f"NIFTY{atm}CE", "BUY" if signal=="GO CALL" else "SELL", qty=50, symboltoken="12345")
    else:
        st.warning(reason)

st.subheader("📑 Trade Log")
for trade in st.session_state["trades"]:
    ltp = spot
    status, msg = manage_trade(trade["entry"], ltp, trade["sl"])
    st.write(trade, status, msg)

import streamlit as st
import os
from datetime import date, timedelta
from modules.angel_client import init_angel, fetch_instruments, get_option_quote, place_order
from modules.strategy import generate_signal
from modules.trade_manager import can_trade, manage_trade
from modules.utils import get_atm_strike

def get_next_tuesdays(count=3):
    today = date.today()
    days_ahead = (1 - today.weekday()) % 7  # Tuesday = 1
    if days_ahead == 0:
        days_ahead = 7
    first_tuesday = today + timedelta(days=days_ahead)
    expiries = []
    for i in range(count):
        d = first_tuesday + timedelta(weeks=i)
        expiries.append(d.strftime("%d%b%Y").upper())
    return expiries

def get_bias_reason(spot, vwap, ema9, ema21, rsi, cpr_top, cpr_bottom, oi_bias):
    reasons = []
    if ema9 > ema21: reasons.append("EMA9 > EMA21")
    else: reasons.append("EMA9 < EMA21")

    if ema9 > vwap: reasons.append("EMA9 > VWAP")
    else: reasons.append("EMA9 < VWAP")

    if rsi > 50: reasons.append("RSI > 50")
    else: reasons.append("RSI < 50")

    if spot > cpr_top: reasons.append("Above CPR")
    elif spot < cpr_bottom: reasons.append("Below CPR")
    else: reasons.append("Inside CPR")

    reasons.append(f"OI bias = {oi_bias}")
    if ema9 > ema21 and ema9 > vwap and rsi > 50 and spot > cpr_top and oi_bias == "BULLISH":
        bias = "BULLISH"
    elif ema9 < ema21 and ema9 < vwap and rsi < 50 and spot < cpr_bottom and oi_bias == "BEARISH":
        bias = "BEARISH"
    else:
        bias = "NEUTRAL"
    return bias, ", ".join(reasons)

# ---------------- AUTH ----------------
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

# ---------------- INIT ----------------
st.title("📊 Nifty_Price_Action_Strategy – options_trading_bot")

if "angel" not in st.session_state:
    st.session_state["angel"] = init_angel()
if "instruments" not in st.session_state:
    st.session_state["instruments"] = fetch_instruments(st.session_state["angel"])

if "trades" not in st.session_state:
    st.session_state["trades"] = []
if "trade_count" not in st.session_state:
    st.session_state["trade_count"] = 0

mode = st.radio("Mode", ["Paper Trading", "Auto Trading"])

angel = st.session_state["angel"]
instruments = st.session_state["instruments"]

# Live NIFTY spot from Angel
quote = get_option_quote(angel, "NSE", "NIFTY", "99926000")
if quote and "data" in quote:
    spot = float(quote["data"]["ltp"])
else:
    spot = 22600

atm = get_atm_strike(spot)
st.metric("Spot", spot)
st.metric("ATM", atm)

# Expiry selection (Tuesdays)
expiry = st.selectbox("Select Expiry", get_next_tuesdays())

def get_token(symbol):
    row = instruments[instruments["tradingsymbol"] == symbol]
    return str(row.iloc[0]["token"]) if not row.empty else None

# OI Bias calculation ATM ±2 strikes
strikes = [atm - 100, atm - 50, atm, atm + 50, atm + 100]
total_ce_change, total_pe_change = 0, 0

for strike in strikes:
    ce_symbol = f"NIFTY{expiry}{strike}CE"
    pe_symbol = f"NIFTY{expiry}{strike}PE"

    ce_token = get_token(ce_symbol)
    pe_token = get_token(pe_symbol)

    ce_quote = get_option_quote(angel, "NFO", ce_symbol, ce_token) if ce_token else None
    pe_quote = get_option_quote(angel, "NFO", pe_symbol, pe_token) if pe_token else None

    ce_change_oi = ce_quote["data"].get("changeinOpenInterest", 0) if ce_quote else 0
    pe_change_oi = pe_quote["data"].get("changeinOpenInterest", 0) if pe_quote else 0

    total_ce_change += ce_change_oi
    total_pe_change += pe_change_oi

if total_pe_change > total_ce_change:
    oi_bias = "BULLISH"
    oi_reason = f"PE Change OI ({total_pe_change}) > CE Change OI ({total_ce_change})"
elif total_ce_change > total_pe_change:
    oi_bias = "BEARISH"
    oi_reason = f"CE Change OI ({total_ce_change}) > PE Change OI ({total_pe_change})"
else:
    oi_bias = "NEUTRAL"
    oi_reason = f"CE Change OI ({total_ce_change}) ≈ PE Change OI ({total_pe_change})"

st.subheader(f"📊 OI Bias: {oi_bias}")
st.caption(f"Reason: {oi_reason}")

# Dummy indicators (replace later with real)
vwap, ema9, ema21, rsi = spot-5, spot-2, spot-3, 55
cpr_top, cpr_bottom = spot-10, spot-20

# CPR Width meter
cpr_width = cpr_top - cpr_bottom
cpr_percent = (cpr_width / spot) * 100
if cpr_percent < 0.25:
    cpr_class = "NARROW"
elif cpr_percent <= 0.5:
    cpr_class = "NORMAL"
else:
    cpr_class = "WIDE"
st.metric("CPR Width", f"{cpr_percent:.2f}% ({cpr_class})")

# Bias dashboard
bias, reason = get_bias_reason(spot, vwap, ema9, ema21, rsi, cpr_top, cpr_bottom, oi_bias)
st.subheader(f"📊 Market Bias: {bias}")
st.caption(f"Reason: {reason}")

signal = generate_signal(spot, vwap, ema9, ema21, rsi, cpr_top, cpr_bottom, oi_bias)
st.subheader(f"Signal: {signal}")

if signal in ["GO CALL", "GO PUT"]:
    can, reason = can_trade(atm, st.session_state["trade_count"], st.session_state["trades"])
    if can:
        if st.button(f"🚀 Take Trade ({signal})"):
            entry_price = spot
            sl = spot - 10 if signal == "GO CALL" else spot + 10
            option_symbol = f"NIFTY{expiry}{atm}{'CE' if signal=='GO CALL' else 'PE'}"
            trade = {"strike": atm, "side": signal, "entry": entry_price, "sl": sl, "status": "OPEN", "symbol": option_symbol}
            st.session_state["trades"].append(trade)
            st.session_state["trade_count"] += 1

            if mode == "Auto Trading":
                token = get_token(option_symbol)
                place_order(angel, option_symbol, "BUY" if signal=="GO CALL" else "SELL", qty=50, symboltoken=token)
    else:
        st.warning(reason)

# ---------------- TRADE PANEL ----------------
st.subheader("📑 Trade Log")
for trade in st.session_state["trades"]:
    ltp = spot
    status, msg = manage_trade(trade["entry"], ltp, trade["sl"])
    st.write(trade, status, msg)

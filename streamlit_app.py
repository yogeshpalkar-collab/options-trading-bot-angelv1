import streamlit as st
import pandas as pd
from modules.angel_client import init_angel, fetch_instruments, get_option_quote, place_order
from modules.strategy import generate_signal
from modules.trade_manager import can_trade, manage_trade, initial_stoploss, calculate_atr
from modules.utils import get_atm_strike

# ---------------- SESSION STATE INIT ----------------
if "trades" not in st.session_state:
    st.session_state["trades"] = []
if "trade_count" not in st.session_state:
    st.session_state["trade_count"] = 0
if "open_positions" not in st.session_state:
    st.session_state["open_positions"] = []

st.title("📊 Options Trading Bot (Angel One)")

# ---------------- LOGIN ----------------
obj = init_angel()
if not obj:
    st.error("❌ Angel login failed. Please check API key / Client ID / Password / TOTP secret.")
if not obj:

# ---------------- INSTRUMENTS ----------------
instruments = fetch_instruments()
if instruments.empty:
    st.error("⚠️ Failed to fetch instruments. Cannot continue.")

expiries = sorted(instruments["expiry"].unique()) if "expiry" in instruments else []
expiry = st.selectbox("Select Expiry", expiries) if expiries else None

spot = 22600  # TODO: replace with live spot fetch
atm = get_atm_strike(spot)

st.markdown(f"**Spot:** {spot} | **ATM Strike:** {atm} | **Expiry:** {expiry if expiry else 'N/A'}")

# ---------------- STRATEGY SIGNAL ----------------
signal = "NO-GO"  # placeholder, actual calc would use indicators
st.markdown(f"### 🎯 Signal: {signal}")

# ---------------- TRADE PANEL ----------------
st.subheader("📑 Trade Log")

if st.session_state["trades"]:
    trade_rows = []
    for trade in st.session_state["trades"]:
        ltp = spot
        status, msg = manage_trade(trade["entry"], ltp, trade["sl"])
        if "trailing SL set at" in msg:
            try:
                new_sl = float(msg.split("at")[-1].strip())
                trade["sl"] = new_sl
            except:
                pass

        trade_rows.append({
            "Symbol": trade.get("symbol",""),
            "Side": trade.get("side",""),
            "Entry": trade.get("entry",0),
            "ATR": trade.get("atr","-"),
            "SL at Entry": trade.get("sl_entry", trade.get("sl",0)),
            "Current LTP": ltp,
            "Target": trade.get("entry",0) + 10 if trade.get("side") == "GO CALL" else trade.get("entry",0) - 10,
            "SL/TSL": trade.get("sl",0),
            "Status": status,
            "Notes": msg
        })

    df = pd.DataFrame(trade_rows)
    st.dataframe(df, use_container_width=True)
else:
    st.info("No trades yet.")
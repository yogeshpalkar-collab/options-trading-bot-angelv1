import streamlit as st
import os
from datetime import date, timedelta
import pandas as pd
from modules.angel_client import init_angel, fetch_instruments, get_option_quote, place_order
from modules.strategy import generate_signal
from modules.trade_manager import can_trade, manage_trade
from modules.utils import get_atm_strike

# Dummy placeholders for initialization to keep example concise
spot = 22600


# ---------------- TRADE PANEL ----------------
import pandas as pd

st.subheader("📑 Trade Log")

if st.session_state["trades"]:
    trade_rows = []
    for trade in st.session_state["trades"]:
        ltp = spot
        status, msg = manage_trade(trade["entry"], ltp, trade["sl"])

        # Update SL dynamically if trailing is applied
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

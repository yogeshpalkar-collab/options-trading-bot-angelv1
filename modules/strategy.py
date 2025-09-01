import streamlit as st

def generate_signal(spot, vwap, ema9, ema21, rsi, cpr_top, cpr_bottom, oi_bias):
    try:
        if spot > vwap and ema9 > ema21 and rsi > 50 and spot > cpr_top and oi_bias == "BULLISH":
            return "GO CALL"
        elif spot < vwap and ema9 < ema21 and rsi < 50 and spot < cpr_bottom and oi_bias == "BEARISH":
            return "GO PUT"
        else:
            return "NO-GO"
    except Exception as e:
        st.error(f"❌ Strategy error: {e}")
        return "NO-GO"

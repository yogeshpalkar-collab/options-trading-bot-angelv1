import streamlit as st

def generate_signal(spot, vwap, ema9, ema21, rsi, cpr_top, cpr_bottom, oi_bias):
    try:
        cpr_width = cpr_top - cpr_bottom
        wide_threshold = 0.005 * spot

        if cpr_width > wide_threshold and cpr_bottom <= spot <= cpr_top:
            return "NO-GO"

        if ema9 > ema21 and ema9 > vwap and rsi > 50 and spot > cpr_top and oi_bias == "BULLISH":
            return "GO CALL"

        elif ema9 < ema21 and ema9 < vwap and rsi < 50 and spot < cpr_bottom and oi_bias == "BEARISH":
            return "GO PUT"

        else:
            return "NO-GO"
    except Exception as e:
        st.error(f"❌ Strategy error: {e}")
        return "NO-GO"

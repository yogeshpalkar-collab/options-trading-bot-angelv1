import streamlit as st
from datetime import datetime

def can_trade(strike, trade_count, open_positions):
    now = datetime.now().time()
    if trade_count >= 3:
        return False, "Max 3 trades reached"
    if strike in [t["strike"] for t in open_positions]:
        return False, "Strike already traded"
    if now.hour >= 15:
        return False, "Trading stopped after 3 PM"
    return True, ""

def manage_trade(entry_price, ltp, sl, target=10, trail_gap=5):
    profit = ltp - entry_price
    if profit >= target and profit < target + 5:
        return "EXIT", f"Booked ₹{target}"
    elif profit >= target + 5:
        new_sl = ltp - trail_gap
        return "HOLD", f"Sudden jump, trailing SL set at {new_sl}"
    elif ltp <= sl:
        return "EXIT", "Stop loss hit"
    else:
        return "HOLD", "Trade active"

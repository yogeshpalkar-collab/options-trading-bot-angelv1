import numpy as np
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

def calculate_atr(prices, period=10):
    if not prices:
        return 10
    if len(prices) < period:
        return max(10, np.std(prices))
    diffs = [abs(prices[i] - prices[i-1]) for i in range(1, len(prices))]
    return max(10, np.mean(diffs[-period:]) * 1.5)

def initial_stoploss(entry_price, side, prices):
    sl_points = calculate_atr(prices)
    if side == "GO CALL":
        return entry_price - sl_points
    else:
        return entry_price + sl_points

def manage_trade(entry_price, ltp, sl, target=10, trail_gap=5):
    profit = ltp - entry_price
    if profit >= target and profit < target + 5:
        return "EXIT", f"Booked ₹{target}"
    elif profit >= target + 5:
        new_sl = ltp - trail_gap
        return "HOLD", f"Sudden jump, trailing SL set at {new_sl}"
    elif (ltp <= sl and entry_price < ltp) or (ltp >= sl and entry_price > ltp):
        return "EXIT", "Stop loss hit"
    else:
        return "HOLD", "Trade active"

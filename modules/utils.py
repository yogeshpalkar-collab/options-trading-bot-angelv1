def get_atm_strike(spot, step=50):
    return int(round(spot / step) * step)

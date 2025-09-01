import streamlit as st
from SmartApi import SmartConnect
import pyotp

def init_angel():
    try:
        obj = SmartConnect(api_key=st.secrets["ANGEL_API_KEY"])
        token = pyotp.TOTP(st.secrets["ANGEL_TOTP"]).now()
        obj.generateSession(st.secrets["ANGEL_CLIENT_ID"], st.secrets["ANGEL_PASSWORD"], token)
        return obj
    except Exception as e:
        st.error(f"❌ Angel init failed: {e}")
        return None

def get_option_quote(obj, exchange, tradingsymbol, symboltoken):
    try:
        params = {"exchange": exchange, "tradingsymbol": tradingsymbol, "symboltoken": symboltoken}
        return obj.ltpData(**params)
    except Exception as e:
        st.error(f"❌ Quote fetch failed: {e}")
        return None

def place_order(obj, tradingsymbol, side, qty, symboltoken, product="INTRADAY"):
    try:
        orderparams = {
            "variety": "NORMAL",
            "tradingsymbol": tradingsymbol,
            "symboltoken": symboltoken,
            "transactiontype": side,
            "exchange": "NFO",
            "ordertype": "MARKET",
            "producttype": product,
            "duration": "DAY",
            "price": "0",
            "squareoff": "0",
            "stoploss": "0",
            "quantity": qty
        }
        return obj.placeOrder(orderparams)
    except Exception as e:
        st.error(f"❌ Order failed: {e}")
        return None

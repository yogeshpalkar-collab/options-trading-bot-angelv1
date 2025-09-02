import streamlit as st
from SmartApi import SmartConnect
import pyotp
import os
import pandas as pd
import requests

def init_angel():
    try:
        obj = SmartConnect(api_key=os.environ["ANGEL_API_KEY"])
        token = pyotp.TOTP(os.environ["ANGEL_TOTP"]).now()
        resp = obj.generateSession(os.environ["ANGEL_CLIENT_ID"], os.environ["ANGEL_PASSWORD"], token)

        if resp.get("status") is True:
            return obj
        else:
            reason = resp.get("message", "Unknown error")
            st.error(f"❌ Angel login failed: {reason}")
            return None
    except Exception as e:
        st.error(f"❌ Angel login exception: {e}")
        return None

def fetch_instruments():
    try:
        url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
        data = requests.get(url).json()
        instruments = pd.DataFrame(data)
        instruments = instruments[instruments["exch_seg"] == "NFO"]
        return instruments
    except Exception as e:
        st.error(f"❌ Failed to fetch instruments: {e}")
        return pd.DataFrame()

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

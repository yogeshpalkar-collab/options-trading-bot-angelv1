import streamlit as st
from SmartApi import SmartConnect
import pyotp
import os
import pandas as pd

def init_angel():
    try:
        obj = SmartConnect(api_key=os.environ["ANGEL_API_KEY"])
        token = pyotp.TOTP(os.environ["ANGEL_TOTP"]).now()
        obj.generateSession(os.environ["ANGEL_CLIENT_ID"], os.environ["ANGEL_PASSWORD"], token)
        return obj
    except Exception as e:
        st.error(f"❌ Angel init failed: {e}")
        return None

def fetch_instruments(obj):
    try:
        # Use Angel API's master contract download
        file_path = obj.download_master_contract("NFO")
        instruments = pd.read_csv(file_path)
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

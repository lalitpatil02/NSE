# kite_live_data.py
from kiteconnect import KiteTicker, KiteConnect
from datetime import datetime, timedelta
import pandas as pd
import time
import csv
import threading
from app.models import KiteToken

# Shared dictionary to hold latest tick by symbol
live_data_cache = {}

# Setup API key and token
api_key = "doieti8s40hlpp6l"
token = KiteToken.objects.latest('created_at')

kite = KiteConnect(api_key=api_key)
kite.set_access_token(token.access_token)

# Load instrument tokens
tokens = []
symbol_map = {}  # instrument_token -> tradingsymbol

with open("filtered_instrument_tokens.csv", newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for i, row in enumerate(reader):
        if i >= 3000:
            break
        try:
            instrument_token = int(row["instrument_token"])
            tokens.append(instrument_token)
            symbol_map[instrument_token] = row["tradingsymbol"]
        except ValueError:
            pass

print(f"✅ Loaded {len(tokens)} tokens for streaming.")

kws = KiteTicker(api_key, token.access_token)

def on_connect(ws, response):
    print("Connected to WebSocket.")
    ws.subscribe(tokens)
    ws.set_mode(ws.MODE_FULL, tokens)

def on_ticks(ws, ticks):
    now = datetime.now()
    for tick in ticks:
        instrument_token = tick.get("instrument_token")
        symbol = symbol_map.get(instrument_token, str(instrument_token))
        live_data_cache[symbol] = {
            "price": tick.get("last_price", 0),
            "volume": tick.get("volume", 0),
            "high": tick.get("ohlc", {}).get("high", 0),
            "low": tick.get("ohlc", {}).get("low", 0),
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S")
        }

def on_close(ws, code, reason): print("WebSocket closed:", reason)
def on_error(ws, code, reason): print("WebSocket error:", code, reason)

# Register callbacks
kws.on_connect = on_connect
kws.on_ticks = on_ticks
kws.on_close = on_close
kws.on_error = on_error

# Start WebSocket in a separate thread
def start_ws():
    kws.connect(threaded=True)

t = threading.Thread(target=start_ws)
t.daemon = True
t.start()

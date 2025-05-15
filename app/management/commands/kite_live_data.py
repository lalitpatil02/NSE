from kiteconnect import KiteTicker
from app.models import InstrumentDetails, KiteToken
from kiteconnect import KiteConnect
from datetime import datetime, timedelta
import pandas as pd
import time
import csv

# Replace these with your own credentials
api_key = "doieti8s40hlpp6l"
token = KiteToken.objects.latest('created_at')
kite = KiteConnect(api_key=api_key)
kite.set_access_token(token.access_token)

tokens = []
with open("filtered_instrument_tokens.csv", newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for i, row in enumerate(reader):
        if i >= 3000:
            break
        try:
            tokens.append(int(row["instrument_token"]))
        except ValueError:
            pass

print(f"✅ Loaded {len(tokens)} tokens for streaming.")

# Create KiteTicker instance
kws = KiteTicker(api_key, token.access_token)

# For candle generation
tick_data = []
current_candle_start = None

# Callback when connection is established
def on_connect(ws, response):
    print("Connected to WebSocket.")
    ws.subscribe(tokens)
    ws.set_mode(ws.MODE_FULL, tokens)

# Callback when ticks are received
def on_ticks(ws, ticks):
    global tick_data, current_candle_start

    for tick in ticks:
        print("=============",tick)
        now = datetime.now().replace(second=0, microsecond=0)

        if current_candle_start is None:
            current_candle_start = now

        if now >= current_candle_start + timedelta(minutes=5):
            # Generate 5-min candle
            if tick_data:
                print("==============tick_data",tick_data)
                df = pd.DataFrame(tick_data)
                open_price = df["last_price"].iloc[0]
                high_price = df["last_price"].max()
                low_price = df["last_price"].min()
                close_price = df["last_price"].iloc[-1]
                volume = df["volume"].iloc[-1] - df["volume"].iloc[0]

                candle = {
                    "time": current_candle_start,
                    "open": open_price,
                    "high": high_price,
                    "low": low_price,
                    "close": close_price,
                    "volume": volume
                }

                print("🕯️ 5-min Candle:", candle)

            # Reset for new candle
            current_candle_start = now
            tick_data = []

        # Append current tick
        tick_data.append({
            "last_price": tick.get("last_price", 0),
            "volume": tick.get("volume", 0),
            "timestamp": datetime.now()
        })

# Other callbacks
def on_close(ws, code, reason):
    print("WebSocket closed:", reason)

def on_error(ws, code, reason):
    print("Error:", code, reason)

def on_reconnect(ws, attempts_count):
    print("Reconnecting...", attempts_count)

def on_order_update(ws, data):
    print("Order update:", data)

# Assign callbacks
kws.on_connect = on_connect
kws.on_ticks = on_ticks
kws.on_close = on_close
kws.on_error = on_error
kws.on_reconnect = on_reconnect
kws.on_order_update = on_order_update

# Start WebSocket
kws.connect(threaded=True)

# Keep main thread alive
while True:
    time.sleep(1)

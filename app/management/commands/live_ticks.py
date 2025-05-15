from kiteconnect import KiteTicker, KiteConnect
from app.models import KiteToken
import csv
import os
import threading
import logging
from datetime import datetime
import time

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Replace with your credentials
API_KEY = "doieti8s40hlpp6l"

# Initialize KiteConnect
try:

    # comment the below code if you got the access token
    api_key = "doieti8s40hlpp6l"
    api_secret = "ijm22wvh5ks2k8m1c72psg17drfj4s29"
    request_token = "9dHgm1XuAA5MUHu4NsB16gH1TR0GJZl1"
    data = kite.generate_session(request_token, api_secret=api_secret)
    access_token = data["access_token"]
    # from to this line you can get the access token



    # if you got the access token then comment the above code
    # access_token = "tJgd1scX5ljHyDv5BkwOaF7rzplf7TxS" # copy the access token from kite connect



    print("access_token",access_token)
    kite = KiteConnect(api_key=API_KEY)
    kite.set_access_token(access_token)
except Exception as e:
    logger.error(f"Failed to initialize KiteConnect: {e}")
    exit(1)

# Create data directory
DATA_DIR = "tick_data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# CSV setup
CSV_FILENAME = os.path.join(DATA_DIR, f"tick_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
CSV_HEADERS = ["timestamp", "instrument_token", "last_price", "volume", "ohlc_open", "ohlc_high", "ohlc_low", "ohlc_close", "change", "last_trade_time"]

# Thread-safe storage for latest data
latest_data = {}
data_lock = threading.Lock()

# Initialize CSV file
with open(CSV_FILENAME, 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS)
    writer.writeheader()

# Load instrument tokens
TOKENS = []
try:
    with open("filtered_instrument_tokens.csv", newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for i, row in enumerate(reader):
            if i >= 3000:
                break
            try:
                TOKENS.append(int(row["instrument_token"]))
            except ValueError:
                logger.warning(f"Invalid token in row {i+1}: {row}")
    logger.info(f"Loaded {len(TOKENS)} tokens for streaming.")
except FileNotFoundError:
    logger.error("Instrument tokens CSV file not found.")
    exit(1)

def append_to_csv(tick_row):
    """Append a single tick to the CSV file."""
    try:
        with open(CSV_FILENAME, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS)
            writer.writerow(tick_row)
    except Exception as e:
        logger.error(f"Failed to append to CSV: {e}")

# WebSocket callbacks
def on_connect(ws, response):
    logger.info("Connected to WebSocket.")
    ws.subscribe(TOKENS)
    ws.set_mode(ws.MODE_FULL, TOKENS)

def on_ticks(ws, ticks):
    for tick in ticks:
        instrument_token = tick.get("instrument_token", "")
        if instrument_token not in TOKENS:
            continue

        # Prepare tick data
        tick_row = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "instrument_token": instrument_token,
            "last_price": tick.get("last_price", 0),
            "volume": tick.get("volume", 0),
            "ohlc_open": tick.get("ohlc", {}).get("open", 0),
            "ohlc_high": tick.get("ohlc", {}).get("high", 0),
            "ohlc_low": tick.get("ohlc", {}).get("low", 0),
            "ohlc_close": tick.get("ohlc", {}).get("close", 0),
            "change": tick.get("change", 0),
            "last_trade_time": tick.get("last_trade_time", "")
        }

        # Update latest data in memory
        with data_lock:
            latest_data[instrument_token] = tick_row

        # Append tick to CSV
        append_to_csv(tick_row)

def on_close(ws, code, reason):
    logger.warning(f"WebSocket closed: {reason}")

def on_error(ws, code, reason):
    logger.error(f"WebSocket error: {code} - {reason}")

def on_reconnect(ws, attempts_count):
    logger.info(f"Reconnecting... Attempt {attempts_count}")

def on_order_update(ws, data):
    logger.info(f"Order update: {data}")

# Initialize KiteTicker
try:
    # kws = KiteTicker(API_KEY, token.access_token)
    kws = KiteTicker(API_KEY, access_token)
    kws.on_connect = on_connect
    kws.on_ticks = on_ticks
    kws.on_close = on_close
    kws.on_error = on_error
    kws.on_reconnect = on_reconnect
    kws.on_order_update = on_order_update

    # Start WebSocket
    kws.connect(threaded=True)
except Exception as e:
    logger.error(f"Failed to start WebSocket: {e}")
    exit(1)

# Keep main thread alive
while True:
    time.sleep(1)
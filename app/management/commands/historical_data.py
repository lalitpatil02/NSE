import csv
import requests
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from kiteconnect import KiteConnect
from app.models import InstrumentDetails, KiteToken
import time


class Command(BaseCommand):
    help = "Import instruments and update historical OHLC data"

    def handle(self, *args, **kwargs):
        api_key = "doieti8s40hlpp6l"
        token = KiteToken.objects.latest('created_at')
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(token.access_token)

        headers = {
            'X-Kite-Version': '3',
            'Authorization': f'token {api_key}:{token.access_token}'
        }

        # Step 1: Download instruments list
        self.stdout.write("📥 Fetching instrument list...")
        response = requests.get('https://api.kite.trade/instruments', headers=headers)
        response.raise_for_status()

        lines = response.text.splitlines()
        reader = csv.DictReader(lines)
        # Step 2: Prepare CSV file to save instrument tokens
        csv_file_path = "instrument_tokens.csv"
        csv_file = open(csv_file_path, mode="w", newline="")
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow([
            "instrument_token", "exchange_token", "tradingsymbol", "name", "last_price", "expiry", 
            "strike", "tick_size", "lot_size", "instrument_type", "segment", "exchange"
        ])  # Header

        count = 0
        for row in reader:
            segment = row["segment"]

            if segment not in ["NSE", "BSE", "NFO", "INDICES"]:
            # if row["segment"] != "NSE":
                continue  # Skip irrelevant instruments

            try:
                obj, created = InstrumentDetails.objects.update_or_create(
                    instrument_token=row["instrument_token"],
                    defaults={
                        "exchange_token": row["exchange_token"],
                        "tradingsymbol": row["tradingsymbol"],
                        "name": row["name"],
                        "last_price": float(row["last_price"]),
                        "expiry": datetime.strptime(row["expiry"], "%Y-%m-%d").date() if row["expiry"] else None,
                        "strike": float(row["strike"]),
                        "tick_size": float(row["tick_size"]),
                        "lot_size": int(row["lot_size"]),
                        "instrument_type": row["instrument_type"],
                        "segment": row["segment"],
                        "exchange": row["exchange"],
                    }
                )
                csv_writer.writerow([
                    row["instrument_token"],
                    row["exchange_token"],
                    row["tradingsymbol"],
                    row["name"],
                    row["last_price"],
                    row["expiry"],
                    row["strike"],
                    row["tick_size"],
                    row["lot_size"],
                    row["instrument_type"],
                    row["segment"],
                    row["exchange"],
                ])

                status = "🆕 Created" if created else "♻️ Updated"
                self.stdout.write(f"{status}: {obj.tradingsymbol}")
                print('=====================obj',obj)
                self.update_historical_data(obj, headers)
                count += 1

                # Respect Kite's rate limits (3/sec)
                time.sleep(0.35)

            except Exception as e:
                self.stderr.write(f"❌ Error processing {row['tradingsymbol']}: {str(e)}")
        csv_file.close()
        self.stdout.write(f"✅ Done. Total instruments processed: {count}")

    def update_historical_data(self, instrument_obj, headers):
        from_day = "2025-04-21"
        to_day = "2025-04-22"
        from_time = f"{from_day}"
        to_time = f"{to_day}"

        url = f"https://api.kite.trade/instruments/historical/{instrument_obj.instrument_token}/day"
        params = {"from": from_time, "to": to_time}

        try:
            resp = requests.get(url, headers=headers, params=params)
            if resp.status_code != 200:
                self.stderr.write(f"❌ Failed historical for {instrument_obj.tradingsymbol}")
                return

            candles = resp.json().get("data", {}).get("candles", [])
            if candles:
                ts, o, h, l, c, v = candles[-1]  # End-of-day candle
                instrument_obj.open = o
                instrument_obj.high = h
                instrument_obj.low = l
                instrument_obj.close = c
                instrument_obj.timestamp = ts
                instrument_obj.volume = v
                instrument_obj.save()
                self.stdout.write(f"📊 EOD updated: {instrument_obj.tradingsymbol}")
            else:
                self.stdout.write(f"ℹ️ No candles: {instrument_obj.tradingsymbol}")

        except Exception as e:
            self.stderr.write(f"🚨 Error fetching historical for {instrument_obj.tradingsymbol}: {str(e)}")

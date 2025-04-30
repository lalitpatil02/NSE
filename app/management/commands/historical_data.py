import csv
import requests
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from kiteconnect import KiteConnect
from app.models import InstrumentDetails, KiteToken, HistoricalOHLC
import time


class Command(BaseCommand):
    help = "Import instruments and update historical OHLC data for multiple days"

    def handle(self, *args, **kwargs):
        api_key = "doieti8s40hlpp6l"
        token = KiteToken.objects.latest('created_at')
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(token.access_token)

        headers = {
            'X-Kite-Version': '3',
            'Authorization': f'token {api_key}:{token.access_token}'
        }

        self.stdout.write("📥 Fetching instrument list...")
        response = requests.get('https://api.kite.trade/instruments', headers=headers)
        response.raise_for_status()

        lines = response.text.splitlines()
        reader = csv.DictReader(lines)

        csv_file_path = "instrument_tokens.csv"
        csv_file = open(csv_file_path, mode="w", newline="")
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow([
            "instrument_token", "exchange_token", "tradingsymbol", "name", "last_price", "expiry",
            "strike", "tick_size", "lot_size", "instrument_type", "segment", "exchange"
        ])

        timing_file_path = "historical_data_timing.csv"
        timing_file = open(timing_file_path, mode="w", newline="")
        timing_writer = csv.writer(timing_file)
        timing_writer.writerow(["tradingsymbol", "instrument_token", "duration_secs", "error"])

        count = 0
        total_start_time = time.time()

        for row in reader:
            segment = row["segment"]
            if segment not in ["NSE", "BSE", "NFO", "INDICES"]:
                continue

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
                    row["instrument_token"], row["exchange_token"], row["tradingsymbol"],
                    row["name"], row["last_price"], row["expiry"], row["strike"],
                    row["tick_size"], row["lot_size"], row["instrument_type"],
                    row["segment"], row["exchange"]
                ])

                status = "🆕 Created" if created else "♻️ Updated"
                self.stdout.write(f"{status}: {obj.tradingsymbol}")

                self.update_historical_data(obj, timing_writer, headers)
                count += 1

                time.sleep(0.35)

            except Exception as e:
                self.stderr.write(f"❌ Error processing {row['tradingsymbol']}: {str(e)}")

        csv_file.close()
        timing_file.close()

        total_end_time = time.time()
        total_duration_seconds = int(total_end_time - total_start_time)
        hours, remainder = divmod(total_duration_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        formatted_time = f"{hours}h {minutes}m {seconds}s"

        with open("historical_data_total_time.csv", mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["total_instruments_processed", "total_time_seconds", "formatted_time"])
            writer.writerow([count, total_duration_seconds, formatted_time])

        self.stdout.write(f"✅ Done. Total instruments processed: {count}")
        self.stdout.write(f"🕒 Total time taken: {formatted_time} ({total_duration_seconds} seconds)")

    def update_historical_data(self, instrument_obj, timing_writer, headers):
        to_day = "2025-04-29"
        from_day = "2025-04-29"
        start_time = time.time()
        interval_ = "day"

        url = f"https://api.kite.trade/instruments/historical/{instrument_obj.instrument_token}/{interval_}"
        params = {"from": str(from_day), "to": str(to_day)}

        try:
            resp = requests.get(url, headers=headers, params=params)
            if resp.status_code != 200:
                self.stderr.write(f"❌ Failed historical for {instrument_obj.tradingsymbol}")
                return

            candles = resp.json().get("data", {}).get("candles", [])
            duration = time.time() - start_time

            for candle in candles:
                ts, o, h, l, c, v = candle
                timestamp = datetime.fromisoformat(ts)
                HistoricalOHLC.objects.update_or_create(
                    instrument=instrument_obj,
                    timestamp=timestamp,
                    interval=interval_,
                    defaults={
                        "open": o,
                        "high": h,
                        "low": l,
                        "close": c,
                        "volume": v,
                    }
                )

            if candles:
                self.stdout.write(f"📊 {instrument_obj.tradingsymbol}: {len(candles)} OHLC entries saved")

            timing_writer.writerow([instrument_obj.tradingsymbol, instrument_obj.instrument_token, round(duration, 2), ""])

        except Exception as e:
            duration = time.time() - start_time
            timing_writer.writerow([instrument_obj.tradingsymbol, instrument_obj.instrument_token, "ERROR", str(e)])
            self.stderr.write(f"🚨 Error fetching historical for {instrument_obj.tradingsymbol}: {str(e)}")

import csv
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from kiteconnect import KiteConnect
from app.models import InstrumentDetails, KiteToken, HistoricalOHLC
import time

#  python manage.py new_historical_data --start-date 2024-01-01 --end-date 2024-12-31 --interval day
class Command(BaseCommand):
    help = "Import instruments and update historical OHLC data for specified date range"

    def add_arguments(self, parser):
        parser.add_argument(
            '--start-date',
            type=str,
            help='Start date in YYYY-MM-DD format',
            required=True
        )
        parser.add_argument(
            '--end-date',
            type=str,
            help='End date in YYYY-MM-DD format',
            required=True
        )
        parser.add_argument(
            '--interval',
            type=str,
            default='day',
            choices=['minute', '5minute', '15minute', '30minute', '60minute', 'day'],
            help='Data interval (default: day)'
        )

    def handle(self, *args, **options):
        api_key = "doieti8s40hlpp6l"
        token = KiteToken.objects.latest('created_at')
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(token.access_token)

        # Parse dates
        try:
            start_date = datetime.strptime(options['start_date'], '%Y-%m-%d')
            end_date = datetime.strptime(options['end_date'], '%Y-%m-%d')
            
            if start_date > end_date:
                raise ValueError("Start date cannot be after end date")
            
            if end_date > datetime.now():
                self.stdout.write(self.style.WARNING("End date is in the future. Using current date instead."))
                end_date = datetime.now()
                
        except ValueError as e:
            self.stderr.write(self.style.ERROR(f"Invalid date format: {str(e)}"))
            return

        self.stdout.write(f"📅 Fetching data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        self.stdout.write(f"⏱️ Interval: {options['interval']}")

        self.stdout.write("📥 Fetching instrument list...")
        instruments = kite.instruments()

        csv_file_path = "instrument_tokens.csv"
        timing_file_path = "historical_data_timing.csv"

        with open(csv_file_path, mode="w", newline="") as csv_file, open(timing_file_path, mode="w", newline="") as timing_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow([
                "instrument_token", "exchange_token", "tradingsymbol", "name", "last_price", "expiry",
                "strike", "tick_size", "lot_size", "instrument_type", "segment", "exchange"
            ])

            timing_writer = csv.writer(timing_file)
            timing_writer.writerow(["tradingsymbol", "instrument_token", "duration_secs", "error"])

            count = 0
            total_start_time = time.time()

            for instrument in instruments:
                segment = instrument["segment"]
                instrument_type = instrument["instrument_type"]

                # Filter only tradable instruments, skip NAVs
                if segment not in ["NSE", "BSE", "NFO", "INDICES"]:
                    continue
                if instrument_type.endswith("NAV"):
                    self.stdout.write(f"⏭️ Skipping NAV instrument: {instrument['tradingsymbol']}")
                    continue

                try:
                    obj, created = InstrumentDetails.objects.update_or_create(
                        instrument_token=instrument["instrument_token"],
                        defaults={
                            "exchange_token": instrument["exchange_token"],
                            "tradingsymbol": instrument["tradingsymbol"],
                            "name": instrument["name"],
                            "last_price": float(instrument["last_price"]),
                            "expiry": datetime.strptime(instrument["expiry"], "%Y-%m-%d").date() if instrument["expiry"] else None,
                            "strike": float(instrument["strike"]),
                            "tick_size": float(instrument["tick_size"]),
                            "lot_size": int(instrument["lot_size"]),
                            "instrument_type": instrument["instrument_type"],
                            "segment": instrument["segment"],
                            "exchange": instrument["exchange"],
                        }
                    )
                    csv_writer.writerow([
                        instrument["instrument_token"], instrument["exchange_token"], instrument["tradingsymbol"],
                        instrument["name"], instrument["last_price"], instrument["expiry"], instrument["strike"],
                        instrument["tick_size"], instrument["lot_size"], instrument["instrument_type"],
                        instrument["segment"], instrument["exchange"]
                    ])

                    status = "🆕 Created" if created else "♻️ Updated"
                    self.stdout.write(f"{status}: {obj.tradingsymbol}")

                    self.update_historical_data(obj, timing_writer, kite, start_date, end_date, options['interval'])
                    count += 1

                    time.sleep(0.35)

                except Exception as e:
                    self.stderr.write(f"❌ Error processing {instrument['tradingsymbol']}: {str(e)}")

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

    def update_historical_data(self, instrument_obj, timing_writer, kite, start_date, end_date, interval):
        start_time = time.time()

        try:
            # Fetch historical data using KiteConnect
            historical_data = kite.historical_data(
                instrument_token=instrument_obj.instrument_token,
                from_date=start_date,
                to_date=end_date,
                interval=interval
            )

            for candle in historical_data:
                timestamp = candle['date']
                HistoricalOHLC.objects.update_or_create(
                    instrument=instrument_obj,
                    timestamp=timestamp,
                    interval=interval,
                    defaults={
                        "open": candle['open'],
                        "high": candle['high'],
                        "low": candle['low'],
                        "close": candle['close'],
                        "volume": candle['volume'],
                    }
                )

            if historical_data:
                self.stdout.write(f"📊 {instrument_obj.tradingsymbol}: {len(historical_data)} OHLC entries saved")
            else:
                self.stderr.write(f"⚠️ No data for {instrument_obj.tradingsymbol} in the specified date range")

            duration = time.time() - start_time
            timing_writer.writerow([instrument_obj.tradingsymbol, instrument_obj.instrument_token, round(duration, 2), ""])

        except Exception as e:
            duration = time.time() - start_time
            timing_writer.writerow([instrument_obj.tradingsymbol, instrument_obj.instrument_token, "ERROR", str(e)])
            self.stderr.write(f"🚨 Error fetching historical for {instrument_obj.tradingsymbol}: {str(e)}")

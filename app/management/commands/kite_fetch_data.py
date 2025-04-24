from kiteconnect import KiteConnect
# for access token
# https://kite.zerodha.com/connect/login?v=3&api_key=xxx



from django.core.management.base import BaseCommand
from kiteconnect import KiteConnect
import requests
import csv
from app.models import KiteToken
class Command(BaseCommand):
    help = "Fetch user profile and balance from Zerodha Kite"

    def handle(self, *args, **kwargs):
        try:
            api_key = "doieti8s40hlpp6l"
            token = KiteToken.objects.latest('created_at')  # Get the most recent token
            kite = KiteConnect(api_key=api_key)
            kite.set_access_token(token.access_token)
            # ======================================== working code  ===============================================
            headers = {
                'X-Kite-Version': '3',
                'Authorization': f'token {api_key}:{token.access_token}'
            }
            instrument_token = 186537988  # Example token
            interval = "day"
            from_time = "2025-04-21"
            to_time = "2025-04-22"

            url = f"https://api.kite.trade/instruments/historical/{instrument_token}/{interval}"
            params = {
                "from": from_time,
                "to": to_time,
            }

            headers = {
                "X-Kite-Version": "3",
                "Authorization": f"token {api_key}:{token.access_token}"
            }

            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                data = response.json()
                print("✅ Historical Data:",data)
                for candle in data.get("data", {}).get("candles", []):
                    print(candle)
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
            # # ✅ Download instruments
            # response = requests.get('https://api.kite.trade/instruments', headers=headers)
            # response.raise_for_status()

            # # Save full CSV
            # with open('instruments_full.csv', 'w') as f:
            #     f.write(response.text)

            # # Extract selected columns
            # with open('instruments_full.csv', 'r') as infile, open('instrument_tokens_new.csv', 'w', newline='') as outfile:
            #     reader = csv.DictReader(infile)
            #     writer = csv.DictWriter(outfile, fieldnames=['instrument_token', 'tradingsymbol', 'exchange'])
            #     writer.writeheader()
            #     for row in reader:
            #         writer.writerow({
            #             'instrument_token': row['instrument_token'],
            #             'tradingsymbol': row['tradingsymbol'],
            #             'exchange': row['exchange']
            #         })
            #  ===================================== end here ================================================
            # Step 2: Prepare instruments to fetch LTP for
            # instruments = ["NSE:INFY", "BSE:SENSEX", "NSE:NIFTY 50"]
            # params = [("i", i) for i in instruments]

            # # Step 3: Prepare API headers with access token
            # headers = {
            #     "X-Kite-Version": "3",
            #     "Authorization": f"token {api_key}:{token.access_token}"
            # }

            # # Step 4: Make the LTP API call
            # response = requests.get("https://api.kite.trade/quote/ltp", headers=headers, params=params)
            # data = response.json()

            # # Step 5: Handle response
            # if data.get("status") == "success":
            #     with open("ltp_data.csv", mode="w", newline="") as csvfile:
            #         fieldnames = ["instrument", "instrument_token", "last_price"]
            #         writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            #         writer.writeheader()

            #         for instrument, details in data["data"].items():
            #             writer.writerow({
            #                 "instrument": instrument,
            #                 "instrument_token": details["instrument_token"],
            #                 "last_price": details["last_price"]
            #             })

            #     self.stdout.write(self.style.SUCCESS("✅ LTP data saved to ltp_data.csv"))
            # else:
            #     self.stderr.write(f"❌ Failed to fetch LTP: {data}")
        except Exception as e:
            self.stderr.write(f"Error: {e}")

from kiteconnect import KiteConnect

# Replace with your API key and secret from Zerodha developer console
# api_key = "t0zjktzp454kxkzt"
# api_secret = "aki7m034o2ud5swopbw0g88muoq0ifjt"

# # You must generate this manually after logging in via the Kite login flow
# # Get the request_token from the redirect URL after logging in
# request_token = "uUsJFZhskY2egXvTZl0yUJ0jA6qLQjTI"

# kite = KiteConnect(api_key=api_key)

# try:
#     # Generate access token
#     data = kite.generate_session(request_token, api_secret=api_secret)
#     access_token = data["access_token"]
#     kite.set_access_token(access_token)

#     # Get user profile info
#     user_profile = kite.profile()
#     print("User Profile Information:")
#     print("User ID:", user_profile['user_id'])
#     print("User Name:", user_profile['user_name'])
#     print("Email:", user_profile['email'])
#     print("User Type:", user_profile['user_type'])
#     print("Broker:", user_profile['broker'])
#     margins = kite.margins("equity")  # or use "commodity" for commodity segment
#     print("\nUser Balance (Equity):")
#     print("Available Cash:", margins['available']['cash'])
#     print("Available Intraday Margin:", margins['available']['intraday_payin'])
#     print("Used Margin:", margins['utilised']['debits'])

# except Exception as e:
#     print("Error:", e)


# for access token
# https://kite.zerodha.com/connect/login?v=3&api_key=xxx



from django.core.management.base import BaseCommand
from kiteconnect import KiteConnect
import requests
import csv
class Command(BaseCommand):
    help = "Fetch user profile and balance from Zerodha Kite"

    def handle(self, *args, **kwargs):
        api_key = "t0zjktzp454kxkzt"
        api_secret = "aki7m034o2ud5swopbw0g88muoq0ifjt"
        request_token = "9G2mC1TiLfidRAv0x597JbyBb7RjY0De"

        kite = KiteConnect(api_key=api_key)

        try:
            data = kite.generate_session(request_token, api_secret=api_secret)
            access_token = data["access_token"]
            kite.set_access_token(access_token)

            # user_profile = kite.profile()
            # self.stdout.write("User Profile Information:")
            # self.stdout.write(f"User ID: {user_profile['user_id']}")
            # self.stdout.write(f"User Name: {user_profile['user_name']}")
            # self.stdout.write(f"Email: {user_profile['email']}")
            # self.stdout.write(f"User Type: {user_profile['user_type']}")
            # self.stdout.write(f"Broker: {user_profile['broker']}")

            # margins = kite.margins("equity")
            # self.stdout.write("\nUser Balance (Equity):")
            # self.stdout.write(f"Available Cash: {margins['available']['cash']}")
            # self.stdout.write(f"Available Intraday Margin: {margins['available']['intraday_payin']}")
            # self.stdout.write(f"Used Margin: {margins['utilised']['debits']}")
            # instruments = kite.instruments("NFO")


            # # Filter for NIFTY options
            # nifty_options = [i for i in instruments if i['segment'] == 'NFO-OPT' and i['name'] == 'NIFTY']

            # # Step 1: List available expiry dates
            # expiries = sorted(set(i['expiry'] for i in nifty_options))
            # print("Available Expiry Dates for NIFTY:")
            # for e in expiries:
            #     print(e)

            # # Pick one expiry to explore
            # selected_expiry = expiries[0]  # or choose any from the printed list

            # # Step 2: List strikes available for that expiry
            # available_strikes = sorted(set(i['strike'] for i in nifty_options if i['expiry'] == selected_expiry))
            # print(f"\nAvailable Strikes for Expiry {selected_expiry}:")
            # print(available_strikes)

            # # Step 3 (Optional): Pick strike + type and get LTP
            # strike = available_strikes[len(available_strikes) // 2]  # Mid strike
            # option_type = "CE"

            # filtered = [
            #     i for i in nifty_options
            #     if i['expiry'] == selected_expiry and
            #     i['strike'] == strike and
            #     i['instrument_type'] == option_type
            # ]

            # if filtered:
            #     token = filtered[0]['instrument_token']
            #     ltp = kite.ltp([token])
            #     print(f"\nLTP for NIFTY {strike}{option_type} ({selected_expiry}):", ltp[str(token)]['last_price'])
            # else:
            #     print("Option not found.")


            # ======================================== working code  ===============================================
            # headers = {
            #     'X-Kite-Version': '3',
            #     'Authorization': f'token {api_key}:{request_token}'
            # }

            # response = requests.get('https://api.kite.trade/instruments', headers=headers)
            # response.raise_for_status()

            # # Save full CSV
            # with open('instruments_full.csv', 'w') as f:
            #     f.write(response.text)

            # # Optional: Extract only selected columns into a new CSV
            # with open('instruments_full.csv', 'r') as infile, open('instrument_tokens.csv', 'w', newline='') as outfile:
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

            instruments = ["NSE:INFY", "BSE:SENSEX", "NSE:NIFTY 50"]

            # Prepare query parameters
            params = [("i", i) for i in instruments]

            # API headers
            headers = {
                "X-Kite-Version": "3",
                "Authorization": f"token {api_key}:{request_token}"
            }

            # Make API request
            response = requests.get("https://api.kite.trade/quote/ltp", headers=headers, params=params)
            data = response.json()

            # Check for success and write to CSV
            if data.get("status") == "success":
                with open("ltp_data.csv", mode="w", newline="") as csvfile:
                    fieldnames = ["instrument", "instrument_token", "last_price"]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    for instrument, details in data["data"].items():
                        writer.writerow({
                            "instrument": instrument,
                            "instrument_token": details["instrument_token"],
                            "last_price": details["last_price"]
                        })
                print("✅ LTP data saved to ltp_data.csv")
            else:
                print("❌ Failed to fetch data:", data)
        except Exception as e:
            self.stderr.write(f"Error: {e}")
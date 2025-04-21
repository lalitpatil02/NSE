from kiteconnect import KiteConnect
from .models import KiteToken

def save_kite_token(request_token):
    kite = KiteConnect(api_key="t0zjktzp454kxkzt")
    data = kite.generate_session(request_token, api_secret="aki7m034o2ud5swopbw0g88muoq0ifjt")

    token = KiteToken.objects.create(
        access_token=data["access_token"],
        public_token=data.get("public_token"),
        request_token=request_token,
    )
    return token
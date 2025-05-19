from django.http import JsonResponse
from app.models import InstrumentDetails
from kiteconnect import KiteConnect
from app.models import KiteToken

def live_stock_data_api(request, symbol):
    try:
        # Get token
        kite_token = KiteToken.objects.latest('created_at')
        kite = KiteConnect(api_key="doieti8s40hlpp6l")
        kite.set_access_token(kite_token.access_token)

        # Get stock instrument
        stock = InstrumentDetails.objects.filter(tradingsymbol=symbol).first()
        if not stock:
            return JsonResponse({"error": "Symbol not found"}, status=404)

        # Get live quote
        quote = kite.ltp(f"{stock.exchange}:{stock.tradingsymbol}")
        quote_data = quote.get(f"{stock.exchange}:{stock.tradingsymbol}", {})

        return JsonResponse({
            "price": quote_data.get("last_price", 0),
            "volume": quote_data.get("volume_traded", 0),
            "change_pct": quote_data.get("net_change", 0),
            "marketcap": stock.instrument_token
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
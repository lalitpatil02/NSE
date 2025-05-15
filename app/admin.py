from django.contrib import admin
from .models import InstrumentDetails, HistoricalOHLC, KiteToken

@admin.register(HistoricalOHLC)
class HistoricalOHLCAdmin(admin.ModelAdmin):
    list_display = ("instrument", "timestamp", "open", "high", "low", "close", "volume", "interval", "created_at")
    list_filter = ("interval", "timestamp", "instrument__segment")
    search_fields = ("instrument__tradingsymbol",)

@admin.register(InstrumentDetails)
class InstrumentDetailsAdmin(admin.ModelAdmin):
    list_display = ("tradingsymbol", "exchange", "timestamp")
    search_fields = ("tradingsymbol",)
    list_filter = ( "exchange", "segment")

admin.site.register(KiteToken)
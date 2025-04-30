from django.contrib import admin
from .models import InstrumentDetails, HistoricalOHLC

@admin.register(HistoricalOHLC)
class HistoricalOHLCAdmin(admin.ModelAdmin):
    list_display = ("instrument", "timestamp", "open", "high", "low", "close", "volume", "interval")
    list_filter = ("interval", "timestamp")
    search_fields = ("instrument__tradingsymbol",)

@admin.register(InstrumentDetails)
class InstrumentDetailsAdmin(admin.ModelAdmin):
    list_display = ("tradingsymbol", "exchange", "timestamp")
    search_fields = ("tradingsymbol",)

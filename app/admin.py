from django.contrib import admin

# Register your models here.
from .models import CorporateFiling, KiteToken, InstrumentDetails

admin.site.register(CorporateFiling)
admin.site.register(KiteToken)


class Instrument_DetailsAdmin(admin.ModelAdmin):
    list_display = ['instrument_token', 'exchange_token', 'tradingsymbol', 'name', 'segment', 'open', 'interval', 'timestamp']
    list_filter = ['segment']
admin.site.register(InstrumentDetails, Instrument_DetailsAdmin)

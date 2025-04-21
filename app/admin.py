from django.contrib import admin

# Register your models here.
from .models import CorporateFiling, KiteToken

admin.site.register(CorporateFiling)
admin.site.register(KiteToken)
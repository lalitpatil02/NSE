from django.db import models
from django.utils import timezone

class CorporateFiling(models.Model):
    symbol = models.CharField(max_length=20)
    company_name = models.CharField(max_length=200)
    subject = models.TextField()
    filing_date = models.DateField()
    filing_type = models.CharField(max_length=100)
    pdf_link = models.URLField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    details = models.TextField()
    source = models.CharField(max_length=100, null=True, blank=True)
    category = models.CharField(max_length=100, null=True, blank=True)
    AMC_scheme_name= models.CharField(max_length=100, null=True, blank=True)
    broadcast_date = models.DateTimeField(null=True,blank=True)
    receipt_date =  models.DateTimeField(null=True,blank=True)
    dissemination = models.DateTimeField(null=True,blank=True)
    difference = models.TimeField(null=True,blank=True)

    
    class Meta:
        ordering = ['-filing_date']
        indexes = [
            models.Index(fields=['symbol']),
            models.Index(fields=['filing_date']),
        ]

    def __str__(self):
        return f"{self.symbol} - {self.subject[:50]}"


class KiteToken(models.Model):
    access_token = models.CharField(max_length=200)
    public_token = models.CharField(max_length=200, blank=True, null=True)
    request_token = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"KiteToken (created: {self.created_at})"
    

class InstrumentDetails(models.Model):
    instrument_token = models.BigIntegerField()
    exchange_token = models.BigIntegerField()
    tradingsymbol = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    last_price = models.FloatField()
    expiry = models.DateField(null=True, blank=True)
    strike = models.FloatField()
    tick_size = models.FloatField()
    lot_size = models.IntegerField()
    instrument_type = models.CharField(max_length=200)
    segment = models.CharField(max_length=200)
    exchange = models.CharField(max_length=200)
    open = models.FloatField(null=True, blank=True)
    high = models.FloatField(null=True, blank=True)
    low = models.FloatField(null=True, blank=True)
    close = models.FloatField(null=True, blank=True)
    interval = models.CharField(max_length=200, null=True, blank=True)
    timestamp = models.DateTimeField(null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True)

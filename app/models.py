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
    tradingsymbol = models.CharField(max_length=200, unique=True)
    name = models.CharField(max_length=200)
    last_price = models.FloatField()
    expiry = models.DateField(null=True, blank=True)
    strike = models.FloatField()
    tick_size = models.FloatField()
    lot_size = models.IntegerField()
    instrument_type = models.CharField(max_length=200)
    segment = models.CharField(max_length=200)
    exchange = models.CharField(max_length=200)
    timestamp = models.DateTimeField(null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_price']
        indexes = [
            models.Index(fields=['tradingsymbol']),
            models.Index(fields=['last_price']),
        ]

    def __str__(self):
        return f"{self.tradingsymbol} - {self.name}"


class HistoricalOHLC(models.Model):
    instrument = models.ForeignKey(InstrumentDetails, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    volume = models.BigIntegerField()
    interval = models.CharField(max_length=50, default="day")  # can also be '5minute', '15minute', etc.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("instrument", "timestamp", "interval")
        ordering = ["-timestamp"]

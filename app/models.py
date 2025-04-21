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
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

    class Meta:
        ordering = ['-filing_date']
        indexes = [
            models.Index(fields=['symbol']),
            models.Index(fields=['filing_date']),
        ]

    def __str__(self):
        return f"{self.symbol} - {self.subject[:50]}"

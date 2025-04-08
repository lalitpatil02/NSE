from django.db import models

class CorporateFiling(models.Model):
    company_name = models.CharField(max_length=255)
    symbol = models.CharField(max_length=50)
    subject = models.TextField()
    announcement_date = models.DateField()
    details = models.TextField(blank=True, null=True)
    broadcast_datetime = models.DateTimeField(blank=True, null=True)
    receipt_datetime = models.DateTimeField(blank=True, null=True)
    dissemination_datetime = models.DateTimeField(blank=True, null=True)
    difference = models.CharField(max_length=50, blank=True, null=True)
    attachment_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.symbol} - {self.subject[:30]}"

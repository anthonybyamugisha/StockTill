from django.db import models


class BusinessSettingsModel(models.Model):
    key = models.CharField(max_length=50, primary_key=True, default="main")
    business_name = models.CharField(max_length=200, default="")
    address = models.TextField(blank=True, default="")
    phone = models.CharField(max_length=50, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    currency = models.CharField(max_length=3, default="UGX")
    receipt_header = models.TextField(blank=True, default="")
    receipt_footer = models.TextField(blank=True, default="")
    cashier_discount_limit = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    logo_url = models.URLField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "settings_business"

import uuid

from django.db import models


class PaymentIntentModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tx_ref = models.CharField(max_length=64, unique=True, db_index=True)
    idempotency_key = models.CharField(max_length=100, unique=True)
    cashier_id = models.UUIDField(db_index=True)
    shift_id = models.UUIDField(null=True, blank=True)
    method = models.CharField(max_length=30)
    network = models.CharField(max_length=30, blank=True, default="")
    phone = models.CharField(max_length=30, blank=True, default="")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, default="UGX")
    status = models.CharField(max_length=30, default="pending", db_index=True)
    provider = models.CharField(max_length=50, blank=True, default="")
    gateway_reference = models.CharField(max_length=120, null=True, blank=True, db_index=True)
    checkout_url = models.TextField(blank=True, default="")
    failure_reason = models.TextField(blank=True, default="")
    sale_id = models.UUIDField(null=True, blank=True, db_index=True)
    sale_payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        db_table = "payments_intent"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "gateway_reference"],
                name="uniq_payments_provider_gateway_reference",
            )
        ]

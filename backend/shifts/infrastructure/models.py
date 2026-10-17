import uuid

from django.db import models


class ShiftModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cashier_id = models.UUIDField(db_index=True)
    status = models.CharField(max_length=20, default="open", db_index=True)
    opening_float = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    counted_cash = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True, default="")
    opened_at = models.DateTimeField(auto_now_add=True, db_index=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "shifts_shift"
        ordering = ["-opened_at"]


class CashMovementModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shift = models.ForeignKey(ShiftModel, on_delete=models.CASCADE, related_name="cash_movements")
    type = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    reason = models.TextField(blank=True, default="")
    user_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "shifts_cash_movement"
        ordering = ["created_at"]

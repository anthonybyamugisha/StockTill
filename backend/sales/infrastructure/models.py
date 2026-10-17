import uuid

from django.db import models


class SaleModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    receipt_number = models.CharField(max_length=50, unique=True, db_index=True)
    cashier_id = models.UUIDField(db_index=True)
    shift_id = models.UUIDField(db_index=True, null=True, blank=True)
    status = models.CharField(max_length=30, default="completed", db_index=True)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_discount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    notes = models.TextField(blank=True, default="")
    idempotency_key = models.CharField(max_length=100, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "sales_sale"
        ordering = ["-created_at"]


class SaleLineModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sale = models.ForeignKey(SaleModel, on_delete=models.CASCADE, related_name="lines")
    product_id = models.UUIDField(db_index=True)
    product_name = models.CharField(max_length=300)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=14, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=14, decimal_places=2)
    discount_type = models.CharField(max_length=20, null=True, blank=True)
    discount_value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        db_table = "sales_sale_line"


class PaymentModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sale = models.ForeignKey(SaleModel, on_delete=models.CASCADE, related_name="payments")
    method = models.CharField(max_length=30)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    tendered = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    change = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    reference = models.CharField(max_length=200, null=True, blank=True)
    provider = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = "sales_payment"


class RefundModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sale = models.ForeignKey(SaleModel, on_delete=models.CASCADE, related_name="refunds")
    line_id = models.UUIDField(null=True, blank=True)
    quantity = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    reason = models.TextField()
    restock = models.BooleanField(default=False)
    user_id = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "sales_refund"

import uuid

from django.db import models


class SupplierModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=300, db_index=True)
    contact_name = models.CharField(max_length=300, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=50, blank=True, default="")
    address = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "purchasing_supplier"
        ordering = ["name"]


class PurchaseOrderModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier = models.ForeignKey(
        SupplierModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="purchase_orders",
    )
    supplier_name = models.CharField(max_length=300, blank=True, default="")
    status = models.CharField(max_length=20, default="draft", db_index=True)
    reference = models.CharField(max_length=100, blank=True, default="")
    notes = models.TextField(blank=True, default="")
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    ordered_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "purchasing_purchase_order"
        ordering = ["-created_at"]


class PurchaseOrderLineModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    purchase_order = models.ForeignKey(
        PurchaseOrderModel, on_delete=models.CASCADE, related_name="lines"
    )
    product_id = models.UUIDField(db_index=True)
    product_name = models.CharField(max_length=300, blank=True, default="")
    quantity = models.PositiveIntegerField()
    unit_cost = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        db_table = "purchasing_purchase_order_line"


class SupplierInvoiceModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier = models.ForeignKey(
        SupplierModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoices",
    )
    supplier_name = models.CharField(max_length=300, blank=True, default="")
    invoice_number = models.CharField(max_length=100, db_index=True)
    invoice_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    purchase_order = models.ForeignKey(
        PurchaseOrderModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoices",
    )
    status = models.CharField(max_length=20, default="unpaid", db_index=True)
    notes = models.TextField(blank=True, default="")
    amount_paid = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "purchasing_supplier_invoice"
        ordering = ["-invoice_date", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["supplier", "invoice_number"],
                name="unique_supplier_invoice_number",
            )
        ]


class SupplierInvoiceLineModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(
        SupplierInvoiceModel, on_delete=models.CASCADE, related_name="lines"
    )
    product_id = models.UUIDField(null=True, blank=True, db_index=True)
    product_name = models.CharField(max_length=300, blank=True, default="")
    description = models.CharField(max_length=500, blank=True, default="")
    quantity = models.PositiveIntegerField()
    unit_cost = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        db_table = "purchasing_supplier_invoice_line"

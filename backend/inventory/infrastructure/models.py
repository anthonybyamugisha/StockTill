import uuid

from django.db import models


class StockMovementModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_id = models.UUIDField(db_index=True)
    quantity = models.IntegerField()
    movement_type = models.CharField(max_length=30, db_index=True)
    reason = models.TextField()
    reference = models.CharField(max_length=100, null=True, blank=True)
    unit_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    user_id = models.UUIDField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "inventory_stock_movement"
        ordering = ["-timestamp"]


class StockItemModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_id = models.UUIDField(unique=True, db_index=True)
    quantity_on_hand = models.IntegerField(default=0)
    reserved_quantity = models.IntegerField(default=0)
    last_movement_id = models.UUIDField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inventory_stock_item"
        constraints = [
            models.CheckConstraint(
                check=models.Q(quantity_on_hand__gte=0),
                name="stock_non_negative",
            ),
        ]

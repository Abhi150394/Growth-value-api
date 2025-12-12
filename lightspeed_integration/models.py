from django.db import models
from django.utils import timezone


class LightspeedOrder(models.Model):
    """
    Store Lightspeed orders in local database.
    Uses Lightspeed order ID as primary key to prevent duplicates.
    """
    # Primary key is the Lightspeed order ID
    id = models.BigIntegerField(primary_key=True, help_text="Lightspeed order ID")
    
    # Order dates
    delivery_date = models.DateTimeField(null=True, blank=True, help_text="Order delivery date")
    creation_date = models.DateTimeField(null=True, blank=True, help_text="Order creation date")
    
    # Order details
    type = models.CharField(max_length=50, null=True, blank=True, help_text="Order type (e.g., delivery)")
    receipt_id = models.BigIntegerField(null=True, blank=True, help_text="Receipt ID")
    link_to_open_receipt_on_table = models.BooleanField(default=False)
    status = models.CharField(max_length=50, null=True, blank=True, help_text="Order status (e.g., PROCESSED)")
    
    # Order relationships
    table_id = models.BigIntegerField(null=True, blank=True, help_text="Table ID")
    customer_id = models.BigIntegerField(null=True, blank=True, help_text="Customer ID")
    external_reference = models.CharField(max_length=255, null=True, blank=True, help_text="External reference")
    
    # Order content (stored as JSON)
    order_items = models.JSONField(default=list, blank=True, help_text="Order items array")
    order_payments = models.JSONField(default=list, blank=True, help_text="Order payments array")
    order_tax_info = models.JSONField(default=list, blank=True, help_text="Order tax info array")
    raw_data = models.JSONField(default=dict, blank=True, help_text="Full raw order payload from Lightspeed")
    
    # Additional fields
    note = models.TextField(null=True, blank=True, help_text="Order notes")
    number_of_customers = models.IntegerField(default=0, help_text="Number of customers")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, help_text="When this record was created in our DB")
    updated_at = models.DateTimeField(auto_now=True, help_text="When this record was last updated in our DB")
    
    class Meta:
        db_table = 'lightspeed_orders'
        ordering = ['-creation_date', '-id']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['customer_id']),
            models.Index(fields=['creation_date']),
            models.Index(fields=['type']),
        ]
    
    def __str__(self):
        return f"Lightspeed Order #{self.id} - {self.status}"

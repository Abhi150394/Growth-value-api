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
    
    # Location field with default value
    location = models.CharField(max_length=100, default="Dendermonde", help_text="Order location")
    
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
            models.Index(fields=['location']),
        ]
    
    def __str__(self):
        return f"Lightspeed Order #{self.id} - {self.status}"


class LightspeedProduct(models.Model):
    """
    Store Lightspeed products in local database.
    Uses Lightspeed product ID as primary key to prevent duplicates.
    """
    # Primary key is the Lightspeed product ID
    id = models.BigIntegerField(primary_key=True, help_text="Lightspeed product ID")
    
    # Basic product information
    name = models.CharField(max_length=255, null=True, blank=True, help_text="Product name")
    visible = models.BooleanField(default=True, help_text="Whether product is visible")
    
    # Image locations
    image_location = models.CharField(max_length=500, null=True, blank=True, help_text="Image location URL")
    kitchen_image_location = models.CharField(max_length=500, null=True, blank=True, help_text="Kitchen image location URL")
    cfd_image_location = models.CharField(max_length=500, null=True, blank=True, help_text="CFD image location URL")
    
    # Pricing information
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Product price")
    price_without_vat = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Price without VAT")
    takeaway_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Takeaway price")
    takeaway_price_without_vat = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Takeaway price without VAT")
    delivery_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Delivery price")
    delivery_price_without_vat = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Delivery price without VAT")
    
    # Product details
    product_type = models.CharField(max_length=100, null=True, blank=True, help_text="Product type")
    sku = models.CharField(max_length=100, null=True, blank=True, help_text="SKU code")
    
    # Tax information
    tax_class = models.CharField(max_length=100, null=True, blank=True, help_text="Tax class")
    delivery_tax_class = models.CharField(max_length=100, null=True, blank=True, help_text="Delivery tax class")
    takeaway_tax_class = models.CharField(max_length=100, null=True, blank=True, help_text="Takeaway tax class")
    
    # Stock information
    stock_amount = models.IntegerField(default=0, help_text="Stock amount")
    stock_management_enabled = models.BooleanField(default=False, help_text="Whether stock management is enabled")
    
    # Product relationships and content (stored as JSON)
    group_ids = models.JSONField(default=list, blank=True, help_text="Product group IDs array")
    additions = models.JSONField(default=list, blank=True, help_text="Product additions array")
    raw_data = models.JSONField(default=dict, blank=True, help_text="Full raw product payload from Lightspeed")
    
    # Additional fields
    info = models.TextField(null=True, blank=True, help_text="Product information/description")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, help_text="When this record was created in our DB")
    updated_at = models.DateTimeField(auto_now=True, help_text="When this record was last updated in our DB")
    
    class Meta:
        db_table = 'lightspeed_products'
        ordering = ['-created_at', '-id']
        indexes = [
            models.Index(fields=['visible']),
            models.Index(fields=['sku']),
            models.Index(fields=['product_type']),
            models.Index(fields=['stock_management_enabled']),
        ]
    
    def __str__(self):
        return f"Lightspeed Product #{self.id} - {self.name or 'Unnamed'}"

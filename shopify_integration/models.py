from django.db import models
from django.utils import timezone
from decimal import Decimal


class ShopifyOrder(models.Model):
    """
    Store Shopify orders in local database.
    Uses Shopify order ID as primary key to prevent duplicates.
    """
    # Primary key is the Shopify order ID
    id = models.BigIntegerField(primary_key=True, help_text="Shopify order ID")
    
    # Order basic information
    app_id = models.BigIntegerField(null=True, blank=True, help_text="App ID")
    buyer_accepts_marketing = models.BooleanField(default=False, help_text="Buyer accepts marketing")
    cancel_reason = models.CharField(max_length=255, null=True, blank=True, help_text="Cancel reason")
    cancelled_at = models.DateTimeField(null=True, blank=True, help_text="Cancelled at")
    closed_at = models.DateTimeField(null=True, blank=True, help_text="Closed at")
    confirmation_number = models.CharField(max_length=100, null=True, blank=True, help_text="Confirmation number")
    confirmed = models.BooleanField(default=False, help_text="Order confirmed")
    contact_email = models.EmailField(null=True, blank=True, help_text="Contact email")
    currency = models.CharField(max_length=10, null=True, blank=True, help_text="Currency code")
    customer_locale = models.CharField(max_length=20, null=True, blank=True, help_text="Customer locale")
    device_id = models.BigIntegerField(null=True, blank=True, help_text="Device ID")
    duties_included = models.BooleanField(default=False, help_text="Duties included")
    email = models.EmailField(null=True, blank=True, help_text="Customer email")
    estimated_taxes = models.BooleanField(default=False, help_text="Estimated taxes")
    financial_status = models.CharField(max_length=50, null=True, blank=True, help_text="Financial status")
    fulfillment_status = models.CharField(max_length=50, null=True, blank=True, help_text="Fulfillment status")
    location_id = models.BigIntegerField(null=True, blank=True, help_text="Location ID")
    merchant_business_entity_id = models.CharField(max_length=255, null=True, blank=True, help_text="Merchant business entity ID")
    merchant_of_record_app_id = models.BigIntegerField(null=True, blank=True, help_text="Merchant of record app ID")
    name = models.CharField(max_length=255, null=True, blank=True, help_text="Order name")
    note = models.TextField(null=True, blank=True, help_text="Order note")
    number = models.IntegerField(null=True, blank=True, help_text="Order number")
    order_number = models.IntegerField(null=True, blank=True, help_text="Order number (display)")
    presentment_currency = models.CharField(max_length=10, null=True, blank=True, help_text="Presentment currency")
    processed_at = models.DateTimeField(null=True, blank=True, help_text="Processed at")
    subtotal_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Subtotal price")
    tags = models.CharField(max_length=500, null=True, blank=True, help_text="Order tags")
    tax_exempt = models.BooleanField(default=False, help_text="Tax exempt")
    total_weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Total weight")
    user_id = models.BigIntegerField(null=True, blank=True, help_text="User ID")
    
    # Pricing fields
    current_subtotal_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Current subtotal price")
    current_total_discounts = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Current total discounts")
    current_total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Current total price")
    current_total_tax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Current total tax")
    total_discounts = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Total discounts")
    total_line_items_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Total line items price")
    total_outstanding = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Total outstanding")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Total price")
    total_tax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Total tax")
    total_tip_received = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Total tip received")
    
    # Customer information (extracted from nested customer object)
    customer_id = models.BigIntegerField(null=True, blank=True, help_text="Customer ID")
    customer_email = models.EmailField(null=True, blank=True, help_text="Customer email")
    customer_first_name = models.CharField(max_length=255, null=True, blank=True, help_text="Customer first name")
    customer_last_name = models.CharField(max_length=255, null=True, blank=True, help_text="Customer last name")
    
    # Complex nested data stored as JSON
    billing_address = models.JSONField(default=dict, null=True, blank=True, help_text="Billing address")
    customer_data = models.JSONField(default=dict, blank=True, help_text="Full customer data")
    line_items = models.JSONField(default=list, blank=True, help_text="Line items array")
    shipping_address = models.JSONField(default=dict, blank=True, help_text="Shipping address")
    shipping_lines = models.JSONField(default=list, blank=True, help_text="Shipping lines array")
    discount_codes = models.JSONField(default=list, blank=True, help_text="Discount codes array")
    note_attributes = models.JSONField(default=list, blank=True, help_text="Note attributes array")
    payment_gateway_names = models.JSONField(default=list, blank=True, help_text="Payment gateway names array")
    raw_data = models.JSONField(default=dict, blank=True, help_text="Full raw order payload from Shopify")
    
    # Timestamps from Shopify
    created_at = models.DateTimeField(null=True, blank=True, help_text="Order created at (from Shopify)")
    updated_at = models.DateTimeField(null=True, blank=True, help_text="Order updated at (from Shopify)")
    
    # Local timestamps
    local_created_at = models.DateTimeField(auto_now_add=True, help_text="When this record was created in our DB")
    local_updated_at = models.DateTimeField(auto_now=True, help_text="When this record was last updated in our DB")
    
    class Meta:
        db_table = 'shopify_orders'
        ordering = ['-created_at', '-id']
        indexes = [
            models.Index(fields=['financial_status']),
            models.Index(fields=['fulfillment_status']),
            models.Index(fields=['customer_id']),
            models.Index(fields=['created_at']),
            models.Index(fields=['email']),
            models.Index(fields=['order_number']),
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return f"Shopify Order #{self.id} - {self.name or 'N/A'}"

from django.contrib import admin
from .models import ShopifyOrder


@admin.register(ShopifyOrder)
class ShopifyOrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'order_number',
        'email',
        'financial_status',
        'fulfillment_status',
        'total_price',
        'currency',
        'created_at',
        'local_created_at',
    )
    list_filter = (
        'financial_status',
        'fulfillment_status',
        'currency',
        'confirmed',
        'tax_exempt',
        'created_at',
        'local_created_at',
    )
    search_fields = (
        'id',
        'name',
        'order_number',
        'email',
        'contact_email',
        'customer_email',
        'confirmation_number',
        'note',
    )
    readonly_fields = ('id', 'local_created_at', 'local_updated_at', 'raw_data')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Order Information', {
            'fields': (
                'id', 'name', 'order_number', 'number', 'confirmation_number',
                'confirmed', 'financial_status', 'fulfillment_status'
            )
        }),
        ('Customer Information', {
            'fields': (
                'email', 'contact_email', 'customer_id', 'customer_email',
                'customer_first_name', 'customer_last_name', 'customer_locale'
            )
        }),
        ('Pricing', {
            'fields': (
                'currency', 'presentment_currency',
                'subtotal_price', 'total_line_items_price',
                'total_discounts', 'current_total_discounts',
                'total_tax', 'current_total_tax',
                'total_price', 'current_total_price',
                'current_subtotal_price', 'total_outstanding',
                'total_tip_received', 'total_weight'
            )
        }),
        ('Order Details', {
            'fields': (
                'app_id', 'device_id', 'location_id', 'user_id',
                'merchant_business_entity_id', 'merchant_of_record_app_id',
                'buyer_accepts_marketing', 'duties_included',
                'estimated_taxes', 'tax_exempt',
                'cancel_reason', 'cancelled_at', 'closed_at',
                'processed_at', 'note', 'tags'
            )
        }),
        ('Nested Data', {
            'fields': (
                'billing_address', 'shipping_address',
                'customer_data', 'line_items', 'shipping_lines',
                'discount_codes', 'note_attributes', 'payment_gateway_names'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'local_created_at', 'local_updated_at')
        }),
        ('Metadata', {
            'fields': ('raw_data',),
            'classes': ('collapse',)
        }),
    )

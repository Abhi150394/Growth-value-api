from django.contrib import admin
from .models import LightspeedOrder, LightspeedProduct


@admin.register(LightspeedOrder)
class LightspeedOrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'location',
        'status',
        'type',
        'creation_date',
        'delivery_date',
        'customer_id',
        'external_reference',
        'created_at',
    )
    list_filter = (
        'status',
        'location',
        'type',
        'creation_date',
    )
    search_fields = (
        'id',
        'external_reference',
        'note',
        'customer_id',
    )
    readonly_fields = ('id', 'created_at', 'updated_at', 'raw_data')
    date_hierarchy = 'creation_date'
    
    fieldsets = (
        ('Order Information', {
            'fields': ('id', 'status', 'type', 'receipt_id', 'link_to_open_receipt_on_table')
        }),
        ('Dates', {
            'fields': ('creation_date', 'delivery_date')
        }),
        ('Relationships', {
            'fields': ('customer_id', 'table_id', 'external_reference')
        }),
        ('Order Content', {
            'fields': ('order_items', 'order_payments', 'order_tax_info', 'note', 'number_of_customers')
        }),
        ('Metadata', {
            'fields': ('raw_data', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(LightspeedProduct)
class LightspeedProductAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'sku',
        'visible',
        'price',
        'stock_amount',
        'stock_management_enabled',
        'created_at',
    )
    list_filter = (
        'visible',
        'stock_management_enabled',
        'product_type',
        'created_at',
    )
    search_fields = (
        'id',
        'name',
        'sku',
        'info',
    )
    readonly_fields = ('id', 'created_at', 'updated_at', 'raw_data')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Product Information', {
            'fields': ('id', 'name', 'sku', 'visible', 'product_type')
        }),
        ('Pricing', {
            'fields': (
                'price', 'price_without_vat',
                'takeaway_price', 'takeaway_price_without_vat',
                'delivery_price', 'delivery_price_without_vat'
            )
        }),
        ('Tax Information', {
            'fields': ('tax_class', 'delivery_tax_class', 'takeaway_tax_class')
        }),
        ('Stock', {
            'fields': ('stock_amount', 'stock_management_enabled')
        }),
        ('Images', {
            'fields': ('image_location', 'kitchen_image_location', 'cfd_image_location')
        }),
        ('Product Content', {
            'fields': ('group_ids', 'additions', 'info')
        }),
        ('Metadata', {
            'fields': ('raw_data', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

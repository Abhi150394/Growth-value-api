from django.contrib import admin
from .models import LightspeedOrder


@admin.register(LightspeedOrder)
class LightspeedOrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
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

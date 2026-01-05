from django.contrib import admin
from .models import UserData, Payment, Orders, Searches, Products, Wishlist, Scraper, Tag, Vendor,ShyfterEmployee

# Register your models here.
admin.site.register(UserData)
admin.site.register(Payment)
admin.site.register(Orders)
admin.site.register(Searches)
admin.site.register(Wishlist)
admin.site.register(Scraper)
admin.site.register(Tag)
admin.site.register(Vendor)

class AdminProducts(admin.ModelAdmin):
    search_fields = ("vendor", "brand", "product_name")
    list_display = (
        "product_name",
        "price",
        "relative_price",
        "brand",
        "vendor",
    )
    list_filter=(
        "vendor",
    )

class AdminShyfterEmployee(admin.ModelAdmin):
    search_fields=("location","type")
    list_display=(
        "id",
        "type",
        "email",
        "location",
    )
    list_filter=("location","type")
    
    
admin.site.register(ShyfterEmployee,AdminShyfterEmployee)
admin.site.register(Products, AdminProducts)

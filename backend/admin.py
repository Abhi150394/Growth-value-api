from django.contrib import admin
from .models import UserData, Payment, Orders, Searches, Products, Wishlist, Scraper, Tag, Vendor,ShyfterEmployee,ShyfterEmployeeClocking,ShyfterEmployeeShift

# Register your models here.
admin.site.register(UserData)
admin.site.register(Payment)
admin.site.register(Orders)
admin.site.register(Searches)
admin.site.register(Wishlist)
class AdminScraper(admin.ModelAdmin):
    list_display = (
        "website",
        "scraped",
        "last_scraped",
    )
    
admin.site.register(Scraper,AdminScraper)
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
    search_fields=("location","type","id")
    list_display=(
        "id",
        "type",
        "active",
        "hourly_cost",
        "email",
        "location",
    )
    list_filter=("location","type")
class AdminShyfterEmployeeClocking(admin.ModelAdmin):
    search_fields = (
        "location",
        "employee__email", 
        "id",
        "employee_id"
    )
    list_display = (
        "id",
        "work_date",
        "employee_id",
        "cost",
        "duration_minutes",
        "employee_email",
        "employee_role",  
        "location",
        "employee_active",
    )
    list_filter=("location","employee__type","employee__active","employee__email") 
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related("employee")

    @admin.display(
        description="Employee Email",
        ordering="employee__email"
    )
    def employee_email(self, obj):
        return obj.employee.email if obj.employee else "-"
    @admin.display(
        description="Active",
        ordering="employee__active",
        boolean=True,  
    )
    def employee_active(self, obj):
        return obj.employee.active if obj.employee else False
    
    @admin.display(
        description="Employee Type",
        ordering="employee__type",
    )
    def employee_role(self,obj):
        return obj.employee.type if obj.employee else "-"
        
class AdminShyfterEmployeeShift(admin.ModelAdmin):
    search_fields=("id","location",)
    list_display=("id","employee_id","employee_role","location","duration_minutes","cost","breaks","social_secretary")
    list_filter=("location","employee__type")   
    @admin.display(
        description="Employee Type",
        ordering="employee__type",
    )
    def employee_role(self,obj):
        return obj.employee.type if obj.employee else "-"
    
    
admin.site.register(ShyfterEmployeeShift,AdminShyfterEmployeeShift)
admin.site.register(ShyfterEmployeeClocking,AdminShyfterEmployeeClocking)
admin.site.register(ShyfterEmployee,AdminShyfterEmployee)
admin.site.register(Products, AdminProducts)

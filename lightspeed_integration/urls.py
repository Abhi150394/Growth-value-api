from django.urls import path
from .views import (
    LightspeedAuthView,
    OrdersView,
    OrderDetailView,
    ProductsView,
    ProductDetailView,
    CustomersView,
    ProductSalesView,
    CompanyView,
    CompanyDetailView,
    FinanceReceiptView,
    EmployeeListView,
    EmployeeDetailView,
    EmployeeClocktimeView,
    InventoryProductView,
    InventoryProductGroupView,
    FinanceReceiptActualView,
    LightspeedReceiptFullDumpView
)

urlpatterns = [
    path("auth/", LightspeedAuthView.as_view(), name="lightspeed-auth"),
    path("orders/", OrdersView.as_view(), name="lightspeed-orders"),
    path("orders/<str:order_id>/", OrderDetailView.as_view(), name="lightspeed-order-detail"),
    path("products/", ProductsView.as_view(), name="lightspeed-products"),
    path("products/<str:product_id>/", ProductDetailView.as_view(), name="lightspeed-product-detail"),
    path("customers/", CustomersView.as_view(), name="lightspeed-customers"),
    path("product-sales/", ProductSalesView.as_view(), name="lightspeed-product-sales"),
    path("company/", CompanyView.as_view(), name="lightspeed-company"),
    path("company/<str:company_id>/", CompanyDetailView.as_view(), name="lightspeed-company-detail"),
    path("finance/receipts/", FinanceReceiptView.as_view(), name="lightspeed-finance-receipts"),
    path("finance/actual-receipts/",FinanceReceiptActualView.as_view()),
    path("employees/", EmployeeListView.as_view(), name="lightspeed-employees"),
    path("employees/<str:user_id>/", EmployeeDetailView.as_view(), name="lightspeed-employee-detail"),
    path("employees/clocktime/", EmployeeClocktimeView.as_view(), name="lightspeed-employee-clocktime"),
    path("inventory/products/", InventoryProductView.as_view(), name="lightspeed-inventory-products"),
    path("inventory/productgroups/", InventoryProductGroupView.as_view(), name="lightspeed-inventory-productgroups"),
    path("finance/actual-receipts/dumpdata/",LightspeedReceiptFullDumpView.as_view()),
    
]


from django.urls import path
from . import views

urlpatterns = [
    path("authorize/", views.lightspeed_auth, name="lightspeed_auth"),

    #Orders
    path("orders/", views.get_lightspeed_orders, name="lightspeed_orders"),
    path("orders/<order_id>",views.get_lightspeed_orderById,name="lightspeed_orderById"),

    #
    path("customers/",views.get_lightspeed_customer,name="lightspeed_customers"),

    #Product Sales
    path("productsales/",views.get_lightspeed_productsale,name="lightspeed_productsale"),

    #Company
    path("company/",views.get_lightspeed_company,name="lightspeed_company"),
    path("company/<company_id>",views.get_lightspeed_companyById,name="lightspeed_companyById"),

    #Product
    path("products/",views.get_lightspeed_products,name="lightspeed_product"),
    path("products/<product_id>",views.get_lightspeed_productById,name="lightspeed_productById"),
    path("financeDetails/",views.get_lightspeed_financeReceipt,name="lightspeed_financialReceipt"),
    
    #Labour
    path("employee/",views.get_lightspeed_employeeDetails,name="lightspeed_employees"),
    path("employee/<user_id>",views.get_lightspeed_employeeDetailsById,name="lightspeed_employeesDetilsById"),
    path("employeeClocktime/",views.get_lightspeed_employeeClocktimingDetails,name="lightspeed_employeesClockTime"),

    #Inventory
    path("inventory/product/",views.get_lightspeed_InventoryProductDetails,name="lightspeed_employees"),
    path("inventory/productgroup/",views.get_lightspeed_InventoryProductgroupDetails,name="lightspeed_employees"),


]

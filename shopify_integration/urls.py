from django.urls import path
from . import views

urlpatterns = [
    path('products/', views.products_view, name='shopify_products'),
    path('orders/', views.orders_view, name='shopify_orders'),
    path('customers/', views.customers_view, name='shopify_customers'),
    path('products/<int:product_id>/', views.single_product_view, name='shopify_product_detail'),
    path('routes/',views.all_routes,name='shopify_all_routes'),
    path('reports/',views.reports_view,name='shopify_reports'),
    path('inventory/',views.inventory_view,name='shopify_inventory')

]

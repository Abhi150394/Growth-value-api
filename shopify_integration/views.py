# views.py
from django.http import JsonResponse
from .shopify_api import get_products, get_orders, get_customers, get_single_product,get_routes,get_reports,get_inventory

def products_view(request):
    data = get_products()
    return JsonResponse(data)

def orders_view(request):
    data = get_orders()
    return JsonResponse(data)

def customers_view(request):
    data = get_customers()
    return JsonResponse(data)

def single_product_view(request, product_id):
    data = get_single_product(product_id)
    return JsonResponse(data)

def all_routes(request):
    data=get_routes()
    return JsonResponse(data)

def reports_view(request):
    data=get_reports()
    return JsonResponse(data)

def inventory_view(request):
    data=get_inventory()
    return JsonResponse(data)
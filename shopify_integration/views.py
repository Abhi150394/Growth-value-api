# views.py
from django.http import JsonResponse
from .shopify_api import get_products, get_orders, get_customers, get_single_product, get_routes, get_reports, get_inventory

def products_view(request):
    """Get products from Shopify. Supports location query parameter."""
    location = request.GET.get("location") or "Frietchalet"
    data = get_products(location)
    return JsonResponse(data)

def orders_view(request):
    """Get orders from Shopify. Supports location query parameter."""
    location = request.GET.get("location") or "Frietchalet"
    data = get_orders(location)
    return JsonResponse(data)

def customers_view(request):
    """Get customers from Shopify. Supports location query parameter."""
    location = request.GET.get("location") or "Frietchalet"
    data = get_customers(location)
    return JsonResponse(data)

def single_product_view(request, product_id):
    """Get a single product from Shopify. Supports location query parameter."""
    location = request.GET.get("location") or "Frietchalet"
    data = get_single_product(product_id, location)
    return JsonResponse(data)

def all_routes(request):
    """Get OAuth access scopes from Shopify. Supports location query parameter."""
    location = request.GET.get("location") or "Frietchalet"
    data = get_routes(location)
    return JsonResponse(data)

def reports_view(request):
    """Get shop reports from Shopify. Supports location query parameter."""
    location = request.GET.get("location") or "Frietchalet"
    data = get_reports(location)
    return JsonResponse(data)

def inventory_view(request):
    """Get inventory from Shopify. Supports location query parameter."""
    location = request.GET.get("location") or "Frietchalet"
    data = get_inventory(location)
    return JsonResponse(data)
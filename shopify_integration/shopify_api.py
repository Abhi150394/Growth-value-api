# shopify_api.py
import requests
from django.conf import settings

def _get_shopify_credentials(location="Frietchalet"):
    """
    Get Shopify credentials (store_name, access_token) for a specific location.
    Supports both new location-based structure and old single token structure for backward compatibility.
    
    Args:
        location: Location name (default: "Frietchalet")
    
    Returns:
        tuple: (store_name, access_token)
    """
    # Try to get location-specific credentials (new structure)
    location_creds = getattr(settings, 'SHOPIFY_AUTHORIZATION_CREDENTIALS', {}).get(location)
    
    if location_creds:
        # If it's a dict with store_name and access_token
        if isinstance(location_creds, dict):
            store_name = location_creds.get("store_name") or settings.SHOPIFY_STORE_NAME
            access_token = location_creds.get("access_token")
            if access_token:
                return store_name, access_token
        # If it's just a string (access_token)
        elif isinstance(location_creds, str):
            return settings.SHOPIFY_STORE_NAME, location_creds
    
    # Fallback to old single token structure (backward compatibility)
    return settings.SHOPIFY_STORE_NAME, settings.SHOPIFY_ACCESS_TOKEN

def _get_shopify_headers(location="Frietchalet"):
    """
    Get Shopify headers for a specific location.
    
    Args:
        location: Location name (default: "Frietchalet")
    
    Returns:
        dict: Headers with X-Shopify-Access-Token and Content-Type
    """
    _, access_token = _get_shopify_credentials(location)
    return {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json",
    }

def _get_base_url(location="Frietchalet"):
    """
    Get base URL for Shopify API for a specific location.
    
    Args:
        location: Location name (default: "Frietchalet")
    
    Returns:
        str: Base URL for Shopify API
    """
    store_name, _ = _get_shopify_credentials(location)
    return f"https://{store_name}/admin/api/{settings.SHOPIFY_API_VERSION}"

def get_products(location="Frietchalet"):
    """Get products from Shopify for a specific location."""
    url = f"{_get_base_url(location)}/products.json"
    r = requests.get(url, headers=_get_shopify_headers(location))
    return r.json()

def get_reports(location="Frietchalet"):
    """Get shop reports from Shopify for a specific location."""
    url = f"{_get_base_url(location)}/shop.json"
    r = requests.get(url, headers=_get_shopify_headers(location))
    return r.json()

def get_orders(location="Frietchalet"):
    """Get orders from Shopify for a specific location."""
    url = f"{_get_base_url(location)}/orders.json?limit=250"
    r = requests.get(url, headers=_get_shopify_headers(location))
    return r.json()

def get_customers(location="Frietchalet"):
    """Get customers from Shopify for a specific location."""
    url = f"{_get_base_url(location)}/customers.json"
    r = requests.get(url, headers=_get_shopify_headers(location))
    return r.json()

def get_single_product(product_id, location="Frietchalet"):
    """Get a single product from Shopify for a specific location."""
    url = f"{_get_base_url(location)}/products/{product_id}.json"
    r = requests.get(url, headers=_get_shopify_headers(location))
    return r.json()

def get_routes(location="Frietchalet"):
    """Get OAuth access scopes from Shopify for a specific location."""
    store_name, _ = _get_shopify_credentials(location)
    url = f"https://{store_name}/admin/oauth/access_scopes.json"
    r = requests.get(url, headers=_get_shopify_headers(location))
    return r.json()

def get_inventory(location="Frietchalet"):
    """Get inventory from Shopify for a specific location."""
    url = f"{_get_base_url(location)}/read_inventory.json"
    r = requests.get(url, headers=_get_shopify_headers(location))
    return r.json()
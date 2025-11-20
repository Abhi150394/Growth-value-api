# shopify_api.py
import requests
from django.conf import settings

BASE_URL = f"https://{settings.SHOPIFY_STORE_NAME}/admin/api/{settings.SHOPIFY_API_VERSION}"

HEADERS = {
    "X-Shopify-Access-Token": settings.SHOPIFY_ACCESS_TOKEN,
    "Content-Type": "application/json",
}

def get_products():
    url = f"{BASE_URL}/products.json"
    r = requests.get(url, headers=HEADERS)
    return r.json()

def get_reports():
    url = f"{BASE_URL}/shop.json"
    r = requests.get(url, headers=HEADERS)
    return r.json()

def get_orders():
    url = f"{BASE_URL}/orders.json"
    r = requests.get(url, headers=HEADERS)
    return r.json()

def get_customers():
    url = f"{BASE_URL}/customers.json"
    r = requests.get(url, headers=HEADERS)
    return r.json()

def get_single_product(product_id):
    url = f"{BASE_URL}/products/{product_id}.json"
    r = requests.get(url, headers=HEADERS)
    return r.json()

# def get_locations():/admin/oauth/access_scopes.json
#     url=f"{BASE_URL}/locations.json"
#     r=requests.get(url,)
def get_routes():
    url = f"https://{settings.SHOPIFY_STORE_NAME}/admin/oauth/access_scopes.json"
    r = requests.get(url, headers=HEADERS)
    return r.json()

def get_inventory():
    url= f"{BASE_URL}/read_inventory.json"
    r=requests.get(url,headers=HEADERS)
    return r.json()
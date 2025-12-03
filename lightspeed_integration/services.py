import json
import os
import time
import requests
from .oauth import refresh_access_token
from django.conf import settings
from datetime import datetime, timedelta



# TOKEN_FILE = "lightspeed_tokens.json"
TOKEN_FILE = os.path.join(settings.BASE_DIR, "lightspeed_tokens.json")
BASE_URL = "https://lightspeedapis.com/resto/rest"


def load_token_data():
    """Load full token data (not just access_token)."""
    if not os.path.exists(TOKEN_FILE):
        raise Exception("Token file not found. Run OAuth flow first.")
    with open(TOKEN_FILE, "r") as f:
        return json.load(f)


def get_saved_token():
    """Get access token; refresh automatically if expired."""
    token_data = load_token_data()
    access_token = token_data.get("access_token")
    expires_in = token_data.get("expires_in", 3600)
    issued_at = token_data.get("timestamp", 0)

    # Check if expired (add 30-second safety margin)
    if time.time() - issued_at > expires_in - 30:
        print("🔄 Access token expired — refreshing...")
        token_data = refresh_access_token()
        if not token_data:
            raise Exception("Failed to refresh access token.")
        access_token = token_data.get("access_token")

    return access_token


def lightspeed_get(endpoint, params=None):
    """Authenticated GET request to Lightspeed API (auto refresh)."""
    access_token = get_saved_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }

    url = f"{BASE_URL}/{endpoint.lstrip('/')}"
    print(url,params)
    response = requests.get(url, headers=headers, params=params)

    # Handle expired token during request
    if response.status_code == 401:
        print("⚠️ Token expired mid-request. Refreshing and retrying...")
        refresh_access_token()
        access_token = get_saved_token()
        headers["Authorization"] = f"Bearer {access_token}"
        response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Lightspeed API Error: {response.status_code} - {response.text}")



# def summarize_orders_by_date(orders):
#     result = {}

#     for order in orders:
#         # Extract only YYYY-MM-DD part from ISO Date
#         date_key = order["creationDate"].split("T")[0]

#         if date_key not in result:
#             result[date_key] = {
#                 "totalAmount": 0,
#                 "itemsCount": 0
#             }

#         result[date_key]["totalAmount"] += order.get("total", 0)
#         result[date_key]["itemsCount"] += len(order.get("items", []))

#     return result



def summarize_orders_by_date(orders, from_date, to_date):
    # Convert input strings to date objects if needed
    if isinstance(from_date, str):
        from_date = datetime.strptime(from_date, "%Y-%m-%d").date()
    if isinstance(to_date, str):
        to_date = datetime.strptime(to_date, "%Y-%m-%d").date()

    result = {}

    # ---- Create default structure for entire date range ----
    current = from_date
    while current <= to_date:
        result[str(current)] = {"totalAmount": 0, "itemsCount": 0}
        current += timedelta(days=1)

    # ---- Fill values based on orders ----
    for order in orders:
        date_key = order["creationDate"].split("T")[0]  # "YYYY-MM-DD"

        if date_key in result:
            result[date_key]["totalAmount"] += order.get("total", 0)
            result[date_key]["itemsCount"] += len(order.get("items", []))

    return result

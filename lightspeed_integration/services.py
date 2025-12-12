import json
import os
import time
import requests
from django.conf import settings
from datetime import datetime, timedelta
from lightspeed_integration.oauth import LightspeedAuth


# TOKEN_FILE = "lightspeed_tokens.json"
TOKEN_FILE = os.path.join(settings.BASE_DIR, "lightspeed_tokens.json")
BASE_URL = "https://lightspeedapis.com/resto/rest"

# Create a shared LightspeedAuth instance for token management
_auth_instance = None


def get_auth_instance():
    """Get or create the shared LightspeedAuth instance."""
    global _auth_instance
    if _auth_instance is None:
        _auth_instance = LightspeedAuth()
    return _auth_instance


def load_token_data():
    """Load full token data (not just access_token)."""
    if not os.path.exists(TOKEN_FILE):
        raise Exception("Token file not found. Run OAuth flow first.")
    with open(TOKEN_FILE, "r") as f:
        return json.load(f)


def get_saved_token(location="Frietchalet"):
    """
    Get access token for a specific location; refresh automatically if expired.
    Supports both new location-based structure and old root-level token structure for backward compatibility.
    """
    auth = get_auth_instance()
    all_tokens = load_token_data()
    
    # First, try to get location-specific token (new structure)
    location_token = all_tokens.get(location)
    
    if location_token and isinstance(location_token, dict):
        # New structure: location-based token exists
        # Use LightspeedAuth to get valid token (handles refresh automatically)
        access_token = auth.get_valid_access_token(location)
        if access_token:
            return access_token
    
    # Fallback: check for old root-level token structure (backward compatibility)
    if "access_token" in all_tokens and not isinstance(all_tokens["access_token"], dict):
        # Old structure: root-level token exists
        access_token = all_tokens.get("access_token")
        expires_in = all_tokens.get("expires_in", 3600)
        issued_at = all_tokens.get("timestamp", 0)
        
        # Check if expired (add 30-second safety margin)
        if time.time() - issued_at > expires_in - 30:
            print("🔄 Access token expired — refreshing...")
            # Try to refresh using old refresh_token if available
            refresh_token = all_tokens.get("refresh_token")
            if refresh_token:
                payload = {
                    "grant_type": "refresh_token",
                    "client_id": settings.LIGHTSPEED["CLIENT_ID"],
                    "client_secret": settings.LIGHTSPEED["CLIENT_SECRET"],
                    "refresh_token": refresh_token,
                }
                headers = {"Content-Type": "application/x-www-form-urlencoded"}
                resp = requests.post(settings.LIGHTSPEED["TOKEN_URL"], data=payload, headers=headers)
                
                if resp.status_code == 200:
                    new_token = resp.json()
                    new_token["timestamp"] = int(time.time())
                    # Update only the root-level token fields (preserve location tokens)
                    all_tokens["access_token"] = new_token.get("access_token")
                    all_tokens["refresh_token"] = new_token.get("refresh_token")
                    all_tokens["expires_in"] = new_token.get("expires_in")
                    all_tokens["timestamp"] = new_token.get("timestamp")
                    with open(TOKEN_FILE, "w") as f:
                        json.dump(all_tokens, f, indent=2)
                    access_token = new_token.get("access_token")
                else:
                    raise Exception(f"Failed to refresh access token: {resp.status_code} - {resp.text}")
            else:
                raise Exception("No refresh_token available for old token structure.")
        
        return access_token
    
    # No token found for location or in old structure
    raise Exception(f"No token found for location '{location}' and no fallback token available.")


def lightspeed_get(endpoint, params=None, location="Frietchalet"):
    """
    Authenticated GET request to Lightspeed API (auto refresh).
    
    Args:
        endpoint: API endpoint path (e.g., "onlineordering/order")
        params: Optional query parameters dict
        location: Location name for token selection (default: "Frietchalet")
    """
    access_token = get_saved_token(location)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }

    url = f"{BASE_URL}/{endpoint.lstrip('/')}"
    print(url, params)
    response = requests.get(url, headers=headers, params=params)

    # Handle expired token during request
    if response.status_code == 401:
        print("⚠️ Token expired mid-request. Refreshing and retrying...")
        # Refresh token and retry
        access_token = get_saved_token(location)
        headers["Authorization"] = f"Bearer {access_token}"
        response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Lightspeed API Error: {response.status_code} - {response.text}")

 
 

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


import base64
import hashlib
import os
import re
import json
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from django.conf import settings


def generate_code_verifier_and_challenge():
    verifier = base64.urlsafe_b64encode(os.urandom(40)).rstrip(b'=').decode('utf-8')
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode('utf-8')).digest()
    ).rstrip(b'=').decode('utf-8')
    return verifier, challenge


def get_authorization_code():
    """Simulates login and retrieves the authorization code."""
    verifier, challenge = generate_code_verifier_and_challenge()

    # Step 1: Generate authorization URL
    auth_url = (
        f"{settings.LIGHTSPEED['AUTHORIZE_URL']}"
        f"?response_type=code"
        f"&client_id={settings.LIGHTSPEED['CLIENT_ID']}"
        f"&redirect_uri={settings.LIGHTSPEED['REDIRECT_URI']}"
        f"&code_challenge_method={settings.LIGHTSPEED['CODE_CHALLENGE_METHOD']}"
        f"&code_challenge={challenge}"
    )

    session = requests.Session()
    response = session.get(auth_url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Step 2: Login form
    soup = BeautifulSoup(response.text, "html.parser")
    form = soup.find("form")

    if not form:
        print("❌ No form found on the authorization page.")
        print("🔹 URL:", response.url)
        print("🔹 Status code:", response.status_code)
        print("🔹 Page snippet:")
        print(response.text[:1000])  # show the first 1000 chars
        raise Exception("Lightspeed authorization form not found. Check client_id or redirect_uri.")

    action_url = urljoin(response.url, form.get("action"))
    payload = {i.get("name"): i.get("value", "") for i in form.find_all("input") if i.get("name")}

    payload["userId"] = settings.LIGHTSPEED["LOGIN_ID"]
    payload["password"] = settings.LIGHTSPEED["PASSWORD"]

    login_resp = session.post(action_url, data=payload, allow_redirects=True)
    soup = BeautifulSoup(login_resp.text, "html.parser")

    # Step 3: Consent form
    form = soup.find("form")
    action_url = urljoin(login_resp.url, form.get("action"))
    payload = {i.get("name"): i.get("value", "") for i in form.find_all("input") if i.get("name")}
    payload["consent"] = "true"

    try:
        allow_resp = session.post(action_url, data=payload, allow_redirects=True)
        print("✅ Response URL:", allow_resp.url)
        return None
    except requests.exceptions.ConnectionError as e:
        # Extract code from redirect error (localhost)
        match = re.search(r"[?&]code=([^&\s]+)", str(e))
        if match:
            auth_code = match.group(1)
            print("✅ Authorization code:", auth_code)
            return auth_code, verifier
        else:
            print("❌ Could not extract code.")
            return None, verifier


def exchange_token(auth_code, code_verifier):
    """Exchange authorization code for access token."""
    payload = {
        "grant_type": "authorization_code",
        "client_id": settings.LIGHTSPEED["CLIENT_ID"],
        "client_secret": settings.LIGHTSPEED["CLIENT_SECRET"],
        "redirect_uri": settings.LIGHTSPEED["REDIRECT_URI"],
        "code_verifier": code_verifier,
        "code": auth_code,
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    resp = requests.post(settings.LIGHTSPEED["TOKEN_URL"], data=payload, headers=headers)
    if resp.status_code == 200:
        token_data = resp.json()
        token_data["timestamp"] = int(time.time()) 
        with open(os.path.join(settings.BASE_DIR, "lightspeed_tokens.json"), "w") as f:
            json.dump(token_data, f, indent=2)
        print("✅ Token stored in lightspeed_tokens.json")
        return token_data
    else:
        print("❌ Token request failed:", resp.status_code, resp.text)
        return None


def refresh_access_token():
    """Refresh access token using saved refresh token."""
    try:
        with open(os.path.join(settings.BASE_DIR, "lightspeed_tokens.json"), "r") as f:
            saved = json.load(f)
    except FileNotFoundError:
        print("❌ No saved token file found.")
        return None

    refresh_token = saved.get("refresh_token")
    if not refresh_token:
        print("❌ No refresh_token available.")
        return None

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
        with open(os.path.join(settings.BASE_DIR, "lightspeed_tokens.json"), "w") as f:
            json.dump(new_token, f, indent=2)
        print("✅ Access token refreshed successfully.")
        return new_token
    else:
        print("❌ Refresh failed:", resp.status_code, resp.text)
        return None

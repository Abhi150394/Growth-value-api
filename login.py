import base64
import hashlib
import os
import requests
import json
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin,urlparse, parse_qs


CLIENT_ID='f22f696fcea88edfa6ecaa612cff55d4'
CLIENT_SECERET="69d400fcc219c7acfaa4542bd3c6e3b65731fc0931b14a36ea76723393aebd37",

LIGHTSPEED_LOGIN_ID='Lightspeed@frietchalet.be'
LIGHTSPEED_LOGIN_PASSWORD='Lightspeed1'

REDIRECT_URI='https://localhost'
AUTHORISE_URL='https://lightspeedapis.com/resto/oauth2/v1/authorize'
CODE_CHALLENGE_METHOD = "S256"

#VERIFIERS

# URLS




AUTHORIZATION_TOKEN_URL="https://lightspeedapis.com/resto/oauth2/v1/token"

# LIGHTSPEED_ORDER_DETAIL_URL="https://lightspeedapis.com/resto/rest/onlineordering/order"




# CODE =""




"""
STEP1:
    Genrate the code challenge 

STEP2: 
    USe the light speed url with the updated code challenge.
    --> redirect to the lightspeed login page for the L-Series

STEP3:
    Login Page redirect to the permissoin page for the access confirmation
     ----> redirected to whitelisted redirect urls
    -----> getting the code 

STEP4:
    For the access token 
    use specific url with the code and code verifier.
"""


# STEP1

CODE_VERIFIER = base64.urlsafe_b64encode(os.urandom(40)).rstrip(b'=').decode('utf-8')

CODE_CHALLENGE = base64.urlsafe_b64encode(
    hashlib.sha256(CODE_VERIFIER.encode('utf-8')).digest()
).rstrip(b'=').decode('utf-8')


# STEP2


ACCOUNTS_URL = (
    f"{AUTHORISE_URL}"
    f"?response_type=code"
    f"&client_id={CLIENT_ID}"
    f"&redirect_uri={REDIRECT_URI}"
    f"&code_challenge_method={CODE_CHALLENGE_METHOD}"
    f"&code_challenge={CODE_CHALLENGE}"
)
import pdb
response = requests.get(ACCOUNTS_URL)
print("response", response)


# STEP3

session = requests.Session()
soup = BeautifulSoup(response.text, "html.parser")
form = soup.find("form")
action_url = urljoin(response.url, form.get("action"))

payload = {}
for input_tag in form.find_all("input"):
    name = input_tag.get("name")
    value = input_tag.get("value", "")
    if name:
        payload[name] = value

# fill credentials
payload["userId"] = LIGHTSPEED_LOGIN_ID
payload["password"] = LIGHTSPEED_LOGIN_PASSWORD
login_resp = session.post(action_url, data=payload, allow_redirects=True)

print(login_resp)
# Lightspeed@frietchalet.be
# password
# Lightspeed1
# state
# ht33k0AT2igx1uZ7-UiY4Vnqm1wGtKLUxk_TtejyxLLyelK6bvfnV~zUXJYmG8-U
# client_id
# f22f696fcea88edfa6ecaa612cff55d4
# prompt
# redirect_uri
# https://localhost
# scope
# openid email profile

# Continue using the same session from your previous step
# (the session contains login cookies)
html = login_resp.text  # the page that contains the "Allow" button
soup = BeautifulSoup(html, "html.parser")

# Find the consent/authorization form
form = soup.find("form")
action_url = urljoin(login_resp.url, form.get("action"))

# Extract all inputs
payload = {}
for input_tag in form.find_all("input"):
    name = input_tag.get("name")
    value = input_tag.get("value", "")
    if name:
        payload[name] = value


# (Optional) check which button is "Allow"
allow_button = form.find("button", {"data-testid": "confirm"})
# if allow_button:
#     payload[allow_button["name"]] = allow_button.get("value", "Allow")

# Submit the consent
payload['consent']='true'
# allow_resp = session.post(action_url, data=payload, allow_redirects=True)

try:
    allow_resp = session.post(action_url, data=payload, allow_redirects=True)
    print("✅ Successfully got response:", allow_resp.url)
except requests.exceptions.ConnectionError as e:
    # The exception contains the redirect URL with the ?code= param
    error_message = str(e)
    print("⚠️ Connection failed (expected because localhost has no HTTPS server).")
    print("Raw error message:\n", error_message)

    # Try to extract the code from the error text
    match = re.search(r"[?&]code=([^&\s]+)", error_message)
    if match:
        auth_code = match.group(1)
        print("✅ Extracted authorization code:", auth_code)
    else:
        print("❌ Could not find code in error.")

# print("Status:", allow_resp.status_code)
# print("Redirect URL:", allow_resp.url)

print("Auth code",auth_code)

# parsed = urlparse(allow_resp.url)
# auth_code = parse_qs(parsed.query).get("code", [None])[0]
print("Authorization Code:", auth_code)

# # PAYLOADS
AUTHORIZATION_TOKEN_PAYLOAD={
    "grant_type": "authorization_code",
    "client_id": {CLIENT_ID},
    "client_secret": {CLIENT_SECERET},
    "redirect_uri": "https://localhost",
    "code_verifier": {CODE_VERIFIER}, #which we use to create code challenge
    "code": {auth_code} #the code which you get from redirect url params
}
headers = {
    "Content-Type": "application/x-www-form-urlencoded"
}

resp = requests.post(AUTHORIZATION_TOKEN_URL, data=AUTHORIZATION_TOKEN_PAYLOAD, headers=headers)
if resp.status_code == 200:
    token_data = resp.json()
    print("✅ Token received successfully:")
    print(json.dumps(token_data, indent=2))

    # Extract key fields
    access_token = token_data["access_token"]
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in")

    # Save to file for reuse
    with open("lightspeed_tokens.json", "w") as f:
        json.dump(token_data, f, indent=2)

    print("\n🔹 Access token saved to lightspeed_tokens.json")
else:
    print("❌ Token request failed:", resp.status_code, resp.text)

print("🔹 Status Code:", resp.status_code)
print("🔹 Response JSON:", resp.json())
import base64
import hashlib
import os
from urllib import request

# Generate a random code_verifier (between 43–128 characters)
code_verifier = base64.urlsafe_b64encode(os.urandom(40)).rstrip(b'=').decode('utf-8')

# Create code_challenge using SHA256
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode('utf-8')).digest()
).rstrip(b'=').decode('utf-8')

print("CODE VERIFIER:", code_verifier)
print("CODE CHALLENGE:", code_challenge)


# step1 - open this url with your own code challenge(code_challenge) -'https://lightspeedapis.com/resto/oauth2/v1/authorize?response_type=code&client_id=f22f696fcea88edfa6ecaa612cff55d4&redirect_uri=https://localhost&code_challenge_method=S256&code_challenge=2Nhi50SdnzDg7a9qX6Y2blW7sbXyR_4K5lq7aMg88E4'

# step2 -  step1 opens a page where you have to input login_id and password - ID=Lightspeed@frietchalet.be. ,password=Lightspeed1 on submit it redirect you on page where you have to Allow the following application to access your Lightspeed account

# step3 - step2 redirect you on predefine localhost url which have code parameter , store that code and now we have to make a request to get authorization token on -- https://lightspeedapis.com/resto/oauth2/v1/token , with payload like -- 
# {
#   "grant_type": "authorization_code",
#   "client_id": "f22f696fcea88edfa6ecaa612cff55d4",
#   "client_secret": "69d400fcc219c7acfaa4542bd3c6e3b65731fc0931b14a36ea76723393aebd37",
#   "redirect_uri": "https://localhost",
#   "code_verifier": "jhHX_guOxaae8c-Qu9vgynSq_vNPxGBGtffeo7awRUrhDVZy9p6WTQ", //which we use to create code challenge
#   "code": "yuMyYiImkXaCfXWHYpQTagcVhee2ts6PXt7wJwwM_AAeyB2zWUf.rn8WxT-jdH0Y"
# }
# this will give us access token which gives us permission to make acces lightspeed L-series endpoints.

# step4 - now we can hit l-series endpoints like - https://lightspeedapis.com/resto/rest/onlineordering/order to get order details , just vwe have to pass auth token which we get in step3



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


code_verifier = base64.urlsafe_b64encode(os.urandom(40)).rstrip(b'=').decode('utf-8')
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode('utf-8')).digest()
).rstrip(b'=').decode('utf-8')

client_id='f22f696fcea88edfa6ecaa612cff55d4'
redirect_uri='http://127.0.0.1:8000/lightspeed/callback/'
authorize_url='https://lightspeedapis.com/resto/oauth2/v1/authorize'
client_secret="69d400fcc219c7acfaa4542bd3c6e3b65731fc0931b14a36ea76723393aebd37",
code_challenge_method = "S256"
LIGHTSPEED_LOGIN_ID='Lightspeed@frietchalet.be'
LIGHTSPEED_LOGIN_PASSWORD='Lightspeed1'

accounts_url = (
    f"{authorize_url}"
    f"?response_type=code"
    f"&client_id={client_id}"
    f"&redirect_uri={redirect_uri}"
    f"&code_challenge_method={code_challenge_method}"
    f"&code_challenge={code_challenge}"
)


authorization_token_url=(
    f"https://lightspeedapis.com/resto/oauth2/v1/token"
    )
authorization_token_payload={
    "grant_type": "authorization_code",
    "client_id": "{client_id}",
    "client_secret": "{client_secret}",
    "redirect_uri": "https://localhost",
    "code_verifier": "{code_verifier}", #which we use to create code challenge
    "code": "yuMyYiImkXaCfXWHYpQTagcVhee2ts6PXt7wJwwM_AAeyB2zWUf.rn8WxT-jdH0Y" #the code which you get from redirect url params
    }

lightspeed_order_details_url="https://lightspeedapis.com/resto/rest/onlineordering/order"
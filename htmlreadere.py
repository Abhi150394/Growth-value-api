from bs4 import BeautifulSoup
import requests

# Let's assume you already have the response object from requests
response = requests.get("https://lightspeedapis.com/resto/oauth2/v1/authorize?...")

# Parse HTML content
soup = BeautifulSoup(response.content, "html.parser")

# Find the inputs by data-testid
user_input = soup.find("input", {"data-testid": "userId"})
password_input = soup.find("input", {"data-testid": "password"})

# Extract names (used for form submission)
user_field_name = user_input.get("name")
password_field_name = password_input.get("name")

# Prepare the payload to fill values
payload = {
    user_field_name: "your_username_here",
    password_field_name: "your_password_here"
}

# Print results
print("User field:", user_field_name)
print("Password field:", password_field_name)
print("Payload:", payload)

import requests
from bs4 import BeautifulSoup
from decimal import Decimal
import re

# headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
#            'Upgrade-Insecure-Requests': "1",
#            'Referer': 'https://foodgigant.be/nl/account/login/',
#            'Origin': 'https://foodgigant.be',
#            'Cookie':'PHPSESSID=pd8b1lvuicns0iodoblpf96go8; cookie_lan=nl',
#            'Content-Type': 'application/x-www-form-urlencoded',
#            'Connection': 'keep-alive',
#            'Cache-Control': 'max-age=0',
#            'Accept-Language': 'en-US,en;q=0.9',
#            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
# }
headers = {
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/x-www-form-urlencoded',
}

login_data = {
    'email': 'marketing@defrietbooster.be',
    'password': 'Stoofvlees1!',
    'submit_login_form':'1'
}

def scrape_frituurland():
    with requests.Session() as s:
        # print("[INFO] Scraping Frituurland!")
        # url = 'https://foodgigant.be/nl/account/login/'
        # r = s.post(url,data=login_data,headers = headers)
        
        # headers.pop('Referer')
        # url = "https://foodgigant.be/nl/shop/"
        # r = s.get(url,headers = headers)
        # soup = BeautifulSoup(r.text, 'html5lib')
        # product_div = soup.find('div',attrs = {'class':'product_list'})
        # products = product_div.find_all('a',attrs = {'class':'product'})
        # print(f"[INFO] Products Found: {len(products)}")

        # data = []
        print("[INFO] Logging in...")
        r = s.post(
            'https://foodgigant.be/nl/account/login/',
            data=login_data,
            headers=headers
        )

        print("Session cookies:", s.cookies.get_dict())

        print("[INFO] Fetching shop page...")
        r = s.get('https://foodgigant.be/nl/shop/', headers=headers)

        soup = BeautifulSoup(r.text, 'html5lib')
        product_div = soup.find('div', class_='product_list')
        products = product_div.find_all('a', class_='product')

        print(f"[INFO] Products Found: {len(products)}")

        data = []
        for i in products:
            print(i.prettify())
            # break
            product_name = i.find('div',attrs = {'class':'product_info_wrapper_name'}).get_text(strip=True)
            product_link = "https://foodgigant.be" + i['href']

            product_image_div = i.find('div', class_='product_image')
            style_attribute = product_image_div['style']
            product_image = "https://foodgigant.be" + style_attribute.split('url(')[1].split(')')[0]

            
            price_element = i.find('strong', class_='price')

            if price_element:
                price_text = price_element.get_text(strip=True)
                match = re.search(r'[\d,.]+', price_text)

                if match:
                    value = match.group()
                    value = value.replace(',', '')  # safe default
                    product_price = Decimal(value)
                else:
                    product_price = Decimal("0")
            else:
                product_price = Decimal("0")
            price_value = ''.join(filter(str.isdigit, price_text))
            product_price = Decimal(price_value) / 100

            data.append({'product':product_name,'link':product_link,'image':product_image, 'price':product_price})

    return ['frituurland', data]

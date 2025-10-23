import requests
from bs4 import BeautifulSoup
from decimal import Decimal


headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
           'Upgrade-Insecure-Requests': "1",
           'Referer': 'https://frituurland.be/nl/account/login/',
           'Origin': 'https://frituurland.be',
           'Cookie':'PHPSESSID=pd8b1lvuicns0iodoblpf96go8; cookie_lan=nl',
           'Content-Type': 'application/x-www-form-urlencoded',
           'Connection': 'keep-alive',
           'Cache-Control': 'max-age=0',
           'Accept-Language': 'en-US,en;q=0.9',
           'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
}

login_data = {
    'email': 'marketing@defrietbooster.be',
    'password': 'Stoofvlees1!',
    'submit_login_form':'1'
}

def scrape_frituurland():
    with requests.Session() as s:
        print("[INFO] Scraping Frituurland!")
        url = 'https://frituurland.be/nl/account/login/'
        r = s.post(url,data=login_data,headers = headers)
        
        headers.pop('Referer')
        url = "https://frituurland.be/nl/shop/"
        r = s.get(url,headers = headers)
        soup = BeautifulSoup(r.text, 'html5lib')
        product_div = soup.find('div',attrs = {'class':'product_list'})
        products = product_div.find_all('a',attrs = {'class':'product'})
        print(f"[INFO] Products Found: {len(products)}")

        data = []
        for i in products:
            product_name = i.find('div',attrs = {'class':'product_info_wrapper_name'}).get_text(strip=True)
            product_link = "https://frituurland.be" + i['href']

            product_image_div = i.find('div', class_='product_image')
            style_attribute = product_image_div['style']
            product_image = "https://frituurland.be" + style_attribute.split('url(')[1].split(')')[0]

            price_element = i.find('strong', class_='price')
            price_text = price_element.get_text()
            price_value = ''.join(filter(str.isdigit, price_text))
            product_price = Decimal(price_value) / 100

            data.append({'product':product_name,'link':product_link,'image':product_image, 'price':product_price})

    return ['frituurland', data]

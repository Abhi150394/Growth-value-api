import requests
from bs4 import BeautifulSoup
from decimal import Decimal

import logging

_logger = logging.getLogger(__name__)


headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
           'Upgrade-Insecure-Requests': "1",
           'Referer': 'https://foods.nl/nl',
           'Origin': 'https://foods.nl',
           'Cookie':'stn_userprefs=%7B%22language%22%3A%22nl%22%7D; stn_cookies=accept; PHPSESSID=38e62fb8802dd2d9d15cdbc6899faf6c',
           'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
           'Connection': 'keep-alive',
           'Cache-Control': 'max-age=0',
           'Accept-Language': 'en-US,en;q=0.9',
           'Accept':'application/json, text/javascript, */*; q=0.01',
}

login_data = "project_user_login=8ad41d403fd581f2cac5365cb1fbdfaeae90effb&current_url=%2Fnl&name=INFO%40defrietbooster.be&password=Stoofvlees1!"

def scrape_foodnl():
    with requests.Session() as s:
        print("[Info] Scraping Foods.nl")
        url = 'https://foods.nl/nl'
        r = s.get(url,headers = headers)
        cookie = r.cookies.get("PHPSESSID")
        headers['Cookie'] = "stn_userprefs=%7B%22language%22%3A%22nl%22%7D; stn_cookies=accept; PHPSESSID=" + cookie
        soup = BeautifulSoup(r.text, 'html5lib')
        csrf = soup.find('input',attrs = {'name':'project_user_login'})['value']
        login_data = "project_user_login=" + csrf + "&current_url=%2Fnl&name=INFO%40defrietbooster.be&password=Stoofvlees1!"

        url = 'https://foods.nl/nl/api/v1/user/login'
        r = s.post(url,data=login_data,headers = headers)
        cookie = r.cookies.get("PHPSESSID")
        headers['Cookie'] = "stn_userprefs=%7B%22language%22%3A%22nl%22%7D; stn_cookies=accept; PHPSESSID=" + cookie
        
        url = "https://foods.nl/nl/zoek-op-merk"
        r = s.get(url,headers = headers)
        soup = BeautifulSoup(r.text, 'html5lib')
        brands_list = soup.find_all('a',attrs = {'data-track-action':'Brand clicked'})

        print("[Info] Links Collected!")
        data = []
        for link in brands_list:
            url = "https://foods.nl"+link['href']
            print("[INFO] Scraping", url)
            r = s.get(url,headers = headers)
            soup = BeautifulSoup(r.text, 'html5lib')
            item_list = soup.find_all('div', attrs = {'class':'eq equal-height product product-card product-card-infoorder'})

            for item_div in item_list:
                try:
                    product_link="https://foods.nl"
                    product_name = ""
                    image_link = "https://foods.nl/image" + item_div.find('img', attrs = {'class':'image print-image'})['src']
                    
                    if item_div.find('a', attrs = {'rel':'nofollow'}):
                        product_link = "https://foods.nl" + item_div.find('a', attrs = {'rel':'nofollow'}).get('href')
                    elif item_div.find('a').get('href'):
                        product_link = product_link + item_div.find('a').get('href')
                    
                    if item_div.find('header').find('a', attrs = {'rel':'nofollow'}):
                        product_name = item_div.find('header').find('a', attrs = {'rel':'nofollow'}).get_text(strip=True)
                    elif item_div.find('header').find('a'):
                        product_name = item_div.find('header').find('a').get_text(strip=True)
                        
                    brand = item_div.find('div', class_='item item-1').find('div', class_='value').text.strip()
                    quantity = item_div.find('div', class_='item item-2').find('div', class_='value').text.strip()

                    price_text = item_div.find('div', class_='item item-3').find('span', class_='price').text.strip()
                    price = Decimal(str(price_text).lstrip().rstrip().replace(" ", "")[1:].replace(',','.'))

                    data.append({'product':product_name,'link':product_link,'image':image_link, 'price':price, 'brand': brand, 'quantity':quantity})
                except Exception as exc:
                    _logger.error(f"error",exc)
                    _logger.error(
                        f"image_link: {image_link}"
                        f"product_link: {product_link}"
                        f"product_name: {product_name}"
                        f"brand: {brand}"
                        f"quantity: {quantity}"
                        f"price_text: {price_text}"
                        f"price: {str(price)}"
                    )

    return ['Foods.nl', data]
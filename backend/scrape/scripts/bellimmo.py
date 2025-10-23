import requests
from bs4 import BeautifulSoup
from decimal import Decimal

headers = {'authority' : 'shop.bellimmohoreca.be',
           'accept' : 'application/json, text/javascript, */*; q=0.01',
           'accept-language' : 'en-US,en;q=0.9',
           'content-type' : 'application/x-www-form-urlencoded; charset=UTF-8',
           'origin':'https://shop.bellimmohoreca.be',
           'referer' : 'https://shop.bellimmohoreca.be/',
           'sec-ch-ua' : '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
           'sec-ch-ua-mobile' : '?0',
           'sec-ch-ua-platform' : '"Windows"',
           'sec-fetch-dest' : 'empty',
           'sec-fetch-mode' : 'cors',
           'sec-fetch-site' : 'same-origin',
           'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
           'x-requested-with' : 'XMLHttpRequest'           
}

login_data = {
    'username' : 'info@defrietbooster.be',
    'password' : 'Stoofvlees1!'
}

def scrape_bellimmo():
    with requests.Session() as s:
        offset = 0
        data_list = []
        print("[Info] Scraping Bellimmo")
        while offset <= 10000:
            url = 'https://shop.bellimmohoreca.be/mvc/login'
            r = s.post(url,data=login_data,headers = headers)
            cookie = r.cookies.get("MARCANDO")
            if cookie:
                headers['cookie'] = '_pk_id.17.0953=76519b4631d92957.1687856996.; _ga=GA1.2.1616015301.1687856999; complianceCookie=on; marcandoViewType=g; _gid=GA1.2.1101294487.1688320116; MARCANDO=' + cookie
            url = 'https://shop.bellimmohoreca.be/producten/?offset=' + str(offset)
            print(f"[Info] Scraping page {url}")
            offset += 12
            r = s.get(url, headers=headers)
            soup = BeautifulSoup(r.text, 'html5lib')
            products = soup.find_all('div', attrs={'class': 'list-productwrap'})
            for product in products:
                name = product.find('a', attrs = {'class':'grid-title-fav'}).get_text(strip=True)
                image = 'https://shop.bellimmohoreca.be' + product.find('img', attrs = {'class':'article-catalog-photo'})['src']
                price_element = product.find("strong", attrs = {'class' : 'article-strong-price'})
                try:
                    price_text = ""
                    for child in price_element.children:
                        if isinstance(child, str):
                            price_text += child
                        elif child.name == "span":
                            price_text += child.text
                    price_text = price_text.strip().replace('€\xa0', '').replace(",", ".")
                    price = Decimal(price_text)
                except:
                    price = Decimal(0.0)

                link = 'https://shop.bellimmohoreca.be' + product.find("a", href=True, itemprop="url")['href']

                data_list.append({'product':name, 'link':link, 'image':image, 'price':price})

    return ['bellimmo', data_list]
import requests
from bs4 import BeautifulSoup
import html5lib
from decimal import Decimal

headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
           'Upgrade-Insecure-Requests': "1",
           'Referer':'http://shop.snacksbosteels.be/NL/Account/Login',
           'Origin':'http://shop.snacksbosteels.be',
           'Content-Type':'application/x-www-form-urlencoded',
           'Connection':'keep-alive',
           'Cache-Control': 'max-age=0',
           'Accept-Language':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
 }
login_data = {
             'LUserName' : 'BOST6969',
             'LPassword' : 'FRIETBOOSTER',
        
  }

def scrape_snacksbosteels():
    with requests.Session() as s:
        print("[Info] Scraping Snacks Bosteels")
        url = 'http://shop.snacksbosteels.be/NL/Account/Login'
        r = s.post(url,data=login_data,headers = headers)
        
        headers.pop('Referer')
        url = "http://shop.snacksbosteels.be/NL/Product/Index"
        r = s.get(url,headers = headers)
        soup = BeautifulSoup(r.text, 'html5lib')
        link_div = soup.find('div',attrs = {'id':'page_navigation'})
        links_html = link_div.find_all('a',attrs = {'class':'page_link'})
        links = []
        for link in links_html:
            links.append('http://shop.snacksbosteels.be' + str(link['href']))
        print("[Info] Links Collected!")
        
        data_list = []
        for pages in links:
            r = s.get(pages,headers = headers)
            print(f"[Info] Scraping page {pages}")
            soup = BeautifulSoup(r.text, 'html5lib')
            item = soup.find_all('tr',attrs = {'ng-controller':'ShopActionController'})
            # text_list = [div.get_text(strip=True) for div in item]
            for i in item:
                name = i.find('td',attrs = {'class':'text-left'}).get_text(strip=True)
                link = 'http://shop.snacksbosteels.be' + str(i.find('a',attrs = {'style':'width:50px;'})['href'])
                try:
                    image = 'http://shop.snacksbosteels.be' + str(i.find('img',attrs = {'class':'bg-colr'})['src'])
                except:
                    image = 'No image found'
                price = i.find('td',attrs = {'class':'text-right nowrap'}).get_text(strip=True)
                data_list.append({'product':name,'link':link,'image':image.split('?')[0], 'price':Decimal(str(price)[:-1].replace(',','.'))})

    return ['snacksbosteels', data_list]
    
    
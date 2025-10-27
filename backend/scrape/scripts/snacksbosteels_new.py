import requests
from decimal import Decimal
from bs4 import BeautifulSoup
import logging

_logger = logging.getLogger(__name__)

AllProducts = []
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Upgrade-Insecure-Requests': "1",
    'Referer': 'https://shop.snacksbosteels.be/NL/Account/LogOn',
    'Origin': 'https://shop.snacksbosteels.be',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Cookie': 'ASP.NET_SessionId=hh3uxpwkkfpm3iz2rjpjp5g0; LanguageOfPC=nl; ',
    'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
}

login_url = 'https://shop.snacksbosteels.be/NL/Account/LogOn'
product_url = "https://shop.snacksbosteels.be/NL/Product?department="
GETORDERDATE_URL = "https://shop.snacksbosteels.be/API/Cart/GetOrderDate"
login_data = {
    'UserName': 'BOST6969',
    'PassWord': 'FRIETBOOSTER',
    'RememberMe': True,
}

def parse_date(date_str):
    dd, mm, yyyy = date_str.split("/")
    return f"{yyyy}-{mm}-{dd}"

def scrape_snacksbosteels():

    try:
        with requests.Session() as s:
            print("[INFO] Bosteels Scrape Started!")
            s.post(login_url, data=login_data, headers=headers)
            aspxauth = s.cookies.get('.ASPXAUTH')
            
            headers[
                    'Cookie'] = f".ASPXAUTH={aspxauth}"
            departments = requests.get(
                "https://shop.snacksbosteels.be/API/Department/GetChildDepartments/?DepartmentCode=&language=NL", headers=headers).json()
            
            codes = [dept.get("Code") for dept in departments]
            
            # CODES = []
            # for code in codes:
            #     CODES.append(code)
            #     sub_departments = requests.get(f"https://shop.snacksbosteels.be/API/Department/GetChildDepartments/?DepartmentCode={code}&language=NL", headers=headers).json()
            #     CODES.extend([dept.get("Code") for dept in sub_departments])
            
            order_date = requests.get(GETORDERDATE_URL, headers=headers).json()
            order_date = parse_date(order_date)
            
            for code in codes:
                page_number = 1
                page_url = f"{product_url}{code}"
                print("[Info] Scraping:", page_url)
                while True:
                    product_api_url = f"https://shop.snacksbosteels.be/API/Product/GetProductsAndRelatedProductsByDepartmentCode?DepartmentCode={code}&searchterm=&isFavorite=false&favoriteType=-1&showPromotions=false&language=NL&$expand=Maatbalks&orderdate={order_date}&page={page_number}"
                    products = requests.get(product_api_url, headers=headers).json()
                    
                    if len(products)==0:
                        break
                    
                    articleDetailIds= ",".join([str(p.get("ArticleDetailIds")[0]) for p in products])
                    packageAmounts = ",".join([str(int(p.get("PackageAmount"))) for p in products])
                    
                    price_api_url = f"https://shop.snacksbosteels.be/API/Product/GetProductPriceRelated?articleDetailIds={articleDetailIds}&packageAmounts={packageAmounts}&OrderDate={order_date}"
                    price_json = requests.get(price_api_url, headers=headers).json()
                    
                    for i, p in enumerate(products):
                        id = p.get("Id")
                        name = p.get("Description","")
                        img = p.get("MainImageUrl")
                        price = Decimal(str(round(price_json[i].get("Price"), 2)))
                        item = {
                            "product": name,
                            "link": f"https://shop.snacksbosteels.be/NL/Product/Info/{id}",
                            "image": f"https://shop.snacksbosteels.be{img}",
                            "price": price,
                        }
                        AllProducts.append(item)
                    
                    page_number += 1
                print(f"Product scraped: {len(AllProducts)}")
    
    except Exception as exc:
        _logger.error(f"Unable to scrape Bosteels. error_msg:{exc}")


    return ['snacksbosteels', AllProducts]

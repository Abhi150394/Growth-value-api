from decimal import Decimal
from bs4 import BeautifulSoup
import time
import random
import cloudscraper 

HEADERS={
    "User-Agent":(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.0.0 Safari/537.36"
    ),
    "Referer": "https://shop.bellimmohoreca.be/",
    "X-Requested-With": "XMLHttpRequest",
}

LOGIN_DATA = {
    "username": "info@defrietbooster.be",
    "password": "Stoofvlees1!",  
}

def scrape_bellimmo():
    """
    Scrape Bellimmo products, returns ["bellimmo", data_list]
    Used by backend.scrape.main.call_scrape_bellimmo
    """
    scraper = cloudscraper.create_scraper()
    data_list = []

    login_url = "https://shop.bellimmohoreca.be/mvc/login"

    # 1) GET login page so cloudscraper can handle Cloudflare JS
    r = scraper.get(login_url, headers=HEADERS)
    print("[Bellimmo] GET login status:", r.status_code)

    if "Just a moment" in r.text[:500]:
        print("[Bellimmo] Cloudflare challenge not bypassed by cloudscraper.")
        return ["bellimmo", data_list]

    # 2) POST login (field names assumed to be username/password)
    r2 = scraper.post(
        login_url,
        data=LOGIN_DATA,
        headers=HEADERS,
        # timeout=20,
        allow_redirects=True,
    )
    print("[Bellimmo] POST login status:", r2.status_code)
    print("[Bellimmo] Cookies after login:", scraper.cookies.get_dict())

    if not scraper.cookies.get_dict():
        print("[Bellimmo] No cookies, login probably failed.")
        return ["bellimmo", data_list]

    # 3) Scrape product list pages
    offset = 0
    step = 12

    while offset <= 10000:
        page_url = f"https://shop.bellimmohoreca.be/producten/?offset={offset}"
        print("[Bellimmo] Fetching", page_url)
        r = scraper.get(page_url, headers=HEADERS)

        if r.status_code != 200:
            print("[Bellimmo] Non-200 status:", r.status_code)
            break

        soup = BeautifulSoup(r.text, "html5lib")
        products = soup.find_all("div", attrs={"class": "list-productwrap"})
        if not products:
            print("[Bellimmo] No products found, stopping.")
            break

        for product in products:
            # name
            name_el = product.find("a", attrs={"class": "grid-title-fav"})
            name = name_el.get_text(strip=True) if name_el else ""

            # image
            img_el = product.find("img", attrs={"class": "article-catalog-photo"})
            if img_el and img_el.get("src"):
                image = "https://shop.bellimmohoreca.be" + img_el["src"]
            else:
                image = ""

            # price
            price_element = product.find("strong", attrs={"class": "article-strong-price"})
            price = Decimal("0.0")
            if price_element:
                try:
                    price_text = ""
                    for child in price_element.children:
                        if isinstance(child, str):
                            price_text += child
                        elif getattr(child, "name", None) == "span":
                            price_text += child.get_text()
                    price_text = price_text.strip().replace("€\xa0", "").replace(",", ".")
                    if price_text:
                        price = Decimal(price_text)
                except Exception:
                    price = Decimal("0.0")

            # link
            link_el = product.find("a", href=True, itemprop="url")
            link = "https://shop.bellimmohoreca.be" + link_el["href"] if link_el else ""

            data_list.append(
                {
                    "product": name,
                    "link": link,
                    "image": image,
                    "price": price,
                }
            )

        offset += step
        time.sleep(random.uniform(0.4, 1.2))

    return ["bellimmo", data_list]

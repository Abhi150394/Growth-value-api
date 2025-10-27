import requests
from bs4 import BeautifulSoup
from decimal import Decimal

def scrape_snackdeals():
    with requests.Session() as s:
        print("[INFO] SnacksDeal Scraped Started!")
        url = "https://shop.snackdeals.be/all/?count=100000"
        data_list = []

        response = s.get(url)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            product_items = soup.find_all("div", class_="l-products-item")

            for item in product_items:
                product_name = item.find('span', itemprop='name').text.strip()
                product_price = item.find('span', class_='lbl-priceinline').text.strip()
                product_price = Decimal(product_price[2:].replace(".", "").replace(",", ".")) 

                img_tag = item.find("img", itemprop="image")
                if img_tag:
                    product_image_url = "https://shop.snackdeals.be" + img_tag["src"]

                link_tag = item.find("a", class_="hyp-thumbnail")
                if link_tag:
                    product_link = "https://shop.snackdeals.be" + link_tag["href"]

                # print("Product Name:", product_name)
                # print("Product Price:", product_price)
                # print("Product Image URL:", product_image_url)
                # print("Product Link:", product_link)
                # print()
                
                data_list.append({'product':product_name, 'link':product_link, 'image':product_image_url, 'price':product_price})
        else:
            print("[WARNING] Failed to retrieve the webpage (Status Code:", response.status_code, ")")

    print("[INFO] Products Scraped: " + str(len(data_list)))
    
    return ["snackdeals", data_list]
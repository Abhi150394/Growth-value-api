import requests
import re
from bs4 import BeautifulSoup
from decimal import Decimal

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
    'Referer': 'https://givana.be/account/inloggen/',
    'Origin': 'https://givana.be',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Upgrade-Insecure-Requests': '1',
}


login_data = {
    'email': 'info@defrietbooster.be',
    'password': 'FRIETBOOST',
    'remember_me': '1',
    'submit_login_form': '1',
}

def scrape_givana():
    with requests.Session() as s:
        # Initialize a list to store the extracted data
        print("[INFO] Givana Scrape Started!")
        product_details = []

        # Log in
        login_url = 'https://givana.be/account/inloggen/'
        r = s.post(login_url, data=login_data, headers=headers)

            # Get the main shop page
        response = s.get('https://givana.be/shop/', headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the <li> element with class 'nav_shop'
        nav_shop_element = soup.find('li', class_='nav_shop')

        if nav_shop_element:
            # Find all the <a> elements within the <ul> under the 'nav_shop' element
            a_elements = nav_shop_element.find('ul').find_all('a', href=True)

            links = []

            for a_element in a_elements:
                link = 'https://givana.be' + a_element['href']
                links.append(link)

#             print("Links available: " + links)
#             links = links[3:]
            # print("Links to Scrape: ")
            # print(links)

        for link_category in links:
            
            pageNo = 1
            num_pages = 2

            while (num_pages >= pageNo):

                pageNo = num_pages
                url = link_category + "?page=" + str(pageNo)

                response = requests.get(url)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    paging_section = soup.find('div', class_='paging')
                    if(paging_section):
                        page_links = paging_section.find_all('a')
                    else:
                        pageNo=1
                        break
                    num_pages = 0

                    for link in page_links:
                        try:
                            page_number = int(link.text)
                            num_pages = max(num_pages, page_number)
                        except ValueError:
                            pass 
                        
                    if num_pages > 0:
                        pass
                    else:
                        pageNo = 1
                        break
                        print("No paging information found on the page.")
                else:
                    print("Failed to retrieve the page. Status code:", response.status_code)
                    
            
            for i in range(1, pageNo+1):
            
                url = link_category + "?page=" + str(i)
                response = s.get(url, headers=headers) 

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')

                    product_elements = soup.find_all('a', class_='product')
                    if product_elements:
                        for product_element in product_elements:
                            name = product_element.find('span', class_='name').text.strip()
                            link = 'https://givana.be' + product_element['href']

                            url_parts = link.split('/')
                            for part in reversed(url_parts):
                                if "-" in part:
                                    numbers = re.findall(r'\d+', part)
                                    if numbers:
                                        last_number = numbers[-1]

                                        image = f"https://givana.be/_images/products/{last_number}.jpg"
                                    break
                            price = product_element.find('span', class_='price').text.strip()
                            price = price[2:]
                            price = Decimal(price.replace(".","").replace(",", "."))

                            # Create a dictionary with the extracted data
                            product_info = {
                                'product': name,
                                'link': link,
                                'image': image,
                                'price': price
                            }

                            # Append the dictionary to the list
                            product_details.append(product_info)


                    # Print Progress
                    print("[INFO] Scrapped URL: " + url)
                    print("[INFO] Products Scraped: " + str(len(product_details)))


                else:
                    print('[WARNING] Failed to scrape: ' + url)

    return ["givana", product_details]

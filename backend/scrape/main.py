from .scripts.snacksbosteels_new import scrape_snacksbosteels
from .helpers.export import create_file
from .scripts.bellimmo import scrape_bellimmo
from .scripts.givana import scrape_givana
from .scripts.snacksdeal import scrape_snackdeals
from .scripts.frituurland import scrape_frituurland
from .scripts.foods import scrape_foodnl
from ..models import Products, Scraper
import re
from decimal import Decimal
from datetime import date

brand_bosteels = ['Abinda', 'Ad Van Geloven', 'Alpro', 'Alro', 'Alsa', 'Amaya', 'Anda', 'Apollo', 'Appelsientje', 'Aquarius', 'Ardenia', 'Ardo', 'Ariel', 'Arizona', 'Aroy-D', 'Artifresh', 'Aveno', 'Avg', 'Aviko', 'Avila', 'B Six', 'Bachten de Kupe', 'Baeten', 'Baktat', 'Bakx', 'Balade', 'Ballymaloe', "Banquet d'Or", 'Becel', 'Bechoux', 'Beckers', 'Bellimmo', "Ben & Jerry's", 'Bicky', 'Biere des amis', 'Biodore', 'Bionade', 'Biopack', 'Black Tiger', "Bodhi's", 'Boerinneke', 'Borimex', 'Bosteels', 'Bourgondier', 'Breydel', 'Bs', 'Bubba', 'Buitenhuis', 'Callebaut', 'Calv', "Camp's", 'Capri-Sun', 'Carton', 'Cassonade', 'Castel D Oro', "Castel d'oro", 'Cecemel', 'Cederroth', 'Chaudfontaine', 'Coca Cola', 'Cocovite', 'Coertjens', 'Copperhead', 'Cosy & Trendy', 'Crombez', 'Cruse', 'Cuba Rum', 'Cuisine Maison', "D'Hulster", 'DV Foods', 'Daddy Cool', 'Dash', 'Dauphine', 'De Ambachterie', 'De Bourgondier', 'De Jong', 'De Notekraker', 'De Paddestoel', 'De Vries', 'De Zilverberg', 'De jong', 'Debic', 'Deligout', 'Delimeal', 'Delino', 'Delizio', 'Dely', 'Depa', 'Detectaplast', 'Devos Lemmens', 'Devries', 'Diadem', 'Didden', 'Diknek', 'Dipp', 'Diversi Foods', 'Diversifood', 'Dole', 'Doritos', 'Dr Pepper', 'Dr. Oetker', 'Dreft', 'Duca', 'Duni', 'Dunya', 'Duplex', 'Dürüm Company', 'Elif', 'Elite', 'Elvea', 'Enet', 'Epic', 'Eru', 'Euro', 'Europoultry', 'Evian', 'Family Chicken', 'Fanta', 'Farmchix', 'Ferrerro', 'Fever-tree', 'Fijnko', 'Filou', 'Finley', 'First State', 'Fisker', 'Flexitarian B', 'Flexitarian Bastards', 'Food & Vision', 'Food Empire', 'Foster', 'Frenzel', 'Fresh Fruit Express', 'Fresh&Saucy Foods', 'Frit Is It', 'Futuro', 'Fuze Tea', 'Galana', 'Garden Gourmet', 'Garlan', 'Gastronello', 'Gazi', 'Gini', 'Gran Tapas', 'Gyma', 'Halde', 'Hamal', 'Hay Straws', 'Heinz', 'Hellmann S', 'Hellmanns', 'Hendi', 'Henny S', "Henny's", 'Hennys', 'Heritage', 'Hoegaarden', 'Hofkip', 'Holeki', 'Homeko', 'Honig', 'Horesca', 'I&S', 'Iglo', 'Ijsboerke', 'Il Primo', 'Imperial', 'Inex', 'Inox', 'Inproba', 'Isfi', 'Isigny', 'Java', 'Jermayo', 'Jiv', 'Jupiler', 'K B', 'Karmez', 'Ketjep', 'Kikkoman', 'Knorr', 'Kriek', 'Kwekkeboom', 'L A Streetfood', "L'Arboc", "L'Etoile", 'LA Streetfood', 'La Cuisine Belge', 'La Lorraine', 'La Streetfood', 'La Vie Est Belle', 'La Vie est Belle', 'La William', 'Laan', 'Laiterie des Ardennes', 'LambWeston', 'Lays', 'Le Vesuve', 'Leffe', 'Lenor', 'Limonino', 'Lipton', 'Lolliewood', 'Lutece', 'Lutosa', 'Magic Star', 'Magnum', 'Maitre', 'Malinasauzen', "Mama's Bread", 'Manna', 'Maredsous', 'Maurice Mathieu', 'Mc Cain', 'McCain', 'Mekabe', 'Mekkafood', 'Meli', 'Mestdagh', 'Mini Snacks', 'Minute Maid', 'MoMe', 'Molco', 'Mora', 'Mr. Proper', 'N/B', 'Nalu', 'Nestl', 'Nestlé', 'Nic', 'Noyen', 'OBUZ', 'Oasis', 'Ola', 'Oliehoorn', 'Oma Bobs', 'One Shot', 'Orangina', 'Ottimo', 'Ovi', 'Ozz turk', 'Pagotini', 'Pan', 'Panesco', 'Pastr', 'Pastridor', 'Pauwels', 'Pb Snacks', 'Pegi', 'Pepsi', 'Petrella', 'Piazolla', 'Piedboeuf', 'Pieters', 'Pita Fresh', 'Pitta Fresh', 'Pizzaiolo', 'Polidori', 'Pomton', 'Ponti', 'Poultry', 'Prins & Dingemans', 'Qinti', 'Quinoux', 'Rambol', 'Red bull', 'Rejo', 'Remia', 'Resto Culinair', 'Resto Frit', 'Roband', 'Royal', 'Royal Greenland', 'Salomon', 'Salubris', 'Saluclean', 'Salvequick', 'San pellegrino', 'Saviko', 'Schulstad', 'Schweppes', 'Sea Side', 'Selina', 'Servietto', 'Sier', 'Slowfood Masters', 'Smiths', 'Smoky Mountains', 'Socopa', 'Soft sel', 'Soubry', 'Souflesse', 'Spa', 'Sprite', 'Stella Artois', 'Stevens', 'Suma', 'Suprima', 'Swann', 'Swiffer', 'TNS', 'Tabasco', 'Tanet', 'Tapas Club', 'Tappaz', 'Teker', 'The Smiling Cook', 'Tienen', 'Tierenteyn', 'Tns', 'Topking', 'Tork', 'Torro Nero', 'Tropico', 'Twist and Drink', 'Tyson', 'Uyttewaal', 'V S', 'VA Foods', 'VR Plastics', 'Va Foods', 'Vamix Vdm', 'Van Lieshout', 'Van Osch', 'Van Reusel', 'Vandemoortele', 'Vanreusel', 'Vegetarische Slager', 'Vepeli', 'Verba', 'Verdonck', 'Vermop', 'Verstegen', 'Vikan', 'Vileda', 'Violet', 'Vittel', 'Vivera', 'Vleminckx', 'Vr', 'Welten', 'Werti', 'Wijko', 'Woksaus', 'Wouters', 'Zanetti', 'Zeisner']

def find_matching_item(input_string, string_list):
    for item in string_list:
        if item.lower() in input_string.lower():
            return item
    return ""


def convert_to_liters_or_kg(value, unit):
    unit = unit.upper()
    if unit == "ML":
        return float(value) / 1000.0
    elif unit in ["CL", "DL"]:
        return float(1)
    if unit in ["M","CM", "MM", "DM"]:
        return float(1)
    elif unit == "GR" or unit=="G":
        return float(1)
    elif unit == "ST":
        return float(value)
    else:
        return float(value)

def process_quantities(quantities):
    quantities = list(set(quantities))
    total_qty = 1.0
    multiplicative_qty = 1.0
    for qty in quantities:
        match = re.match(r'(\d+(?:\.\d+)?)(\s?X|\s?KG|\s?GR|\s?L|\s?ST|\s?CL|\s?MM|\s?CM|\s?G|\s?MG|\s?ML|)', qty, re.IGNORECASE)
        if match:
            value, unit = match.groups()
            unit = unit.strip().upper()
            value = value.strip()
            if not unit:
                multiplicative_qty *= float(1)
            if unit == 'X':
                multiplicative_qty *= float(value)
            else:
                total_qty *= convert_to_liters_or_kg(value, unit)
    
    return total_qty * multiplicative_qty

def extract_quantity(input_string):
    pattern = re.compile(r'[\d.]+(?:\s?(?:KG|GR|ML|ST|CL|X|MM|CM|G|M|MM|MG|L))', re.IGNORECASE)
    quantities = [pattern.findall(input_string)]
    for quantity in quantities:
        value = process_quantities(quantity)
    
    return Decimal(value)
    
    # ===================================Old code
    
    # pattern = r'(\d+(\s?[Xx]\s?\d+)?\s?[A-Za-z]+)'
    # match = re.search(pattern, str(input_string).upper())
    # if match:
    #     try:
    #         # value = Decimal(evaluate_rel_price(matches, input_string))
    #         value= Decimal(str(match.group(0).upper().split('L')[0].split('ML')[0].split('X')[0].split('KG')[0].split('G')[0].rstrip().lstrip()))
    #     except:
    #         value= Decimal(1.00)
    # else:
    #     value= Decimal(1.00)
    
    # return value

def clean_title(title):
    name = re.sub(r"[^a-zA-Z0-9'\s]", "", title.upper()).strip()
    return name

def extract_quantity_special(input_string):
    try:
        value= Decimal(str(input_string).replace(" ", "").rstrip().lstrip().upper().split('L')[0].split('ML')[0].split('X')[0].split('KG')[0].split('G')[0].rstrip().lstrip())
    except:
        value= Decimal(1.00)
    return value

def call_scrape_bellimmo():
    bellimo_data = scrape_bellimmo()
    # create_file(bellimo_data[0], bellimo_data[1])
    scraper = Scraper.objects.get(id=2)
    scraper.last_scraped = date.today()
    scraper.save()
    Products.objects.filter(scraper=scraper).delete()
    for i in bellimo_data[1]:
        product_name = str(i['product']).replace(',','.')
        product_link = i['link']
        product_image = i['image']
        product_price = i['price']
        product_brand = find_matching_item(product_name, brand_bosteels)
        product_vendor = "Bellimmo"
        relative = Decimal(format(product_price/extract_quantity(product_name), '.2f'))
        Products.objects.create(
            product_name=product_name,
            link=product_link,
            image_link=product_image,
            price=product_price,
            relative_price=relative,
            vendor=product_vendor,
            brand=product_brand,
            scraper=scraper
        ).save()
    
    print("Scraping Bellimmo Done!!")

def call_scrape_snacksbosteels():
    items = scrape_snacksbosteels()
    # create_file(items[0], items[1])
    scraper = Scraper.objects.get(id=1)
    scraper.last_scraped = date.today()
    scraper.save()
    Products.objects.filter(scraper=scraper).delete()
    for i in items[1]:
        product_name = str(i['product']).replace(',','.')
        product_link = i['link']
        product_image = i['image']
        product_price = i['price']
        product_brand = find_matching_item(product_name, brand_bosteels)
        product_vendor = "Bosteels"
        relative = Decimal(format(product_price/extract_quantity(product_name), '.2f'))
        Products.objects.create(
            product_name=product_name,
            link=product_link,
            image_link=product_image,
            price=product_price,
            relative_price=relative,
            vendor=product_vendor,
            brand=product_brand,
            scraper=scraper
        ).save()
    
    print("Scraping Snaksbosteels Done!!")
    
def call_scrape_givana():
    items = scrape_givana()
    # create_file(items[0], items[1])
    scraper = Scraper.objects.get(id=3)
    scraper.last_scraped = date.today()
    scraper.save()
    Products.objects.filter(scraper=scraper).delete()
    for i in items[1]:
        product_name = str(i['product']).replace(',','.')
        product_link = i['link']
        product_image = i['image']
        product_price = i['price']
        product_brand = find_matching_item(product_name, brand_bosteels)
        product_vendor = "Givana"
        relative = Decimal(format(product_price/extract_quantity(product_name), '.2f'))
        Products.objects.create(
            product_name=product_name,
            link=product_link,
            image_link=product_image,
            price=product_price,
            relative_price=relative,
            vendor=product_vendor,
            brand=product_brand,
            scraper=scraper
        ).save()
    
    print("Scraping Givana Done!!")

def call_scrape_snacksdeal():
    items = scrape_snackdeals()
    # create_file(items[0], items[1])
    scraper = Scraper.objects.get(id=4)
    scraper.last_scraped = date.today()
    scraper.save()
    Products.objects.filter(scraper=scraper).delete()
    for i in items[1]:
        product_name = str(i['product']).replace(',','.')
        product_link = i['link']
        product_image = i['image']
        product_price = i['price']
        product_brand = find_matching_item(product_name, brand_bosteels)
        product_vendor = "SnacksDeal"
        relative = Decimal(format(product_price/extract_quantity(product_name), '.2f'))
        Products.objects.create(
            product_name=product_name,
            link=product_link,
            image_link=product_image,
            price=product_price,
            relative_price=relative,
            vendor=product_vendor,
            brand=product_brand,
            scraper=scraper
        ).save()
    
    print("Scraping SnacksDeal Done!!")

def call_scrape_frituurland():
    items = scrape_frituurland()
    # create_file(items[0], items[1])
    scraper = Scraper.objects.get(id=5)
    scraper.last_scraped = date.today()
    scraper.save()
    Products.objects.filter(scraper=scraper).delete()
    for i in items[1]:
        product_name = str(i['product']).replace(',','.')
        product_link = i['link']
        product_image = i['image']
        product_price = i['price']
        product_brand = find_matching_item(product_name, brand_bosteels)
        product_vendor = "Frituurland"
        relative = Decimal(format(product_price/extract_quantity(product_name), '.2f'))
        Products.objects.create(
            product_name=product_name,
            link=product_link,
            image_link=product_image,
            price=product_price,
            relative_price=relative,
            vendor=product_vendor,
            brand=product_brand,
            scraper=scraper
        ).save()
    
    print("Scraping Frituurland Done!!")

def call_scrape_foodnl():
    items = scrape_foodnl()
    # create_file(items[0], items[1])
    scraper = Scraper.objects.get(id=6)
    scraper.last_scraped = date.today()
    scraper.save()
    Products.objects.filter(scraper=scraper).delete()
    for i in items[1]:
        product_name = clean_title(i['product'].strip()) # i['product'].strip().replace(',','.')
        product_link = i['link']
        product_image = i['image']
        product_price = i['price']
        product_brand = i['brand']
        product_vendor = "Foods.NL"
        relative = Decimal(format(product_price/extract_quantity(i['quantity']), '.2f'))
        Products.objects.create(
            product_name=product_name,
            link=product_link,
            image_link=product_image,
            price=product_price, 
            relative_price=relative,
            vendor=product_vendor,
            brand=product_brand,
            scraper=scraper
        ).save()
        
    print("Scraping Foods.NL Done!!")
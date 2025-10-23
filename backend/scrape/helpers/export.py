#Add all data export related helper functions here
#Later db will be accessed through here

#Temporary function to store the data
#Follow good practice to define functions
def create_file(filename:str, data:list) -> bool:
    try:
        f = open('data/' + filename + '.csv', "w")
    except:
        print('[Warning] Error Opening file!')
        return False
    f.write("Product Name,Product Link,Image,Price"+ "\n")
    for i in data:
        f.write(f"{str(i['product']).replace(',','.')},{i['link']},{i['image']},{i['price']}"+ "\n")
    f.close()
    return True


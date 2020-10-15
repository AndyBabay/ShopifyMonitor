

'''

This class is reponsible for running scripts that continously check inventory of product(s).

Class will have multiple functions specific to a shopify website. Functions that will send discord messages via webhook when a product is in stock.



'''
import time
import numpy as np
from dhooks import Webhook
import requests
import discord
from discord import Webhook, RequestsWebhookAdapter
from datetime import datetime,date
import pandas as pd # will be used to move data into a CSV file





in_Stock = None



key_words = []


'''
https://stackoverflow.com/questions/57422734/how-to-merge-multiple-json-files-into-one-file-in-python
'''

configure_script= {
"NonJsonUrl": "https://us.bape.com/products",
"url": "https://us.bape.com/products",
"ProductKey": ["ALL"],

"ShopifyInStock": "BapeProductsInStock.csv",
"ShopifyAll": "BapeProduct.csv",
"ShopifyOutofStock": "Bape_ProductNoStock.csv"
}


def shopifyScript(config):

    #clear .csv files here
    url = config['url']
    ShopifyInStock = config['ShopifyInStock']
    ShopifyAll= config['ShopifyAll']
    ShopifyOutofStock=config['ShopifyOutofStock']



    json_attach = url

    #print(json_attach)

    r = requests.get(json_attach)
    print(r.status_code)

    # load json object into data variable

    data = r.json()

    # Append dictionary of product details
    product_list = []

    out_of_Stock = []

    in_stock = []




    for item in data['products']:


        title = item['title']
        handle = item['handle']
        quickLink = config['NonJsonUrl'] + "/" + handle
        product_type = item['product_type']



        key_words.append(product_type)




        for variant in item['variants']:



            variantID= variant['id']
            colorSizeTitle = variant['title']
            color = variant['option2']
            #print(colorSizeTitle)
            size = variant['option3']
            price = variant['price']
            sku = variant['sku']
            availible = variant['available']
            #updated = item['updated_at']
            #imageSrc = variant['src']

            i = variant['featured_image']

            grab_image = None

            if i is not None:
                grab_image=i['src']

            product = {
                'Variant_ID': variantID,
                'title': title,
                'handle': handle,
                'product_type': product_type,
                'price': price,
                'size': size,
                'sku': sku,
                'availible': availible,
                'image': grab_image,
                'quickLink': quickLink,
                'colorSizeTitle': colorSizeTitle,
                'color':color
            }
            product_list.append(product)


    allStock = pd.DataFrame(product_list)


    return allStock




# takes url, and returns number of pages for /product website

def maxPages(config):

    count =0

    url =config['url'] + ".json?limit=800&page="+str(count)
    r= requests.get(url)

    var = r.json()

    if var['products'] is []:
        return count
    else:
        x= True
        while (x):
            count += 1
            url = config['url'] + ".json?limit=800&page=" + str(count)

            r = requests.get(url)
            var = r.json()
            if len(var['products'])==0:
                x=False
    url = " "
    return count


def mergeDataFrames(config):

    last_page = 5
    print(last_page)

    url = config['url']

    config['url'] += ".json?limit=800&page=0"
    print(config['url'])

    x = shopifyScript(config)
    getAllStock = x.copy()

    ShopifyAll = config['ShopifyAll']

    for i in range(1,last_page):
        config['url'] = url + ".json?limit=800&page="+str(i)
        print(config['url'])
        x = shopifyScript(config)
        grabDataFrames= x.copy()
        getAllStock=pd.concat([getAllStock,grabDataFrames]).drop_duplicates().reset_index(drop=True)


    getAllStock.to_csv("NEWER_FRAMES2.csv")
    currentTime = time.strftime("%T", time.localtime())
    config['url'] = url
    getAllStock = None
    print(f"Data Updated at {currentTime} on {str(date.today().year)}-{str(date.today().month)}-{str(date.today().day)}")


# takes configuration dictionary and returns a dataframe containign all the filtered products
def filterProducts(config,csv):



    # merging dataframes based on product key elements

    #csv= csv[csv['availible']==True]



    ProductKey = config['ProductKey'][0]

    if ProductKey == "ALL":
        return None
    else:
        filter_product = csv[csv['product_type'] == ProductKey]

        c = config["ProductKey"]

        for i in range(1, len(c)):
            ProductKey = config['ProductKey'][i]
            filter_product_inner = csv[csv['product_type'] == ProductKey]
            filter_product = pd.concat([filter_product, filter_product_inner]).drop_duplicates().reset_index(drop=True)


        filter_product.to_csv("FILTERIT.csv")

        return filter_product


'''
   ParseData: Takes as input a dictionary containing URL,Excel name, and key word. 
   
   Creates a list of key word(s). if an item in that key word matches product type, grab data from that row and use discord
   webhooks to pretty printed message
   '''


def discordWebHook(config,dataFrame):
    '''
        data frame is a table or a two-dimensional array-like structure in which each column contains values of one variable and each row contains one set of values from each column
       '''

    # Create webhook

    webhook = Webhook.partial(749291392794230856,
                              "BzcVpMGwBJ1Ja1NnlqaszAkNjNpVVbPenAs8AfyW6yAOogrVHUOVORziWsziQ1kDCRTd",
                              adapter=RequestsWebhookAdapter())
    filter_product = dataFrame.copy()

    # print first row and all columns
    # print (filter_shoes.iloc[0])
    '''
    https://stackoverflow.com/questions/40622796/pandas-dataframe-how-to-print-single-row-horizontally
    '''
    # access each row and column of the data frame
    firstVal = filter_product['title'].iloc[0]
    firstColor = filter_product['color'].iloc[0]
    firstHandle = filter_product['handle'].iloc[0]
    firstSku = filter_product['sku'].iloc[0]
    firstThumbNail = filter_product['image'].iloc[0]
    #updated = filter_product['updated'].iloc[0]

    embed_ = discord.Embed(title=filter_product['title'].iloc[0],
                           description="Color: " + firstColor + " | " "Price: " +
                                       str(filter_product['price'].iloc[0]), colour=discord.Colour.red(),
                           timestamp=datetime.utcnow())

    embed_.add_field(name="Size: " + filter_product['size'].iloc[0], value=filter_product['quickLink'].iloc[0],
                     inline=False)
    if not (pd.isnull(firstThumbNail)):
        embed_.set_thumbnail(url=firstThumbNail)

    for index, row in filter_product.iloc[1:].iterrows():
        grab_title = (f"{row['title']}")
        size = (f"{row['size']}")
        thumbNail = (row['image'])
        ATC = row['quickLink']
        price = row['price']
        grabHandle = row['handle']
        grabSku = row['sku']

        grabColor = row['color']

        if ((grab_title == firstVal) and (grabColor != firstColor)) or (
                (grab_title != firstVal) and (grabHandle != firstHandle)):
            embed_.set_footer(text='Powered by NotAHacker#4787')
            webhook.send(embed=embed_)

            time.sleep(5)

            firstVal = row['title']
            firstColor = row['color']
            firstHandle = row['handle']

            embed_ = discord.Embed(title=grab_title,
                                   description="Color: " + grabColor + " | " + "Price: " + str(price),
                                   colour=discord.Colour.red(), timestamp=datetime.utcnow())
            embed_.add_field(name="Size: " + str(size), value=ATC, inline=False)
            if not (pd.isnull(thumbNail)):
                embed_.set_thumbnail(url=thumbNail)

                # embed_.adds_field(name='ATC:', value=ATC)

        else:
            embed_.add_field(name="Size: " + size, value=ATC, inline=False)

    embed_.set_footer(text='Powered by NotAHacker#4787')
    webhook.send(embed=embed_)
    filter_product_copy = filter_product.copy()




# Tracking changes in an older csv file and newer csv file containign shopify data. And the goal is to track
#changes in
#when new product is added
#when product information changes
#when a product is removed




#mergeDataFrames(configure_script)
df1= pd.read_csv("BapeProduct.csv",na_values=['NA'])
df2 = pd.read_csv("NEWER_FRAMES2.csv",na_values=['NA'])

df1['version']="old"
df2['version']="new"

#df2.to_csv("NEWER_FRAME.csv")

print(len(df1))
print("NEW",len(df2))



old_accts_all = set(df1["Variant_ID"])
new_accts_all = set(df2["Variant_ID"])

#data frame of removed variants and of added variants
dropped_accts = old_accts_all - new_accts_all
added_accts = new_accts_all - old_accts_all

full_set = pd.concat([df1,df2],ignore_index=True)

full_set.drop(full_set.filter(regex="Unname"),axis=1, inplace=True)
#print(full_set)

#full_set.to_csv("full_set.csv")

#print(full_set.head(5))

# use drop_duplicates to get rid of obvious columns that have no change

changes = full_set.drop_duplicates(subset=["Variant_ID"],keep='last')


dupe_accts = changes[changes['Variant_ID'].duplicated() == True]['Variant_ID'].tolist()
dupes = changes[changes["Variant_ID"].isin(dupe_accts)]

dupes.to_csv("dupes.csv")
#next we have to figure out which variant IDS are duplicated twice
#if we see a variant ID twice that seems that one product is in stock and other not in stock indicating a change in value








'''
mergeDataFrames(configure_script)
csv = pd.read_csv("C:/Users/Andyb/PycharmProjects/Shopify-Monitor/" + configure_script['ShopifyAll'], index_col=0)
x = csv.copy()
# creates a column that puts a yes for products not in stock that we can use to check later
x['Monitor'] = np.where(x['availible'] == False, True, False)
x.to_csv("first.csv")


while(True):

    mergeDataFrames(configure_script)
    csv = pd.read_csv("C:/Users/Andyb/PycharmProjects/Shopify-Monitor/" + configure_script['ShopifyAll'], index_col=0)
    y = csv.copy()
    y['Monitor']=x['Monitor']


    conditions = [(y['Monitor'] == True) & (y['availible'] == True)]
    choices= [True]
    y['ReStock'] = np.select(conditions, choices, default=False)

    checkReStock = y[y['ReStock']==True]
    #print(len(checkReStock))
    #checkReStock.to_csv("second.csv")

    if(len(checkReStock)>0):
        checkReStock.to_csv("second.csv")
        print("---------RESTOCK----------")
        try:
            discordWebHook(configure_script,checkReStock)
        except IndexError:
            print("EXCEPTION: NO VALUES EXIST")
        else:
            break

    time.sleep(40)
    
    '''


'''
df = pd.concat([x, y])
df = df.reset_index(drop=True)
df_gpby = df.groupby(list(df.columns))
idx = [x[0] for x in df_gpby.groups.values() if len(x) == 1]
z = df.reindex(idx)

# if y has more rows or equivalent rows AND both dataframes have different rows that describe a product.
# the diff will be printed becausfe a restock or new product is is being indicated.
# if i didnt have this if condition, only out of stock things would be printed


if len(idx) != 0:
    print("------differences-------")
    new_frame = z
    try:
        new_frame = new_frame.loc[new_frame['availible'] == True]
        new_frame.to_csv("FILL.csv")
    except IndexError:
        print("EXCEPTION: True doesnt exist")
    else:
        discordWebHook(configure_script, new_frame)
        print("----UPDATING X for comparison----")
        mergeDataFrames(configure_script)
        x.to_csv("first.csv")
        y.to_csv("second.csv")
        csv = pd.read_csv("C:/Users/Andyb/PycharmProjects/Shopify-Monitor/" + configure_script['ShopifyAll'],
                          index_col=0)
        x = filterProducts(configure_script, csv)
        if (x is None):
            x = csv.copy()
        break

time.sleep(10)

configure_script['url'] += ".json?limit=800&page=0"
x = shopifyScript(configure_script)
new_frame = x.copy()
new_frame = new_frame.loc[new_frame['availible'] == True]
# new_frame.to_csv("FILL.csv")

try:
    z = new_frame.copy()

    z = z.loc[z['availible'] == True]

    discordWebHook(configure_script, z)
except IndexError:
    print("INDEX ERROR True DOESNT EXIST")df = pd.concat([x, y])
    df = df.reset_index(drop=True)
    df_gpby = df.groupby(list(df.columns))
    idx = [x[0] for x in df_gpby.groups.values() if len(x) == 1]
    z = df.reindex(idx)

    # if y has more rows or equivalent rows AND both dataframes have different rows that describe a product.
    # the diff will be printed becausfe a restock or new product is is being indicated.
    # if i didnt have this if condition, only out of stock things would be printed
    

    x['printStock'] = np.where(x['Monitor'] =="YES" and y['availible']==True, 'True', 'False')


    if len(idx) != 0:
        print("------differences-------")
        new_frame = z
        try:
            new_frame =  new_frame.loc[new_frame['availible']==True]
            new_frame.to_csv("FILL.csv")
        except IndexError:
            print("EXCEPTION: True doesnt exist")
        else:
            discordWebHook(configure_script,new_frame)
            print("----UPDATING X for comparison----")
            mergeDataFrames(configure_script)
            x.to_csv("first.csv")
            y.to_csv("second.csv")
            csv = pd.read_csv("C:/Users/Andyb/PycharmProjects/Shopify-Monitor/" + configure_script['ShopifyAll'],
                          index_col=0)
            x = filterProducts(configure_script, csv)
            if (x is None):
                x = csv.copy()
            break

    time.sleep(10)


configure_script['url'] += ".json?limit=800&page=0"
x = shopifyScript(configure_script)
new_frame = x.copy()
new_frame = new_frame.loc[new_frame['availible'] == True]
#new_frame.to_csv("FILL.csv")

try:
    z = new_frame.copy()

    z = z.loc[z['availible'] == True]

    discordWebHook(configure_script, z)
except IndexError:
    print("INDEX ERROR True DOESNT EXIST")
'''

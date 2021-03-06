from bs4 import BeautifulSoup
import requests
import json
import datetime
import codecs
import time

conHolder = {}
conHolder['name'] = 'Pathfinder 2.0 Consumable Item list'
conHolder['date'] = datetime.date.today().strftime("%B %d, %Y")


def get_consumable_multi(link):
    items = []
    string = " "
    res2 = requests.get(link)
    res2.raise_for_status()
    soup2 = BeautifulSoup(res2.text, 'lxml')
    main = soup2.find("span", {'id':'ctl00_MainContent_DetailedOutput'})
    traits = main.find_all("span", {"class" : lambda L: L and L.startswith('trai')})
    traitHolder = []
    for trait in traits:
        traitHolder.append(trait.text)
    children = main.contents
    reachedBreak = False
    reachedItem = False
    detailHolder = []
    notFirstH2 = False
    inHeader = False
    parentDetails = {}
    parentDetails['traits'] = traitHolder
    item = {}
    item['link'] = link
    tagType = ""
    itemDetailHolder = []
    for child in children:
        
        stringContents = str(child)
        if stringContents.startswith("<"):     
            if child.name == "hr":
                tagType = ""
                reachedBreak = True
                inHeader = False
            if child.name == "img":
                if not reachedItem:
                    parentDetails['actions'] = child['alt']
                else:
                    item['actions'] = child['alt']
            if child.name == "h1":
                inHeader = True
            if child.name == "h2":
                try: 
                    className = child['class'][0]
                    if notFirstH2: 
                        item['text'] = string.join(detailHolder) + string.join(itemDetailHolder)
                        for key in parentDetails.keys():
                            if key == "text":
                                item[key] += parentDetails[key]
                            elif key not in item:
                                item[key] = parentDetails[key]
                        items.append(item)
                        item = {}
                        item['link'] = link
                        itemDetailHolder = []
                    else:

                        notFirstH2 = True
                
                    reachedBreak = False
                    reachedItem = True
                    inHeader = False
                    name = child.text
                    start = child.text.find("Item")
                    item['name'] = child.text[0:start]
                except:
                    pass
            if child.name == "b":
                if(child.text != "Source"):
                    tagType = child.text.lower().replace(" ", "")
                    
            if child.name == "a":
                try:
                    if child['class'][0] == "external-link" :
                        item['source'] = child.text
                except:
                    pass
                if inHeader:
                    if tagType != "":
                        if tagType in parentDetails:
                            parentDetails[tagtype] += child.text
                        else:
                            parentDetails[tagType] = child.text

                elif reachedBreak:
                    if tagType != "":
                        if tagType in item:
                            item[tagType] += " " + child.text
                        else:
                            item[tagType] = child.text
                else:
                    tagType = ""
            if child.name == "i":
                if tagType in item:
                    item[tagType] += child.text
                else:
                    item[tagType] = child.text
        else:
            #print(reachedBreak, inHeader, reachedItem, stringContents)
            if reachedBreak:
                if(tagType != ""):
                    if not stringContents.isspace():
                        if tagType in parentDetails:
                            parentDetails[tagtype] += stringContents.strip()
                        else:
                            parentDetails[tagType] = stringContents.strip()
                        tagType = ""
                else: 
                    detailHolder.append(stringContents)
            elif inHeader:
                if tagType != "":
                    if tagType in parentDetails:
                        parentDetails[tagType] += stringContents.strip()
                    else:
                        parentDetails[tagType] = stringContents.strip()
                    tagType = ""
            elif reachedItem:
                if tagType == "level":
                    item['level'] = int(stringContents.replace(";","").strip()) 
                elif tagType != "":
                    if tagType in item:
                        item[tagType] += stringContents.strip()
                    else:
                        item[tagType] = stringContents.strip()
                else:
                    if not stringContents.isspace():
                        itemDetailHolder.append(stringContents.strip())
                tagType = ""

    for key in parentDetails.keys():
        if key == "text":
            item[key] += parentDetails[key]
        elif key not in item:
            item[key] = parentDetails[key]
    item['text'] = string.join(detailHolder + itemDetailHolder)
    items.append(item)
    
    return items

def get_ammunition(link):
    items = []
    multiItems = []
    res2 = requests.get(link)
    res2.raise_for_status()
    soup2 = BeautifulSoup(res2.text, 'lxml')
    item = soup2.find_all("div", {'class':'main'})
    table = soup2.find(lambda tag: tag.name=='table' and tag.has_attr('id') and tag['id']=="ctl00_MainContent_TreasureElement")
    rows = table.findAll(lambda tag: tag.name=='tr')
    t = 0
    for row in rows:
        t += 1
        #print(row)
        #print("-----------------------------------")
        item = {}
        entries = row.find_all(lambda tag: tag.name=='td')
        if entries is not None:
            if len(entries) > 0:
                name = entries[0].find("a").text
                if ("Type" in name) or ("Explosive" in name):
                    #print("Type")
                    start = name.find("(")
                    shortName = ""
                    if(start > 0):
                        shortName = name[0:start].strip()
                    else:
                        shortName = name
                    if shortName not in multiItems:
                        print("getting ammunition:",name)
                        ammos = get_consumable_multi("https://2e.aonprd.com/"+entries[0].find("a")['href'])
                        multiItems.append(shortName)
                        for ammo in ammos:
                            items.append(ammo)
                else:

                    item['name'] = name
                    item['link'] = "https://2e.aonprd.com/"+entries[0].find("a")['href']
                    item['category'] = "ammunition"
                    item['level'] = int(entries[1].text)
                    item['price'] = entries[2].text
                    print("getting ammunition:",item['name'])
                    itemDetails = get_consumable_details(item['link'])

                    for key in itemDetails.keys():
                        item[key] = itemDetails[key]

                    items.append(item)
        #if t > 5:
            #break
    return items

def get_consumable_details(link):
    consumDetails = {}
    itemDetails = {}
    res2 = requests.get(link)
    res2.raise_for_status()
    inHeader = False
    soup2 = BeautifulSoup(res2.text, 'lxml')
    detail = soup2.find(lambda tag: tag.name=='span' and tag.has_attr('id') and tag['id']=="ctl00_MainContent_DetailedOutput") 

    traits = detail.find_all("span", {"class" : lambda L: L and L.startswith('trai')})
    traitHolder = []
    for trait in traits:
        traitHolder.append(trait.text)
    consumDetails['traits'] = traitHolder
    children = detail.contents
    reachedBreak = False
    detailHolder = []
    tagType = ""
    for child in children:

        stringContents = str(child)
        if stringContents.startswith("<"):
            if child.name == "hr":
                tagType = ""
                reachedBreak = True
                inHeader = False
            if child.name == "img":
                consumDetails['actions'] = child['alt']
            if child.name == "h1":
                inHeader = True
            if child.name == "a":
                try:
                    if child['class'][0] == "external-link" :
                        consumDetails['source'] = child.text
                        tagType = ""
                except:
                    
                    if tagType != "":
                        if tagType in consumDetails:
                            consumDetails[tagType] += " " + child.text
                        else:
                            consumDetails[tagType] = child.text
                    else:
                        detailHolder.append(child.text)

            if child.name == "b":

                if(child.text != "Source"):
                    tagType = child.text.lower().replace(" ", "")
            if child.name == "img":
                consumDetails['actions'] = child['alt']
            if child.name == "i":
                if tagType != "":
                    if tagType in consumDetails:
                        consumDetails[tagType] += child.text
                    else:
                        consumDetails[tagType] = child.text
                else:
                    if(reachedBreak):
                        detailHolder.append(child.text) 
            #else:
                #if not stringContents.isspace() :
                    #detailHolder.append(child.text)        
        else:

            if reachedBreak:
                if tagType != "":
                    if not stringContents.isspace():
                        if tagType in consumDetails:
                            consumDetails[tagType] += stringContents
                        else:
                            consumDetails[tagType] = stringContents
                else:
                    if not stringContents.isspace() :
                        detailHolder.append(stringContents)
            else:
                if tagType != "":
                    if (tagType != "Bulk") & (tagType!= "Price"):
                        if not stringContents.isspace():
                            if tagType in consumDetails:
                                consumDetails[tagType] += stringContents
                            else:
                                consumDetails[tagType] = stringContents
                

       #print(child)
        string = " "
        consumDetails['text'] = string.join(detailHolder)
    return consumDetails

def get_oils(link):
    items = []
    multiItems = []
    res2 = requests.get(link)
    res2.raise_for_status()
    soup2 = BeautifulSoup(res2.text, 'lxml')
    item = soup2.find_all("div", {'class':'main'})
    table = soup2.find(lambda tag: tag.name=='table' and tag.has_attr('id') and tag['id']=="ctl00_MainContent_TreasureElement")
    rows = table.findAll(lambda tag: tag.name=='tr')
    t = 0
    for row in rows:
        t += 1
        #print(row)
        #print("-----------------------------------")
        item = {}
        entries = row.find_all(lambda tag: tag.name=='td')
        if entries is not None:
            if len(entries) > 0:
                name = entries[0].find("a").text
                if ("Weightlessness" in name) or ("Antiparalysis" in name):
                    #print("Type")
                    start = name.find("(")
                    shortName = ""
                    if(start > 0):
                        shortName = name[0:start].strip()
                    else:
                        shortName = name
                    if shortName not in multiItems:
                        print("getting oil:",name)
                        oils = get_consumable_multi("https://2e.aonprd.com/"+entries[0].find("a")['href'])
                        multiItems.append(shortName)
                        for oil in oils:
                            items.append(oil)
                else:

                    item['name'] = name
                    item['link'] = "https://2e.aonprd.com/"+entries[0].find("a")['href']
                    item['category'] = "oil"
                    item['level'] = int(entries[1].text)
                    item['price'] = entries[2].text
                    print("getting oil:",item['name'])
                    itemDetails = get_consumable_details(item['link'])

                    for key in itemDetails.keys():
                        item[key] = itemDetails[key]

                    items.append(item)
        #if t > 5:
            #break
    return items

def get_others(link):
    items = []
    multiItems = []
    res2 = requests.get(link)
    res2.raise_for_status()
    soup2 = BeautifulSoup(res2.text, 'lxml')
    item = soup2.find_all("div", {'class':'main'})
    table = soup2.find(lambda tag: tag.name=='table' and tag.has_attr('id') and tag['id']=="ctl00_MainContent_TreasureElement")
    rows = table.findAll(lambda tag: tag.name=='tr')
    t = 0
    for row in rows:
        t += 1
        #print(row)
        #print("-----------------------------------")
        item = {}
        entries = row.find_all(lambda tag: tag.name=='td')
        if entries is not None:
            if len(entries) > 0:
                name = entries[0].find("a").text
                if ("Feather" in name):
                    #print("Type")
                    start = name.find("(")
                    shortName = ""
                    if(start > 0):
                        shortName = name[0:start].strip()
                    else:
                        shortName = name
                    if shortName not in multiItems:
                        print("getting name:",name)
                        others = get_consumable_multi("https://2e.aonprd.com/"+entries[0].find("a")['href'])
                        multiItems.append(shortName)
                        for other in others:
                            other['category'] = "other"
                            items.append(other)
                else:

                    item['name'] = name
                    item['link'] = "https://2e.aonprd.com/"+entries[0].find("a")['href']
                    item['category'] = "other"
                    item['level'] = int(entries[1].text)
                    item['price'] = entries[2].text
                    item['bulk'] = entries[3].text
                    print("getting other:",item['name'])
                    itemDetails = get_consumable_details(item['link'])

                    for key in itemDetails.keys():
                        item[key] = itemDetails[key]

                    items.append(item)
        #if t > 5:
            #break
    return items

def get_potions(link):
    items = []
    multiItems = []
    res2 = requests.get(link)
    res2.raise_for_status()
    soup2 = BeautifulSoup(res2.text, 'lxml')
    item = soup2.find_all("div", {'class':'main'})
    table = soup2.find(lambda tag: tag.name=='table' and tag.has_attr('id') and tag['id']=="ctl00_MainContent_TreasureElement")
    rows = table.findAll(lambda tag: tag.name=='tr')
    t = 0
    for row in rows:
        t += 1
        #print(row)
        #print("-----------------------------------")
        item = {}
        entries = row.find_all(lambda tag: tag.name=='td')
        if entries is not None:
            if len(entries) > 0:
                name = entries[0].find("a").text
                if ("(" in name) or ("Shrinking" in name) or ("Flying" in name):
                    #print("Type")
                    start = name.find("(")
                    shortName = ""
                    if(start > 0):
                        shortName = name[0:start].strip()
                    else:
                        shortName = name
                    if shortName not in multiItems:
                        print("getting potion:",name)
                        potions = get_consumable_multi("https://2e.aonprd.com/"+entries[0].find("a")['href'])
                        multiItems.append(shortName)
                        for potion in potions:
                            potion['category'] = "potion"
                            items.append(potion)
                else:

                    item['name'] = name
                    item['link'] = "https://2e.aonprd.com/"+entries[0].find("a")['href']
                    item['category'] = "potion"
                    item['level'] = int(entries[1].text)
                    item['price'] = entries[2].text
                    
                    print("getting potion:",item['name'])
                    itemDetails = get_consumable_details(item['link'])

                    for key in itemDetails.keys():
                        item[key] = itemDetails[key]

                    items.append(item)
        #if t > 5:
            #break
    return items

def get_talismans(link):
    items = []
    multiItems = []
    res2 = requests.get(link)
    res2.raise_for_status()
    soup2 = BeautifulSoup(res2.text, 'lxml')
    item = soup2.find_all("div", {'class':'main'})
    table = soup2.find(lambda tag: tag.name=='table' and tag.has_attr('id') and tag['id']=="ctl00_MainContent_TreasureElement")
    rows = table.findAll(lambda tag: tag.name=='tr')
    t = 0
    for row in rows:
        time.sleep(1)
        t += 1
        #print(row)
        #print("-----------------------------------")
        item = {}
        entries = row.find_all(lambda tag: tag.name=='td')
        if entries is not None:
            if len(entries) > 0:
                name = entries[0].find("a").text

                item['name'] = name
                item['link'] = "https://2e.aonprd.com/"+entries[0].find("a")['href']
                item['category'] = "talisman"
                item['level'] = int(entries[1].text)
                item['price'] = entries[2].text
                
                print("getting talisman:",item['name'])
                itemDetails = get_consumable_details(item['link'])

                for key in itemDetails.keys():
                    item[key] = itemDetails[key]

                items.append(item)
        #if t > 5:
            #break
    return items

def get_all():
    conHolder['ammunition'] = get_ammunition("https://2e.aonprd.com/Equipment.aspx?Category=15&Subcategory=16")
    conHolder['oil'] = get_oils("https://2e.aonprd.com/Equipment.aspx?Category=15&Subcategory=17")
    conHolder['other'] = get_others("https://2e.aonprd.com/Equipment.aspx?Category=15&Subcategory=20")
    conHolder['potions'] = get_potions("https://2e.aonprd.com/Equipment.aspx?Category=15&Subcategory=18")
    conHolder['talismans'] = get_talismans("https://2e.aonprd.com/Equipment.aspx?Category=15&Subcategory=19")
    
    return conHolder

#print(get_all())
json_data = json.dumps(get_all(), indent=4)
#print(json_data)
filename = "consumables-pf2.json"
f = open(filename, "w")
f.write(json_data)
f.close
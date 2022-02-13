# -*- coding: utf-8 -*-
"""
Created on Thu Apr 15 15:40:58 2021

@author: yjian
"""


"""
--- this file is for Yelp data collection using web crawler ---

"""
#%%
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import pandas as pd
import os
import json

#%%
dict_business = {}

#%%
""" search restaurants in certain location """

headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36'}
url='https://www.yelp.com/search?cflt=restaurants&find_loc=Las Vegas, NV'

response=requests.get(url,headers=headers).text

soup=BeautifulSoup(response,'html.parser') 

#%%
""" find total page number """
page_num = soup.select('[aria-label*="Pagination navigation"]')[0].find_all('span')[-1].get_text()
    
total_page_num = int(page_num.split(' ')[-1])

#%%
""" business information """

for num in tqdm(range(total_page_num)):
    url_search = url+'&start='+str(10*num)
    response = requests.get(url_search,headers=headers).text
    soup = BeautifulSoup(response,'html.parser')
   
    for item in soup.select('[class*=container]'):
        try:
            if item.find('h4') and item.select('[class*=priceRange]'):
                name = item.find('h4').get_text()
                print(name)
                print(item.select('[class*=reviewCount]')[0].get_text())
                print(item.select('[aria-label*=rating]')[0]['aria-label'])
                print(item.select('[class*=secondaryAttributes]')[0].get_text())
                print(item.select('[class*=priceRange]')[0].get_text())
                print(item.select('[class*=priceCategory]')[0].get_text())
                print(item.find_all('a')[-1]['href'])
                print('------------------')
                dict_business[name] = {'business info':{'restaurant name':name,\
                                       'review count':item.select('[class*=reviewCount]')[0].get_text(),\
                                       'rating':item.select('[aria-label*=rating]')[0]['aria-label'],
                                       'attributes':item.select('[class*=secondaryAttributes]')[0].get_text(),\
                                       'price range':item.select('[class*=priceRange]')[0].get_text(),\
                                       'price category':item.select('[class*=priceCategory]')[0].get_text(),\
                                       'link':item.find_all('a')[-1]['href']}}
        except Exception as e:
            raise e
            print('error')


    


#%%
for name in dict_business.keys():
    dict_business[name]['business info']['review count'] = int(dict_business[name]['business info']['review count'])

dict_temp = {}
for name in dict_business.keys():
    dict_temp[name] = dict_business[name]['business info']
    
df_business = pd.DataFrame.from_dict(dict_temp).T

df_business = df_business.sort_values(by = 'review count',axis = 0,ascending = False)
df_business.index = range(1,len(df_business)+1)

del dict_temp

    


















#%%
""" save results """
path = r'C:\Users\yjian\OneDrive\Documents\research files\dissertation\Yelp Fake Reviews\Yelp data collection\Las Vegas'

with open(os.path.join(path, 'Las Vegas.json'), 'w+', encoding="utf-8") as outfile:
    json.dump(dict_business, outfile, ensure_ascii=False) 



#%%
""" other code """  

#%%
""" import business info """
path = r'C:\Users\yjian\OneDrive\Documents\research files\dissertation\Yelp Fake Reviews\Yelp data collection'
path_business = os.path.join(path,'Seattle')

with open(os.path.join(path_business, 'Seattle.json'), 'r', encoding="utf-8") as file:
    for line in file.readlines():
        dict_business = json.loads(line)


#%%

""" str -> int """
for name in dict_business.keys():
    dict_business[name]['business info']['review count'] = int(dict_business[name]['business info']['review count'])

dict_temp = {}
for name in dict_business.keys():
    dict_temp[name] = dict_business[name]['business info']
    
df_business = pd.DataFrame.from_dict(dict_temp).T

df_business = df_business.sort_values(by = 'review count',axis = 0,ascending = False)
df_business.index = range(1,len(df_business)+1)


#%%
# remove sponsored results
for i in range(len(soup.find_all('li'))):
    for element in soup.find_all('li')[i].find_all('h3'):
        if element.get_text() == 'All Results':
            list_search = soup.find_all('li')[i:-1]
        if element.get_text() == 'Sponsored Result':
            list_search = list_search[0:i]
            
  


#%%
""" collect reviews & other information from top-10 restaurants based on review number """

for i in range(10):
    name = df_business.iloc[i]['restaurant name']
    url_business = 'http://www.yelp.com'+df_business.iloc[i]['link']
    response = requests.get(url_business,headers=headers).text
    soup = BeautifulSoup(response,'html.parser')
    
    # collect business information
    for item in soup.select('[class*=margin-b2]'):
        ## covid-19 updates
        if item.find('p'):
            dict_business[name]['business info']['covid-19 updates'] = item.get_text()
            continue
        if item.find('h5') and item.find('span'):
            for element in item.select('[class*=margin-b2]'):
                ## updated service
                if 'Updated Services' in element.get_text():
                    condition = 'updated services'
                ## health & safety measures
                elif 'Health & Safety Measures' in element.get_text():
                    condition = 'health & safety measures'
                dict_business[name]['business info'][condition] = {}
                for j in range(len(element.select('[class*=margin-t2]')[0].select('[class*=display--inline-block]'))):
                    if j % 2 == 0:
                        ### remove irrelevant characters
                        service = element.select('[class*=margin-t2]')[0].select('[class*=display--inline-block]')[0].get_text().split('According')[0]
                        if 'M9.46' in element.select('[class*=margin-t2]')[0].select('[class*=display--inline-block]')[0].find('path')['d']:
                                dict_business[name]['business info'][condition][service] = 'Yes'
                        elif 'M13.41' in element.select('[class*=margin-t2]')[0].select('[class*=display--inline-block]')[0].find('path')['d']:
                            dict_business[name]['business info'][condition][service] = 'No'
            # the first element with h5 and span contains all the info so break the current loop
            break
    # collect reviews
    list_reviews = soup.find_all("li",{"class":"lemon — li__373c0__1r9wz margin-b3__373c0__q1DuY padding-b3__373c0__342DA border — bottom__373c0__3qNtD border-color — default__373c0__3-ifU"})
        
    
    
    
    break









# -*- coding: utf-8 -*-
"""
Created on Tue Apr 27 10:37:10 2021

@author: yjian
"""

"""
   --- this file is for visualize the star-rating of Yelp businesses --- 
   
"""

#%%
import json
import os
import pandas as pd
from matplotlib import pyplot as plt
import re
from tqdm import tqdm
from datetime import datetime, timedelta

#%%
""" import data """

path = r'C:\Users\yjian\OneDrive\Documents\research files\dissertation\Yelp Fake Reviews\Yelp data collection\LA\reviews'

filenames = os.listdir(path)

#%%

with open(os.path.join(path, filenames[0]), 'r', encoding="utf-8") as file:
    for line in file.readlines():
        dict_business =  json.loads(line)

#%%
""" review processing """

dict_reviews = {}

for review_num in dict_business['reviews'].keys():
    dict_reviews[review_num] = {'star-rating': int(re.findall(r"\d+\.?\d*",dict_business['reviews'][review_num]['review_info']['review_rating'])[0]),
                                'review_date': datetime.strptime(dict_business['reviews'][review_num]['review_info']['review_date'][0:10].strip(),"%m/%d/%Y"),
                                'review_type': 'recommended'}
    
for review_num in dict_business['not recommended reviews'].keys():
    dict_reviews[review_num] = {'star-rating': int(re.findall(r"\d+\.?\d*",dict_business['not recommended reviews'][review_num]['review info']['review rating'])[0]),
                                'review_date': datetime.strptime(dict_business['not recommended reviews'][review_num]['review info']['review_date'][0:10].strip(),"%m/%d/%Y"),
                                'review_type': 'not recommended'}

#%%
""" extract star-rating, review_type and review_date"""

df_reviews = pd.DataFrame.from_dict(dict_reviews).T

df_reviews = df_reviews.sort_values(by = 'review_date', axis = 0, ascending = False)

#%%
""" sort data by review data """

df_dates = df_reviews.review_date.value_counts()
df_dates = df_dates.sort_index(ascending = False)
df_dates = pd.DataFrame(df_dates)

#%%
""" sort data by review type: recommended, not recommended """

df_rec = df_reviews[df_reviews.review_type == 'recommended']
df_nrec = df_reviews[df_reviews.review_type == 'not recommended']

#%%
""" add columns for df_dates """

df_dates['recommended'] = df_rec.review_date.value_counts().sort_index(ascending = False)
df_dates['not_recommended'] = df_nrec.review_date.value_counts().sort_index(ascending = False)

# replace nan by 0
df_dates = df_dates.fillna(0)
df_dates.rename(columns={'review_date':'review_count'}, inplace = True)

#%%
""" plot: review count """

plt.style.use('ggplot')
fig = plt.figure(dpi = 80, figsize = (15, 5))
fig.suptitle('review count per day', fontsize=30)
plt.plot(df_dates.index, df_dates.review_count,color='k',label='count')
plt.tick_params(labelsize=20,rotation=45)
#plt.xticks(index, y_test.index.values,fontsize = 16,rotation=45)
plt.xlabel('date', fontsize=25)
plt.ylabel('count', fontsize=25)
plt.legend()
plt.show()

fig

#%%
""" plot: scatter plot of review star-ratings """

plt.style.use('ggplot')
fig = plt.figure(dpi = 80, figsize = (15, 5))
fig.suptitle('review star-rating', fontsize=30)
plt.plot(df_rec.review_date, df_rec['star-rating'],'o',color='r',label='Recommended Reviews')
plt.plot(df_nrec.review_date, df_nrec['star-rating'],'o',color='b',label='Not-Recommended Reviews')
plt.tick_params(labelsize=15,rotation=45)
plt.yticks([1,2,3,4,5],fontsize=15)
plt.xlabel('date', fontsize=20)
plt.ylabel('Star-rating', fontsize=25)
plt.xlim(xmin=datetime(2021,1,1),xmax=max(df_rec.review_date))
plt.legend(fontsize=12,loc='best')
plt.show()

fig
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 18 23:05:28 2021

@author: yjian
"""


"""
--- crawler for Yelp review data based on selenium ---

"""
#%%
from bs4 import BeautifulSoup
from selenium import webdriver
import time
import requests
import json
import os
import pandas as pd
import string
import re
from tqdm import tqdm

#%%
createVar = locals()

#%%
""" import business info """
path = r'C:\Users\yjian\OneDrive\Documents\research files\dissertation\Yelp Fake Reviews\Yelp data collection\Las Vegas'
path_business = os.path.join(path,'reviews')

with open(os.path.join(path, 'Las Vegas.json'), 'r', encoding="utf-8") as file:
    for line in file.readlines():
        dict_lv = json.loads(line)


#%%
""" dict -> df """
""" str -> int """

for name in dict_lv.keys():
    dict_lv[name]['business info']['review count'] = int(dict_lv[name]['business info']['review count'])

dict_temp = {}
for name in dict_lv.keys():
    dict_temp[name] = dict_lv[name]['business info']
    
df_lv = pd.DataFrame.from_dict(dict_temp).T

df_lv = df_lv.sort_values(by = 'review count',axis = 0,ascending = False)
df_lv.index = range(1,len(df_lv)+1)

del dict_temp


#%%

list_linkstring = ['&','?']
list_user_count = ['Friends','Reviews','Photos']

#%%
""" select business """
filenames = os.listdir(path_business)
if filenames == []:
    business_num = 0
else:
    business_num = len(filenames)-1 # the latest business data may be incomplete

#%%

while business_num <= 91:
    
    print('current business num is:', business_num, 'current_time is:', time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))

    """ initialize browser """
    driver = webdriver.Chrome(r'C:\Users\yjian\OneDrive\Documents\research files\dissertation\Yelp Fake Reviews\Yelp data collection\chromedriver_win32\chromedriver.exe')
    
    # temp url, may revise aftering accessing it
    url = 'https://www.yelp.com'+df_lv.iloc[business_num]['link']

    """ open webpage """
    driver.get(url)
    time.sleep(5) # Let the user actually see something!
    soup = BeautifulSoup(driver.page_source,'html.parser')   
    
    # if error in reading page source, retry 3 times
    count_reading = 0
    while (soup.select('[aria-label*="Pagination navigation"]') == []) and (count_reading < 3):
        print('re-open the page')
        driver.quit()
        driver = webdriver.Chrome(r'C:\Users\yjian\Downloads\chromedriver_win32\chromedriver.exe')
        driver.get(url)
        time.sleep(10) # waiting for response
        soup = BeautifulSoup(driver.page_source,'html.parser')
        count_reading += 1
        if soup.select('[aria-label*="Pagination navigation"]') != []:
            print('business initial page is successfully opened')
            break
    
    
    """ get page_num """
    page_num = soup.select('[aria-label*="Pagination navigation"]')[0].find_all('span')[-1].get_text()
    total_page_num = int(page_num.split(' ')[-1])

    """ collect business info """
    for item in soup.select('[type*="application/json"]'):
        if 'businessId' in item.text:
            dict_temp = json.loads(item.text[4:-3])
            business_id = dict_temp['bizDetailsPageProps']['businessId']
            dict_business = {'business info':dict_lv[df_lv.iloc[business_num]['restaurant name']]['business info'],\
                             'reviews':{}, 'not recommended reviews':{}}
            dict_business['business info']['business_id']=business_id
    
    for item in soup.select('[class*=margin-b2]'):
        if item.find('span') and item.find('h5') and len(item.find_all('h5')) == 2:
            for element in item.select('[class*=margin-b2]'):    
                # updated service
                if 'Updated Services' in element.text:
                    condition = 'updated services'
                ## health & safety measures
                elif 'Health & Safety Measures' in element.get_text():
                    condition = 'health & safety measures'
                dict_business['business info'][condition] = {}
                for j in range(len(element.select('[class*=margin-t2]')[0].select('[class*=display--inline-block]'))):
                    if j % 2 == 0:
                        ### remove irrelevant characters
                        service = element.select('[class*=margin-t2]')[0].select('[class*=display--inline-block]')[j].get_text().split('According')[0]
                        if 'M9.46' in element.select('[class*=margin-t2]')[0].select('[class*=display--inline-block]')[j].find('path')['d']:
                                dict_business['business info'][condition][service] = 'Yes'
                        elif 'M13.41' in element.select('[class*=margin-t2]')[0].select('[class*=display--inline-block]')[j].find('path')['d']:
                            dict_business['business info'][condition][service] = 'No'
                            
    """ may revise the url here """
    url_base = dict_temp['staticUrl']
    
    """ try different linkstring """
    for char in list_linkstring:
        print('current linkstring is',str(char))
        # open the second review page, check if it is correctly opened
        # and compare its content with the first page
        url = url_base+char+'start='+str(10)
        driver.get(url)
        time.sleep(5) # Let the user actually see something!
        soup_second = BeautifulSoup(driver.page_source,'html.parser')   
    
        ## if error in reading page source, retry 3 times
        count_reading = 0
        while (soup_second.select('[class*= "error-page"]') != []) and (count_reading < 3):
            print('re-open the page')
            driver.quit()
            driver = webdriver.Chrome(r'C:\Users\yjian\Downloads\chromedriver_win32\chromedriver.exe')
            driver.get(url)
            time.sleep(10) # waiting for response
            soup_second = BeautifulSoup(driver.page_source,'html.parser')
            count_reading += 1
            if soup_second.select('[class*= "error-page"]') == []:
                print('page is successfully opened')
                page_opened = True
                break
        ## if still error in reading the page source, try the next linkstring
        if (count_reading >= 3) and (soup_second.select('[class*= "error-page"]') != []):
            print('error in reading the page using linkstring',str(char),'try the other one')
            continue
        ## if page is successfully opened, compare its content with the initial page
        if (soup_second.select('[class*= "error-page"]') == []) and\
            (soup.select('[class*="review__373c0__13kpL"]') != soup_second.select('[class*="review__373c0__13kpL"]')):
                linkstring = char
                print('linkstirng',str(char),'is successfully determined')
                break

    
    # not-recommented reviews
    dict_business['business info']['link_not_recommended_reviews'] = soup.select('[href*="not_recommended"]')[0]['href']
    
    """ collect review&user info """
    # since there's no review id, we save the review by the collecting order
    review_count = 0
    num = 0 # page num
    
    # dict of errors
    dict_error = {'reviews':{},'fake reviews':{}}

    """ reading reviews """
    while num < total_page_num:
        try:
            print('\n')
            print('start page ', str(num), 'current time is:', time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
            
            if num == 0:
                # the first review overall might be repliacte on other pages, 
                #so save and compare it for each page
                item_firstreview = soup.select('[class*="review__373c0__13kpL"]')[0]
            
            elif num != 0:
                # get all source code from the targeted webpage
                url = url_base+linkstring+'start='+str(num*10)
                driver.get(url)
                time.sleep(3) # Let the user actually see something!
                soup = BeautifulSoup(driver.page_source,'html.parser')
                
                if num % 50 == 0:
                    # take a break after reading 50 pages of reviews
                    time.sleep(60) 
                if num % 100 == 0:
                    # save dataset
                    with open(os.path.join(path_business, str(business_id)+'.json'), 'w+', encoding="utf-8") as outfile:
                        json.dump(dict_business, outfile, ensure_ascii=False)          
                        
                # search reviews
            for item in soup.select('[class*="review__373c0__13kpL"]'):
                try:
                    # the first review overall might be repliacte on other pages, 
                    # so compare it for each page
                    if (soup.select('[class*="review__373c0__13kpL"]').index(item) == 0) and (num > 0)\
                        and (item == item_firstreview):
                            print('replicate review')
                            continue
                    
                    dict_business['reviews'][str(review_count)] = {'user_info':{'user_link':'', 'user_id':'','user_name':''},\
                                                                   'review_info':{}}
                    ## user info
                    ### user link, id, name, location, elite info
                    #### user link
                    if item.select('[class*="user-passport-info"]')[0].select('[class="css-166la90"]') != []:
                        dict_business['reviews'][str(review_count)]['user_info']['user_link'] = \
                            item.select('[class*="user-passport-info"]')[0].select('[class="css-166la90"]')[0]['href']
                        #### user id
                        dict_business['reviews'][str(review_count)]['user_info']['user_id'] = \
                            item.select('[class*="user-passport-info"]')[0].select('[class="css-166la90"]')[0]['href'].split('userid=')[-1]
                        #### user name
                        dict_business['reviews'][str(review_count)]['user_info']['user_name'] = \
                            item.select('[class*="user-passport-info"]')[0].select('[class="css-166la90"]')[0].text
                        user_link = True
                    else:
                        user_link = False
                    #### user location
                    if item.select('[class*="user-passport-info"]')[0].select('[class*="responsive-hidden-small"]') == []:
                        dict_business['reviews'][str(review_count)]['user_info']['user_location'] = ''
                    else:
                        dict_business['reviews'][str(review_count)]['user_info']['user_location'] = \
                            item.select('[class*="user-passport-info"]')[0].select('[class*="responsive-hidden-small"]')[0].text
                    ### user elite info
                    if item.select('[class*="user-passport-info"]')[0].select('[class*="elite-badge"]') != []:
                        user_elite = True
                    else: user_elite = False
                    
                    ## review info
                    ### review star-rating, date, num of photo, text, votes
                    dict_business['reviews'][str(review_count)]['review_info']['review_rating'] = \
                        item.select('[class*="i-stars"]')[0]['aria-label']
                    dict_business['reviews'][str(review_count)]['review_info']['review_date'] = \
                        item.select('[class*="css-e81eai"]')[0].text
                    if item.select('[class*="css-1x0u7iy"]') != []:
                        dict_business['reviews'][str(review_count)]['review_info']['review_photo_count'] = \
                            item.select('[class*="css-1x0u7iy"]')[0].text.split(' photo')[0]
                    else:
                        dict_business['reviews'][str(review_count)]['review_info']['review_photo_count'] = '0'
                    dict_business['reviews'][str(review_count)]['review_info']['review_text'] = \
                        item.select('[class*=comment]')[0].text
                    for element in item.select('[class*="css-1ha1j8d"]'):
                        votetype = element.text.split(' ')[0].lower()
                        # if no num
                        if re.compile('[0-9]+').findall(element.text) == []:
                            dict_business['reviews'][str(review_count)]['review_info']['review_vote_'+votetype] = '0'
                        else:
                            dict_business['reviews'][str(review_count)]['review_info']['review_vote_'+votetype] = \
                                element.text.split(' ')[-1]
                    
                    if user_link == True:
                        ## addtional user info
                        url_user = 'https://www.yelp.com'+item.select('[class*="user-passport-info"]')[0].select('[class="css-166la90"]')[0]['href']
                        driver.get(url_user)
                        time.sleep(3) # Let the user actually see something!
                        soup_user = BeautifulSoup(driver.page_source,'html.parser')
    
                        count_reading = 0
                        user_removed = False
                        while (soup_user.select('[class*="user-profile_info arrange_unit"]') == [])\
                            and (count_reading < 100):
                            print('re-open the page')
                            driver.quit()
                            driver = webdriver.Chrome(r'C:\Users\yjian\Downloads\chromedriver_win32\chromedriver.exe')
                            driver.get(url_user)
                            time.sleep(10) # waiting for response
                            soup_user = BeautifulSoup(driver.page_source,'html.parser')
                            count_reading += 1
                            if soup_user.select('[class*="user-profile_info arrange_unit"]') != []:
                                print('page is successfully opened')
                            elif 'This user has been removed' in soup_user.text:
                                user_removed = True
                                print('this user account has been removed, collect user data from review page')
                                break
                        
                        if user_removed == True:
                            # collect user friends&review&photo count if exists
                            if item.select('[class*="user-passport-stats"]') != []:
                                for element in item.select('[class*="user-passport-stats"]')[0].select('[aria-label]'):
                                    if element['aria-label'] in list_user_count:
                                        count_type = element['aria-label'].lower().strip('s')
                                        dict_business['reviews'][str(review_count)]['user_info']['user_'+count_type+'_count'] = \
                                            element.text
                            # if no more user info, or collection finished, then continue to the next review
                            print('collection of removed user finished, go to the next review')
                            continue
                            
                        
                        ### user friend count, review count, photo count
                        dict_business['reviews'][str(review_count)]['user_info']['user_friend_count'] = \
                            re.findall(r"\d+\.?\d*",soup_user.select('[class*="user-profile_info arrange_unit"]')[0].select('[class*="friend-count"]')[0].text)[0]
                        dict_business['reviews'][str(review_count)]['user_info']['user_review_count'] = \
                            re.findall(r"\d+\.?\d*",soup_user.select('[class*="user-profile_info arrange_unit"]')[0].select('[class*="review-count"]')[0].text)[0]
                        dict_business['reviews'][str(review_count)]['user_info']['user_photo_count'] = \
                            re.findall(r"\d+\.?\d*",soup_user.select('[class*="user-profile_info arrange_unit"]')[0].select('[class*="photo-count"]')[0].text)[0]
                        ### user elite info
                        if user_elite == True:
                            list_user_eliteyear = re.findall(r"\d+\.?\d*",soup_user.select('[class*="user-profile_info arrange_unit"]')[0].select('[class*="badge-bar u-space"]')[0].text)
                            for i in range(len(list_user_eliteyear)):
                                if len(list_user_eliteyear[i]) < 4:
                                    list_user_eliteyear[i] = '20'+ list_user_eliteyear[i]
                            dict_business['reviews'][str(review_count)]['user_info']['user_elite_year'] = \
                                list_user_eliteyear
                        ### user review votes, follower, yelping since
                        #### initial vote count
                        dict_business['reviews'][str(review_count)]['user_info']['user_vote_useful'] = '0'
                        dict_business['reviews'][str(review_count)]['user_info']['user_vote_funny'] = '0'
                        dict_business['reviews'][str(review_count)]['user_info']['user_vote_cool'] = '0'
                
                        for element in soup_user.select('[class*="user-details-overview_sidebar"]')[0].select('[class*=ysection]'):
                            if 'Review Votes' in element.text:
                                list_user_votecount = re.findall(r"\d+\.?\d*",element.text)
                                list_user_votetype = \
                                    re.sub(r"[^A-Za-z\s]", " ", element.text.replace('Review Votes','').strip()).split()
                                for i in range(len(list_user_votetype)):
                                    dict_business['reviews'][str(review_count)]['user_info']['user_vote_'+list_user_votetype[i].lower()] = \
                                        list_user_votecount[i]
                                continue
                            if ('Followers' in element.text) and ('Stats' in element.text):
                                list_stats_count = re.findall(r"\d+\.?\d*",element.text)
                                list_stats_type = \
                                    re.sub(r"[^A-Za-z\s]", " ",element.text.replace('Stats','').replace(' ','')).split()
                                i = list_stats_type.index('Followers')
                                dict_business['reviews'][str(review_count)]['user_info']['user_followers'] = \
                                    list_stats_count[i]
                                continue
                            if 'Yelping Since' in element.text:
                                list_attr = list(filter(None,element.text.split('\n')))
                                i = list_attr.index('Yelping Since')
                                dict_business['reviews'][str(review_count)]['user_info']['user_yelpingsince'] = \
                                    list_attr[i+1]
                        ## followers = 0 if 'followers' not in content
                        if 'Followers' not in soup_user.select('[class*="user-details-overview_sidebar"]')[0].text:
                            dict_business['reviews'][str(review_count)]['user_info']['user_followers'] = '0'
                                    
                    review_count += 1
                
                except Exception as e:
                    
                    print('review/user error')
                    dict_error['reviews']['page_'+str(num)] = 'review_count: '+str(review_count)
                    raise e
                    
            num += 1   
            
        except Exception as e:
            
            print('review page error')
            raise e
                   
    ############################################################
    """ 
    --- collect not-recommended reviews ---
    
    """
    print('\n\n\n\n\n')
    print('***********************************************************************')
    print('start not-recommended reviews, current time is:', time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
            
    
    url_not_recommended = 'http://www.yelp.com'+dict_business['business info']['link_not_recommended_reviews']
    
    driver.get(url_not_recommended)
    time.sleep(3) # Let the user actually see something!
    soup_fake = BeautifulSoup(driver.page_source,'html.parser')
    
    
    """ total page num of not recommended reviews """
    total_page_num = int(soup_fake.select('[class*="ysection not-recommended-reviews review-list-wide"]')[0].select('[class*="page-of-pages"]')[0].text.strip().split('of ')[-1])
    
    url_base_fakereview = soup_fake.select('[class*="ysection not-recommended-reviews review-list-wide"]')[0].select('[class*="available-number pagination-links_anchor"]')[0]['href'].split('start=')[0]
    
    #url_base_user = 'https://www.yelp.com/user_details?userid='

    # initial page num
    num = 0
    
    ## review count is continued from normal reviews
    review_count = len(dict_business['reviews'])
    
    
    while num < total_page_num:
        try:
            print('\n')
            print('start page ', str(num), 'current time is:', time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))      
            
            if num != 0:
                url_not_recommended = 'https://www.yelp.com'+url_base_fakereview+'start='+str(10*num)
                driver.get(url_not_recommended)
                time.sleep(3) # Let the user actually see something!
                soup_fake = BeautifulSoup(driver.page_source,'html.parser')
                
            ## if error in reading page source, retry 3 times
            count_reading = 0
            while (soup_fake.select('[class*="ysection not-recommended-reviews review-list-wide"]') == []) and (count_reading < 3):
                print('re-open the page')
                driver.quit()
                driver = webdriver.Chrome(r'C:\Users\yjian\Downloads\chromedriver_win32\chromedriver.exe')
                driver.get(url)
                time.sleep(10) # waiting for response
                soup_fake = BeautifulSoup(driver.page_source,'html.parser')
                count_reading += 1
                if soup_fake.select('[class*="ysection not-recommended-reviews review-list-wide"]') != []:
                    print('page is successfully opened')
                    page_opened = True
                    break            

            try:
                # search reviews
                for item in soup_fake.select('[class*="ysection not-recommended-reviews review-list-wide"]')[0].select('[class*="review review--with-sidebar"]'):
                    dict_business['not recommended reviews'][str(review_count)] = \
                        {'user info':{},'review info':{}}
                    ## user info, location, id ? (!!!! this id is not user id, but save it just in case),
                    dict_business['not recommended reviews'][str(review_count)]['user info']['user_name'] = \
                        item.select('[class="user-name"]')[0].text.strip()
                    if item.select('[class="user-display-name"]') == []:
                        dict_business['not recommended reviews'][str(review_count)]['user info']['id'] = ''
                    else:
                        dict_business['not recommended reviews'][str(review_count)]['user info']['id'] = \
                            item.select('[class="user-display-name"]')[0]['data-hovercard-id']
                    if item.select('[class*="user-location"]') == []:
                        dict_business['not recommended reviews'][str(review_count)]['user info']['user_location'] = []
                    else:
                        dict_business['not recommended reviews'][str(review_count)]['user info']['user_location'] = \
                            item.select('[class*="user-location"]')[0].text.strip()
                    
                    ## user friend, review, photo count
                    if item.select('[class*="friend-count"]') != []:
                        dict_business['not recommended reviews'][str(review_count)]['user info']['user_friend_count'] = \
                            re.findall(r"\d+\.?\d*",item.select('[class*="friend-count"]')[0].text)[0]
                    else:
                        dict_business['not recommended reviews'][str(review_count)]['user info']['user_friend_count'] = '0'
                    if item.select('[class*="review-count"]') != []:
                        dict_business['not recommended reviews'][str(review_count)]['user info']['user_review_count'] = \
                            re.findall(r"\d+\.?\d*",item.select('[class*="review-count"]')[0].text)[0]
                    else:
                        dict_business['not recommended reviews'][str(review_count)]['user info']['user_review_count'] = '0'
                    if item.select('[class*="photo-count"]') != []:
                        dict_business['not recommended reviews'][str(review_count)]['user info']['user_photo_count'] = \
                            re.findall(r"\d+\.?\d*",item.select('[class*="photo-count"]')[0].text)[0]
                    else:
                        dict_business['not recommended reviews'][str(review_count)]['user info']['user_photo_count'] = '0'
                        
                    
                    ## review info
                    ### review star-rating, date, text
                    dict_business['not recommended reviews'][str(review_count)]['review info']['review rating'] = \
                        item.select('[class*="i-stars i-stars"]')[0]['title'].replace('.0','')
                    dict_business['not recommended reviews'][str(review_count)]['review info']['review_date'] = \
                        item.select('[class*="rating-qualifier"]')[0].text.strip()
                    if item.find('p') is None:
                        dict_business['not recommended reviews'][str(review_count)]['review info']['review_text'] = ''
                    else:
                        dict_business['not recommended reviews'][str(review_count)]['review info']['review_text'] = \
                            item.find('p').text
                        
                    
                    review_count += 1
                    
                num += 1
        
        
            except Exception as e:
                raise e
                print('review/user error')
                dict_error['fake reviews']['page_'+str(num)] = 'review_count: '+str(review_count)
    
    
        except Exception as e:
            raise e
            print('review page error')
    
    
    """ save dictionary """
    

    with open(os.path.join(path_business, str(business_id)+'.json'), 'w+', encoding="utf-8") as outfile:
        json.dump(dict_business, outfile, ensure_ascii=False) 
    
    print('dictionary saved, current time is:', time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
    
    """ close the chrome """
    driver.quit()
    
    
    print('\n\n\n\n\n\n\n\n\n\n\n\n')
    
    """ next business """
    business_num += 1

#%%














































#%%
""" test code: review page """

""" select business """
business_num = 0
url = 'https://www.yelp.com'+df_lv.iloc[business_num]['link']+'&start='+str(0)

""" get page_num """
driver.get(url)
time.sleep(5) # Let the user actually see something!
soup = BeautifulSoup(driver.page_source,'html.parser')
page_num = soup.select('[aria-label*="Pagination navigation"]')[0].find_all('span')[-1].get_text()
total_page_num = int(page_num.split(' ')[-1])
print('total_page_num:', total_page_num)

""" collect business info """
for item in soup.select('[type*="application/json"]'):
    if 'businessId' in item.text:
        dict_temp = json.loads(item.text[4:-3])
        print('business_id:', dict_temp['bizDetailsPageProps']['businessId'])
        print('\n\n')
        #dict_business = {'business info':dict_ny[df_ny.iloc[business_num]['restaurant name']]['business info']}
        #dict_business['business info']['business_id']=business_id
for item in soup.select('[class*=margin-b2]'):
    if item.find('span') and item.find('h5') and len(item.find_all('h5')) == 2:
        for element in item.select('[class*=margin-b2]'):    
            # updated service
            if 'Updated Services' in element.text:
                print('updated services:')
            ## health & safety measures
            elif 'Health & Safety Measures' in element.get_text():
                print('health & safety measures:')
            #dict_business['business info'][condition] = {}
            for j in range(len(element.select('[class*=margin-t2]')[0].select('[class*=display--inline-block]'))):
                if j % 2 == 0:
                    ### remove irrelevant characters
                    service = element.select('[class*=margin-t2]')[0].select('[class*=display--inline-block]')[j].get_text().split('According')[0]
                    if 'M9.46' in element.select('[class*=margin-t2]')[0].select('[class*=display--inline-block]')[j].find('path')['d']:
                            print(str(service)+':', 'Yes')
                    elif 'M13.41' in element.select('[class*=margin-t2]')[0].select('[class*=display--inline-block]')[j].find('path')['d']:
                        print(str(service)+':', 'No')
            print('\n\n')
            
# collect review&user info
# since there's no review id, we save the review by the collecting order
review_count = 0
dict_business['reviews'] = {}

for num in range(total_page_num):
    
    if num != 0:
        # get all source code from the targeted webpage
        url = 'https://www.yelp.com'+df_lv.iloc[business_num]['link']+'&start='+str(num*10)
        driver.get(url)
        time.sleep(3) # Let the user actually see something!
        soup = BeautifulSoup(driver.page_source,'html.parser')
        
    print('page num:', num)
    print('\n\n')
    for item in soup.select('[class*="review__373c0__13kpL"]'):
        
        ## user info
        ### user link, id, name, location, elite info
        print('user_link:', item.select('[class*="user-passport-info"]')[0].select('[class="css-166la90"]')[0]['href'])
        print('user_id:', item.select('[class*="user-passport-info"]')[0].select('[class="css-166la90"]')[0]['href'].split('userid=')[-1])
        print('user_name:', item.select('[class*="user-passport-info"]')[0].select('[class="css-166la90"]')[0].text)
        print('user_location:', item.select('[class*="user-passport-info"]')[0].select('[class*="responsive-hidden-small"]')[0].text)
        ### user elite info
        if item.select('[class*="user-passport-info"]')[0].select('[class*="elite-badge"]') != []:
            user_elite = True
        else: user_elite = False
        print('elite_user:', user_elite)
        
        ## review info
        ### review star-rating, date, num of photo, text, votes
        print('review_rating:', item.select('[class*="i-stars"]')[0]['aria-label'])
        print('review_date:', item.select('[class*="css-e81eai"]')[0].text)
        if item.select('[class*="css-1x0u7iy"]') != []:
            print('review_photo_num:', item.select('[class*="css-1x0u7iy"]')[0].text.split(' photo')[0])
        else:
            print('review_photo_num', '0')
        print('review_text:', item.select('[class*=comment]')[0].text)
        for element in item.select('[class*="css-1ha1j8d"]'):
            votetype = element.text.split(' ')[0].lower()
            # if no num
            if re.compile('[0-9]+').findall(element.text) == []:
                print('review_vote_'+votetype+':', '0')
            else:
                print('review_vote_'+votetype+':', element.text.split(' ')[-1])
    
        
        """ test code: user page """
        ## addtional user info
        url_user = 'https://www.yelp.com'+item.select('[class*="user-passport-info"]')[0].select('[class="css-166la90"]')[0]['href']
        driver.get(url_user)
        time.sleep(5) # Let the user actually see something!
        soup_user = BeautifulSoup(driver.page_source,'html.parser')
        
        ### user friend count, review count, photo count
        print('user_friend_count:', re.findall(r"\d+\.?\d*",soup_user.select('[class*="user-profile_info arrange_unit"]')[0].select('[class*="friend-count"]')[0].text)[0])
        print('user_review_count:', re.findall(r"\d+\.?\d*",soup_user.select('[class*="user-profile_info arrange_unit"]')[0].select('[class*="review-count"]')[0].text)[0])
        print('user_photo_count:', re.findall(r"\d+\.?\d*",soup_user.select('[class*="user-profile_info arrange_unit"]')[0].select('[class*="photo-count"]')[0].text)[0])
        ### user elite info
        if user_elite == True:
            list_user_eliteyear = re.findall(r"\d+\.?\d*",soup_user.select('[class*="user-profile_info arrange_unit"]')[0].select('[class*="badge-bar u-space"]')[0].text)
            for i in range(len(list_user_eliteyear)):
                if len(list_user_eliteyear[i]) < 4:
                    list_user_eliteyear[i] = '20'+ list_user_eliteyear[i]
            print('user_elite_year:', list_user_eliteyear)
        ### user review vote, followers, yelpingsince
        for element in soup_user.select('[class*="user-details-overview_sidebar"]')[0].select('[class*=ysection]'):
            if 'Review Votes' in element.text:
                list_user_votecount = re.findall(r"\d+\.?\d*",element.text)
                list_user_votetype = \
                    re.sub(r"[^A-Za-z\s]", " ", element.text.replace('Review Votes','').strip()).split()
                for i in range(len(list_user_votetype)):
                    print('user_vote_'+list_user_votetype[i].lower()+':', list_user_votecount[i])
                if 'Useful' not in list_user_votetype:
                    print('user_vote_useful:', '0')
                elif 'Funny' not in list_user_votetype:
                    print('user_vote_funny:', '0')
                elif 'Cool' not in list_user_votetype:
                    print('user_vote_cool:', '0')                
                continue
            if 'Followers' in element.text:
                list_stats_count = re.findall(r"\d+\.?\d*",element.text)
                list_stats_type = \
                    re.sub(r"[^A-Za-z\s]", " ",element.text.replace('Stats','').replace(' ','')).split()
                i = list_stats_type.index('Followers')
                print('user_followers:', list_stats_count[i])
                continue
            if 'Yelping Since' in element.text:
                list_attr = list(filter(None,element.text.split('\n')))
                i = list_attr.index('Yelping Since')
                print('user_yelpingsince:', list_attr[i+1])
        ## followers = 0 if 'followers' not in content
        if 'Followers' not in soup_user.select('[class*="user-details-overview_sidebar"]')[0].text:
            print('user_followers:', '0')
        
        print('\n\n')
        
    print('\n\n\n')
    
    if num >= 1:
        break
    

#%%


dict_temp = dict_business['reviews']['0']

dict_reviews = {}
review_count = 0

for review_num in range(len(dict_business['reviews'].keys())):
    if review_num == 0:
        dict_reviews[str(review_count)] = dict_business['reviews'][str(review_num)]
        review_count += 1
        continue
    if dict_business['reviews'][str(review_num)] != dict_temp:
        dict_reviews[str(review_count)] = dict_business['reviews'][str(review_num)]
        review_count += 1
#%%
dict_business['reviews'] = dict_reviews

#%%
        
# search reviews
for item in soup.select('[class*="review__373c0__13kpL"]'):
    dict_reviews[str(review_count)] = {'user_info':{},'review_info':{}}
    ## user info
    ### user link, id, name, location, elite info
    dict_reviews[str(review_count)]['user_info']['user_link'] = \
        item.select('[class*="user-passport-info"]')[0].select('[class="css-166la90"]')[0]['href']
    dict_reviews[str(review_count)]['user_info']['user_id'] = \
        item.select('[class*="user-passport-info"]')[0].select('[class="css-166la90"]')[0]['href'].split('userid=')[-1]
    dict_reviews[str(review_count)]['user_info']['user_name'] = \
        item.select('[class*="user-passport-info"]')[0].select('[class="css-166la90"]')[0].text
    if item.select('[class*="user-passport-info"]')[0].select('[class*="responsive-hidden-small"]') == []:
        dict_reviews[str(review_count)]['user_info']['user_location'] = ''
    else:
        dict_reviews[str(review_count)]['user_info']['user_location'] = \
            item.select('[class*="user-passport-info"]')[0].select('[class*="responsive-hidden-small"]')[0].text
    ### user elite info
    if item.select('[class*="user-passport-info"]')[0].select('[class*="elite-badge"]') != []:
        user_elite = True
    else: user_elite = False
    
    
    ## review info
    ### review star-rating, date, num of photo, text, votes
    dict_reviews[str(review_count)]['review_info']['review_rating'] = \
        item.select('[class*="i-stars"]')[0]['aria-label']
    dict_reviews[str(review_count)]['review_info']['review_date'] = \
        item.select('[class*="css-e81eai"]')[0].text
    if item.select('[class*="css-1x0u7iy"]') != []:
        dict_reviews[str(review_count)]['review_info']['review_photo_count'] = \
            item.select('[class*="css-1x0u7iy"]')[0].text.split(' photo')[0]
    else:
        dict_reviews[str(review_count)]['review_info']['review_photo_count'] = '0'
    dict_reviews[str(review_count)]['review_info']['review_text'] = \
        item.select('[class*=comment]')[0].text
    for element in item.select('[class*="css-1ha1j8d"]'):
        votetype = element.text.split(' ')[0].lower()
        # if no num
        if re.compile('[0-9]+').findall(element.text) == []:
            dict_reviews[str(review_count)]['review_info']['review_vote_'+votetype] = '0'
        else:
            dict_reviews[str(review_count)]['review_info']['review_vote_'+votetype] = \
                element.text.split(' ')[-1]

    ## addtional user info
    url_user = 'https://www.yelp.com'+item.select('[class*="user-passport-info"]')[0].select('[class="css-166la90"]')[0]['href']
    driver.get(url_user)
    soup_user = BeautifulSoup(driver.page_source,'html.parser')
    time.sleep(3) # Let the user actually see something!
    
    ### user friend count, review count, photo count
    dict_reviews[str(review_count)]['user_info']['user_friend_count'] = \
        re.findall(r"\d+\.?\d*",soup_user.select('[class*="user-profile_info arrange_unit"]')[0].select('[class*="friend-count"]')[0].text)[0]
    dict_reviews[str(review_count)]['user_info']['user_review_count'] = \
        re.findall(r"\d+\.?\d*",soup_user.select('[class*="user-profile_info arrange_unit"]')[0].select('[class*="review-count"]')[0].text)[0]
    dict_reviews[str(review_count)]['user_info']['user_photo_count'] = \
        re.findall(r"\d+\.?\d*",soup_user.select('[class*="user-profile_info arrange_unit"]')[0].select('[class*="photo-count"]')[0].text)[0]
    ### user elite info
    if user_elite == True:
        list_user_eliteyear = re.findall(r"\d+\.?\d*",soup_user.select('[class*="user-profile_info arrange_unit"]')[0].select('[class*="badge-bar u-space"]')[0].text)
        for i in range(len(list_user_eliteyear)):
            if len(list_user_eliteyear[i]) < 4:
                list_user_eliteyear[i] = '20'+ list_user_eliteyear[i]
        dict_reviews[str(review_count)]['user_info']['user_elite_year'] = \
            list_user_eliteyear
    ### user review votes, follower, yelping since
    #### initial vote count
    dict_reviews[str(review_count)]['user_info']['user_vote_useful'] = '0'
    dict_reviews[str(review_count)]['user_info']['user_vote_funny'] = '0'
    dict_reviews[str(review_count)]['user_info']['user_vote_cool'] = '0'

    for element in soup_user.select('[class*="user-details-overview_sidebar"]')[0].select('[class*=ysection]'):
        if 'Review Votes' in element.text:
            list_user_votecount = re.findall(r"\d+\.?\d*",element.text)
            list_user_votetype = \
                re.sub(r"[^A-Za-z\s]", " ", element.text.replace('Review Votes','').strip()).split()
            for i in range(len(list_user_votetype)):
                dict_reviews[str(review_count)]['user_info']['user_vote_'+list_user_votetype[i].lower()] = \
                    list_user_votecount[i]
            continue
        if 'Followers' in element.text:
            list_stats_count = re.findall(r"\d+\.?\d*",element.text)
            list_stats_type = \
                re.sub(r"[^A-Za-z\s]", " ",element.text.replace('Stats','').replace(' ','')).split()
            i = list_stats_type.index('Followers')
            dict_reviews[str(review_count)]['user_info']['user_followers'] = \
                list_stats_count[i]
            continue
        if 'Yelping Since' in element.text:
            list_attr = list(filter(None,element.text.split('\n')))
            i = list_attr.index('Yelping Since')
            dict_reviews[str(review_count)]['user_info']['user_yelpingsince'] = \
                list_attr[i+1]
    ## followers = 0 if 'followers' not in content
    if 'Followers' not in soup_user.select('[class*="user-details-overview_sidebar"]')[0].text:
        dict_reviews[str(review_count)]['user_info']['user_followers'] = '0'
            
            
    review_count += 1
    

num += 1  

#%%
""" compare businesses with df """
list_businessname = []

for filename in filenames:
    with open(os.path.join(path, 'reviews', filename), 'r', encoding="utf-8") as file:
        for line in file.readlines():
            dict_business =  json.loads(line)
    list_businessname.append(dict_business['business info']['restaurant name'])

for name in df_ny[df_ny['review count'] >= 1000]['restaurant name']:
    if name not in list_businessname:
        print(name)
    
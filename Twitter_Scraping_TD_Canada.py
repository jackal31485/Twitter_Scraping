#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
#Defining Required Libraries
import os
import sys
import datetime
import time
import json
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
#- Globals --------------------------------------------------------------------
#------------------------------------------------------------------------------
# Setting Working Directory
working_directory = 'D:\Twitter_Test'
os.chdir(working_directory)
print('Working Directory: %s'%(working_directory))
# Setting Twitter All IDs Filename
filename_twitter_ids = 'all_tracked_twitter_ids_TD_Canada_20100101_20180201.json'
location_twitter_ids = os.path.join(os.getcwd(),filename_twitter_ids)
# Temporary Files being used in this Script
filename_twitter_output_file_temp = 'filename_twitter_output_file_temp.json'
#Twitter API Credentials
filename_twitter_api_keys = 'api_keys.json'
#Setting Starting Date
date1 = '2010-01-01'
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# Creating a list of Days that will be processed ------------------------------
#------------------------------------------------------------------------------
Dates_to_process_final = []
date2 = datetime.datetime.today()
stepback = datetime.timedelta(days=1)
date2 -= stepback
date2 = date2.strftime('%Y-%m-%d')
date2 = '2018-02-01'

#Setting End Date
start = datetime.datetime.strptime(date1, '%Y-%m-%d')
end = datetime.datetime.strptime(date2, '%Y-%m-%d')
step = datetime.timedelta(days=1)
while start <= end:
    #print (start.date())
    Dates_to_process_final.insert(0,str(start.date()))
    start += step
print('Date Start: %s'%(date1))
print('Date End  : %s'%(date2))
print('Number of Days in consideration for processing: %d' % (len(Dates_to_process_final)))

#------------------------------------------------------------------------------
#- Perparing Twitter Handle & Hashtag Lists to Process ------------------------
#------------------------------------------------------------------------------
#Creating lists of all users and hashtags to check against
#Green Bank - TD Bank
track_items1_a= ['@TD_Canada']
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
#- All definitions for Twitter Handle and Hastag Processing -------------------
#------------------------------------------------------------------------------
# don't mess with this stuff
id_selector = '.time a.tweet-timestamp'
tweet_selector = 'li.js-stream-item'
ids = []
# URLs for Quering
def form_url1(user, since, until):
    p1 = 'https://twitter.com/search?f=tweets&vertical=default&q=from%3A'
    p2 =  user + '%20since%3A' + since + '%20until%3A' + until + 'include%3Aretweets&src=typd'
    return p1 + p2
def form_url2(user, since, until):
    p1 = 'https://twitter.com/search?f=tweets&vertical=default&q='
    p2 =  user + '%20since%3A' + since + '%20until%3A' + until + 'include%3Aretweets&src=typd'
    return p1 + p2
def url_processing(urllink):
    print(urllink)
    ids = []
    driver.get(urllink)
    time.sleep(delay)
    try:
        found_tweets = driver.find_elements_by_css_selector(tweet_selector)
        increment = 10
        for tweet in found_tweets:
            try:
                id = tweet.find_element_by_css_selector(id_selector).get_attribute('href').split('/')[-1]
                ids.append(id)
            except StaleElementReferenceException as e:
                print('lost element reference', tweet)
            while len(found_tweets) >= increment:
                print('scrolling down to load more tweets')
                driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
                time.sleep(delay)
                found_tweets = driver.find_elements_by_css_selector(tweet_selector)
                increment += 10
                print('{} tweets found, {} total'.format(len(found_tweets), len(ids)))
                for tweet in found_tweets:
                    try:
                        id = tweet.find_element_by_css_selector(id_selector).get_attribute('href').split('/')[-1]
                        ids.append(id)
                    except StaleElementReferenceException as e:
                        print('lost element reference', tweet)
    except NoSuchElementException:
        print('no tweets on this day')
    try:
        with open(filename_twitter_ids, encoding = 'utf8') as f:
            all_ids = ids + json.load(f)
            data_to_write = list(set(all_ids))
            print('tweets found on this scrape: ', len(ids))
            print('total tweet count: ', len(data_to_write))
    except FileNotFoundError:
        with open(filename_twitter_ids, 'w', encoding = 'utf8') as f:
            all_ids = ids
            data_to_write = list(set(all_ids))
            print('tweets found on this scrape: ', len(ids))
            print('total tweet count: ', len(data_to_write))
    finally:
        if f is not None:
            f.close()
    with open(filename_twitter_ids, 'w') as outfile:
        json.dump(data_to_write, outfile)
#------------------------------------------------------------------------------
def selenium_processing(processdate,twitter_handle_hashtag):
    start = datetime.datetime.strptime(processdate, '%Y-%m-%d')
    user = twitter_handle_hashtag
    user = user.lower()
    user = user.replace('#','%23')
    url = form_url1(user, start.strftime('%Y-%m-%d'),(start + step).strftime('%Y-%m-%d'))
    url_processing(url)
    url = form_url2(user, start.strftime('%Y-%m-%d'),(start + step).strftime('%Y-%m-%d'))
    url_processing(url)
#------------------------------------------------------------------------------
#- Running Selenium to get all twitter Handles for Required Dates -------------
#------------------------------------------------------------------------------
try:
    #^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    if os.path.exists(os.path.join(os.getcwd(),'chromedriver.exe')):
        print("Getting new Tweets - Start")
        #^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        # only edit these if you're having problems
        delay = 3  # time to wait on each page load before reading the page
        driver = webdriver.Chrome()  # options are Chrome() Firefox() Safari()
        #^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        # Starting Day Processing - Toronto-Dominion Bank
        #^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        print('Number of Days for processing: %d' % (len(Dates_to_process_final)))
        for processdate in Dates_to_process_final:
            for twitter_handle_hashtag in track_items1_a:
                print("For Date: %s | Currently Processing: %s"%(processdate,twitter_handle_hashtag))
                selenium_processing(processdate,twitter_handle_hashtag)
        print("Getting new Tweets - End")
    else:
        print("Chrome Driver File Missing. No new Tweets IDs Can be downloaded.")
    #^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
except IOError as e:
    print ("I/O error({0}): {1}".format(e.errno, e.strerror))
except ValueError:
    print ("Could not convert data to an integer.")
except:
    print ("Unexpected error:", sys.exc_info()[0])
    raise
finally:
    if os.path.exists(os.path.join(os.getcwd(),'chromedriver.exe')):
        driver.close()
        driver.quit()

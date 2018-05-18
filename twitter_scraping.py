#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
#Defining Required Libraries
import os
import sys
import datetime
import sqlite3
import time
import json
import tweepy
import math
import re
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from collections import Counter
from geopy.geocoders import GoogleV3
from geopy.exc import GeocoderQuotaExceeded
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
#- Globals --------------------------------------------------------------------
#------------------------------------------------------------------------------
# Setting Working Directory
working_directory = ''
os.chdir(working_directory)
print('Working Directory: %s'%(working_directory))
# Setting Twitter All IDs Filename
filename_twitter_ids = 'all_tracked_twitter_ids_from_yyyymmdd.json'
location_twitter_ids = os.path.join(os.getcwd(),filename_twitter_ids)
# Setting Twitter Database
filename_twitter_db = 'twitterDB.db'
location_db = os.path.join(os.getcwd(),filename_twitter_db)
# Temporary Files being used in this Script
filename_twitter_output_file_temp = 'filename_twitter_output_file_temp.json'
#Twitter API Credentials
filename_twitter_api_keys = 'api_keys.json'
#Wordcount Settings
WordCloudTweetNo = 40
#GeoCode Daily Limit - Free Max = 1000; Registered Max = 2500
geocode_dailymaxretrievefree = 1000
geocode_dailymaxretrieveuser = 2500
google_api_key = ''
#Setting Starting Date
date1 = 'yyyy-mm-dd'
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
#- Setting Up database objects schema -----------------------------------------
#------------------------------------------------------------------------------
objectsCreate = {'UserTimeline':
                 'CREATE TABLE IF NOT EXISTS UserTimeline ('
                 'user_id_str str, '
                 'user_name text, '
                 'screen_name  text, '
                 'user_description text, '
                 'user_location text, '
                 'user_url text, '
                 'user_created_datetime text,'
                 'user_created_date text,'
                 'user_language text ,'
                 'user_timezone text, '
                 'user_utc_offset real,'
                 'user_friends_count real,'
                 'user_followers_count real,'
                 'user_statuses_count real,'
                 'tweet_id int,'
                 'tweet_id_str text,'
                 'tweet_text text,'
                 'tweet_in_reply_to_screen_name text,'
                 'tweet_created_timestamp text,'
                 'tweet_created_date text,'
                 'tweet_probability_sentiment_positive real,'
                 'tweet_probability_sentiment_neutral real,'
                 'tweet_probability_sentiment_negative real,'
                 'tweet_sentiment text,'
                 'tweet_longitude real,'
                 'tweet_latitude real,'
                 'tweet_grouping_1 text,'
                 'tweet_retweeted text,'
                 'PRIMARY KEY(tweet_id_str))',

                 'FollowersGeoData':
                 'CREATE TABLE IF NOT EXISTS FollowersGeoData ('
                 'follower_id_str text,'
                 'follower_name text,'
                 'follower_location text,'
                 'location_latitude real,'
                 'location_longitude real,'
                 'PRIMARY KEY (follower_id_str))'}

                 'WordsCount':
                 'CREATE TABLE IF NOT EXISTS WordsCount ('
                 'tweet_created_date text,'
                 'tweet_grouping text,'
                 'word text,'
                 'frequency int,'
                 'PRIMARY KEY (tweet_created_date, tweet_grouping, word))'
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# Creating a list of Days that will be processed ------------------------------
#------------------------------------------------------------------------------
Dates_to_process_pre = []
Dates_to_process_final = []
date2 = datetime.datetime.today()
stepback = datetime.timedelta(days=2)
date2 -= stepback
date2 = date2.strftime('%Y-%m-%d')

#Setting End Date
start = datetime.datetime.strptime(date1, '%Y-%m-%d')
end = datetime.datetime.strptime(date2, '%Y-%m-%d')
step = datetime.timedelta(days=1)
while start <= end:
    #print (start.date())
    Dates_to_process_pre.insert(0,str(start.date()))
    start += step
print('Date Start: %s'%(date1))
print('Date End  : %s'%(date2))
print('Number of Days in consideration for processing: %d' % (len(Dates_to_process_pre)))
#------------------------------------------------------------------------------
# Checking if JSON File Exists
exists_json = not os.path.exists(location_twitter_ids)
if exists_json:
    print('No %s File Found!'%(filename_twitter_ids))
# Checking if Database Exists
exists_db = not os.path.exists(location_db)
if exists_db:
    conn = sqlite3.connect(location_db)
    print("Creating database schema on " + location_db + " database...")
    for t in objectsCreate.items():
        try:
            conn.executescript(t[1])
        except sqlite3.OperationalError as e:
            print (e)
            conn.rollback()
            sys.exit(1)
        else:
            conn.commit()
    conn.close()
    print('%s Database is recently created!'%(filename_twitter_db))
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
#- Perparing Twitter Handle & Hashtag Lists to Process ------------------------
#------------------------------------------------------------------------------
#Creating lists of all users and hashtags to check against
#Green Bank - TD Bank
track_items1_a= ['@']
track_items1_b= r"(@)"
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
def downloadtwitterdata():
    print('Twitter Download and Database Update Process - Starting')
    #Checking to see if new UserIDs need to be downloaded
    print('------------------------------------------------')
    Database_UserTimelineIDs = []
    cur = 'SELECT DISTINCT tweet_id_str from UserTimeline'
    data = conn.execute(cur).fetchall()
    for u in data:
        Database_UserTimelineIDs.extend(u)
    print('Total Database UserTimelineIDs: ', len(Database_UserTimelineIDs))
    Raw_UserTimelineIDs = []
    try:
        with open(filename_twitter_ids, encoding = 'utf8') as f:
            Raw_UserTimelineIDs = list(set(json.load(f)))
        print('Total Raw UserTimelineIDs: ', len(Raw_UserTimelineIDs))
    except FileNotFoundError:
        print('No Raw UserTimelineIDs Found')
    finally:
        if f is not None:
            f.close()
    ToDownload_UserTimelineIDs = []
    ToDownload_UserTimelineIDs = [item for item in Raw_UserTimelineIDs if item not in Database_UserTimelineIDs]
    print('Total ToDownload UserTimelineIDs: ', len(ToDownload_UserTimelineIDs))
    if len(ToDownload_UserTimelineIDs) <= 0:
        print('No new Twitter IDs to Process')
    else:
        print('Metadata collection - Starting')
        with open(filename_twitter_api_keys, encoding = 'utf8') as f:
            keys = json.load(f)
        auth = tweepy.OAuthHandler(keys['consumer_key'], keys['consumer_secret'])
        auth.set_access_token(keys['access_token'], keys['access_token_secret'])
        api = tweepy.API(auth)
        #Splitting into 1000 tweets chunks
        chunks = [ToDownload_UserTimelineIDs[x:x+1000] for x in range(0, len(ToDownload_UserTimelineIDs), 1000)]
        #iterating though sublists
        all_data = []
        print('Total Chunks to be processed: {}'.format(len(chunks)))
        for index, chunk in enumerate(chunks):
            print('Starting Chunks %s of %s' % (index+1,len(chunks)))
            print('total sublist ids: {}'.format(len(chunk)))
            start = 0
            end = 100
            limit = len(chunk)
            i = math.ceil(limit / 100)
            for go in range(i):
                print('currently getting {} - {}'.format(start, end))
                time.sleep(6)  # needed to prevent hitting API rate limit
                id_batch = chunk[start:end]
                start += 100
                end += 100
                tweets = api.statuses_lookup(id_batch)
                for tweet in tweets:
                    all_data.append(dict(tweet._json))
            time.sleep(5)  # Taking a break

            print('creating master json file - Starting')
            with open(filename_twitter_output_file_temp, 'w', encoding = 'utf8') as outfile:
                json.dump(all_data, outfile)
            print('creating master json file - Complete')

            print('Updating UserTimeline - Starting')
            with open(filename_twitter_output_file_temp, 'r', encoding = 'utf8') as json_data:
                data = json.load(json_data)
                for entry in data:
                    payload = str(entry['text'])
                    #concatnate if tweet is on multiple lines
                    payload = str(payload.replace("\n", ""))
                    #remove http:// URL shortening links
                    payload = re.sub(r'http://[\w.]+/+[\w.]+', "", payload, re.IGNORECASE)
                    #remove https:// URL shortening links
                    payload = re.sub(r'https://[\w.]+/+[\w.]+', "", payload, re.IGNORECASE)
                    #remove certain characters
                    payload = re.sub(r'([^\s\w]|_)', '', payload)
                    sid = SentimentIntensityAnalyzer()
                    ss = sid.polarity_scores(payload)
                    tweet_sentiment_txt = "Neutral"
                    if ss['compound'] >= 0.25:
                        tweet_sentiment_txt = "Positive"
                    elif ss['compound'] <= -0.25:
                        tweet_sentiment_txt = "Negative"

                    #Getting Tweet Coordinates
                    long = None
                    lati = None
                    if entry['coordinates'] is not None:
                        lati = entry['coordinates']['coordinates'][1]
                        long = entry['coordinates']['coordinates'][0]

                    #Checking to see if is it a retweet
                    def is_retweet(entry):
                        return 'retweeted_status' in entry.keys()
                    retweet_status = "No"
                    if is_retweet(entry) is not False:
                        retweet_status = "Yes"

                    conn.execute("INSERT OR IGNORE INTO UserTimeline "
                                 "(user_id_str,"
                                 "user_name,"
                                 "screen_name,"
                                 "user_description,"
                                 "user_location,"
                                 "user_url,"
                                 "user_created_datetime,"
                                 "user_created_date,"
                                 "user_language,"
                                 "user_timezone,"
                                 "user_utc_offset,"
                                 "user_friends_count,"
                                 "user_followers_count,"
                                 "user_statuses_count,"
                                 "tweet_id,"
                                 "tweet_id_str,"
                                 "tweet_text,"
                                 "tweet_in_reply_to_screen_name,"
                                 "tweet_created_timestamp,"
                                 "tweet_created_date,"
                                 "tweet_probability_sentiment_positive,"
                                 "tweet_probability_sentiment_neutral,"
                                 "tweet_probability_sentiment_negative,"
                                 "tweet_sentiment,"
                                 "tweet_latitude,"
                                 "tweet_longitude,"
                                 "tweet_retweeted ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(
                                entry['user']['id_str'],
                                entry['user']['name'],
                                entry['user']['screen_name'],
                                entry['user']['description'],
                                entry['user']['location'],
                                entry['user']['url'],
                                time.strftime('%Y-%m-%d %H:%M:%S', time.strptime(entry['user']['created_at'],'%a %b %d %H:%M:%S +0000 %Y')),
                                time.strftime('%Y-%m-%d', time.strptime(entry['user']['created_at'],'%a %b %d %H:%M:%S +0000 %Y')),
                                entry['user']['lang'],
                                entry['user']['time_zone'],
                                entry['user']['utc_offset'],
                                entry['user']['friends_count'],
                                entry['user']['followers_count'],
                                entry['user']['statuses_count'],
                                entry['id'],
                                entry['id_str'],
                                payload,
                                entry['in_reply_to_screen_name'],
                                time.strftime('%Y-%m-%d %H:%M:%S', time.strptime(entry['created_at'],'%a %b %d %H:%M:%S +0000 %Y')),
                                time.strftime('%Y-%m-%d', time.strptime(entry['created_at'],'%a %b %d %H:%M:%S +0000 %Y')),
                                ss['pos'],
                                ss['neu'],
                                ss['neg'],
                                tweet_sentiment_txt,
                                lati,
                                long,
                                retweet_status))
                    conn.commit()

            json_twitterlocation = os.path.join(os.getcwd(),filename_twitter_output_file_temp)
            json_twittertemp = os.path.exists(json_twitterlocation)
            if json_twittertemp:
                print("Deleting " + filename_twitter_output_file_temp + " ...")
                os.remove(json_twitterlocation)
            print('Updating UserTimeline - Complete')
        print('Metadata collection - Complete')
    print('------------------------------------------------')
    print('Twitter Download and Database Update Process - Completed')
#------------------------------------------------------------------------------
def updategrouping_1():
    grouping_1 = None
    #Setting Grouping
    cur_db_user = "SELECT DISTINCT tweet_id_str,tweet_text,screen_name,tweet_in_reply_to_screen_name from UserTimeline where tweet_grouping_1 is null"
    dbgrouping = conn.execute(cur_db_user).fetchall()
    print('Number of IDs processing: %d' % (len(dbgrouping)))
    for tweetidstr in dbgrouping:
        if tweetidstr[1] is not None:
            payload = tweetidstr[1]
        else:
            payload = ""
        if tweetidstr[2] is not None:
            tweet_screenname = tweetidstr[2]
        else:
            tweet_screenname = ""
        if tweetidstr[3] is not None:
            tweet_inreplyto = tweetidstr[3]
        else:
            tweet_inreplyto = ""
        tweet_masterstring = payload + " " + tweet_screenname + " " + tweet_inreplyto
        if re.search(track_items1_b,tweet_masterstring, re.IGNORECASE):
            grouping_1 = "Toronto-Dominion Bank"
        if grouping_1 is not None:
            conn.execute("UPDATE UserTimeline SET tweet_grouping_1 = ? WHERE tweet_id_str = ?",(grouping_1,tweetidstr[0]))
            conn.commit()
#------------------------------------------------------------------------------
def updateDailyWordCounts():
    #Checking to see if new Daily WordCounts need to be created for Tweet_Groups
    print('------------------------------------------------')
    print('Twitter WordCounts Update Process - Starting')
    cur = 'SELECT DISTINCT tweet_grouping from UserTimeline WHERE tweet_grouping is not null AND tweet_grouping != ""'
    wordgrouplist = conn.execute(cur).fetchall()
    for wordgroupindex, wordgroup in enumerate(wordgrouplist):
        print("Processing Word Group: %d of %d | %s" % (wordgroupindex+1,len(wordgrouplist),wordgroup[0]))

        DaysUserTimeline = []
        cur = 'SELECT DISTINCT tweet_created_date from UserTimeline WHERE tweet_grouping ="'+wordgroup[0]+'"'
        data = conn.execute(cur).fetchall()
        for u in data:
            DaysUserTimeline.extend(u)
        print('Total Database UserTimeline Days: ', len(DaysUserTimeline))
        DaysWordCount = []
        cur = 'SELECT DISTINCT tweet_created_date from WordsCount WHERE tweet_grouping ="'+wordgroup[0]+'"'
        data = conn.execute(cur).fetchall()
        for u in data:
            DaysWordCount.extend(u)
        print('Total Database WordsCount Days: ', len(DaysWordCount))
        ToProcess_WordCountDays = []
        ToProcess_WordCountDays = [item for item in DaysUserTimeline if item not in DaysWordCount]
        print('Total ToProcess WordCountDays: ', len(ToProcess_WordCountDays))
        if len(ToProcess_WordCountDays) == 0:
            print('No new Word Count Days to Process')
        else:
            print('Updating WordsCount - Starting')
            tweet_grouping = wordgroup[0]
            StopList_en = stopwords.words('english')
            Lem = WordNetLemmatizer()
            cur = 'SELECT distinct tweet_created_date from UserTimeline WHERE tweet_grouping ="'+tweet_grouping+'"'
            data = conn.execute(cur).fetchall()
            print("Number of days to be processed: %d" % (len(data)))
            for wordindex, entry in enumerate(data):
                print("Processing Day: %d of %d" % (wordindex+1,len(data)))
                AllWords = ''
                process_date = str(entry[0]).replace("(", "").replace(")", "").replace("'", "").replace(",", "")
                cur_text = "SELECT tweet_text, user_language from UserTimeline WHERE tweet_created_date = '"+process_date+'" and tweet_grouping ="'+tweet_grouping+'" and user_language = "en"'
                data_text = conn.execute(cur_text).fetchall()
                for entry_text in data_text:
                    payload = str(entry_text[0])
                    #concatnate if tweet is on multiple lines
                    payload = str(payload.replace("\n", ""))
                    #remove http:// URL shortening links
                    payload = re.sub(r'http://[\w.]+/+[\w.]+', "", payload, re.IGNORECASE)
                    #remove https:// URL shortening links
                    payload = re.sub(r'https://[\w.]+/+[\w.]+', "", payload, re.IGNORECASE)
                    #remove certain characters
                    payload = re.sub(r'([^\s\w]|_)', '', payload)
                    #removes words of up to 3 characters entirely
                    payload = re.sub(r'\b\w{1,3}\b', '', payload)
                    #tokenize and convert to lower case
                    payload = [words.lower() for words in word_tokenize(payload) if words not in StopList_en]
                    #lemmatize words
                    payload = [Lem.lemmatize(word) for word in payload]
                    #join words
                    payload =' '.join(payload)
                    AllWords += payload
                if AllWords is not None:
                    words = [word for word in AllWords.split()]
                    c = Counter(words)
                    for word, count in c.most_common(WordCloudTweetNo):
                        conn.execute("INSERT OR IGNORE INTO WordsCount (tweet_created_date, tweet_grouping, word, frequency) VALUES (?,?,?,?)", (process_date, tweet_grouping, word, count))
                        conn.commit()
            print('Updating WordsCount - Complete')
    print('Twitter WordCounts Update Process - Complete')
    print('------------------------------------------------')
#------------------------------------------------------------------------------
def UpdateFollowersGeoData():
    #Looking for all users that have a location or the FollowersGeoData location is set to zero
    print('------------------------------------------------')
    print('Twitter FollowersGeoData Update Process - Starting')
    cur_db_user_chk = "SELECT distinct user_id_str AS IDS, screen_name AS SCRNNAME, user_location AS USRLOC from UserTimeline where user_location <> '' UNION SELECT distinct follower_id_str AS IDS, follower_name AS SCRNNAME, follower_location AS USRLOC from FollowersGeoData where location_latitude is null and location_longitude is null"
    data_db_user = conn.execute(cur_db_user_chk).fetchall()
    for entry in data_db_user:
        follower_id_str = str(entry[0])
        follower_name = entry[1]
        follower_location = entry[2]
        conn.execute("INSERT OR IGNORE INTO FollowersGeoData (follower_id_str,follower_name,follower_location) VALUES (?,?,?)", (follower_id_str,follower_name,follower_location))
        conn.commit()
    #Looking for users with no location set
    cur_db_geo = 'SELECT distinct * from FollowersGeoData where location_latitude is null and location_longitude is null'
    data_db_geo = conn.execute(cur_db_geo).fetchall()
    if len(data_db_geo) == 0:
        print('No new Twitter Followers to Geocode')
    else:
        print('Updating GetFollowersGeoData - Starting')
        print("Number or users to geocode for: %d" % (len(data_db_geo)))
        for geoindex, entry in enumerate(data_db_geo):
            latitude=0
            longitude=0
            if geoindex <= geocode_dailymaxretrievefree:
                geo = GoogleV3(timeout=5)
            else:
                geo = GoogleV3(api_key=google_api_key,timeout=5)
            geocode_daily = geocode_dailymaxretrievefree+geocode_dailymaxretrieveuser
            if geoindex <= geocode_daily:
                try:
                    try:
                        geoparams = geo.geocode(entry[2])
                    except GeocoderQuotaExceeded as e:
                        print(e)
                    else:
                        if geoparams is None:
                            pass
                        else:
                            latitude = geoparams.latitude
                            longitude = geoparams.longitude
                            conn.execute("UPDATE FollowersGeoData "
                                            "SET location_latitude = ?,"
                                            "location_longitude = ?"
                                            "WHERE follower_id_str = ?",
                                            (latitude,longitude,entry[0]))
                            conn.commit()
                except Exception as e:
                    print("Error: geocode failed on input %d of %d %s with message %s"%(geoindex+1,len(data_db_geo),entry[2], e))
                    continue
                print("Geocoding user: %d of %d | %s|%s|%s|%s|%s" % (geoindex+1,len(data_db_geo),latitude,longitude,entry[0],entry[1],entry[2]))
        print('Updating GetFollowersGeoData - Complete')
    print('------------------------------------------------')
    print('Twitter FollowersGeoData Update Process - Complete')
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
#- Running Selenium to get all twitter Handles for Required Dates -------------
#------------------------------------------------------------------------------
try:
    #^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    #Updating Twitter Database
    #^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    if os.path.exists(os.path.join(os.getcwd(),filename_twitter_api_keys)) and os.path.exists(os.path.join(os.getcwd(),location_twitter_ids)):
        print("Twitter API Credentials File Exists. Updating Twitter Database - Start.")
        conn = sqlite3.connect(location_db)
        downloadtwitterdata()
        updateDailyWordCounts()
        UpdateFollowersGeoData()
        conn.close()
        print("Updating Twitter Database - Complete.")
    else:
        print("Twitter API Credentials and/or Twitter IDS JSON is File Missing.")
    #^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    if os.path.exists(os.path.join(os.getcwd(),'chromedriver.exe')):
        print("Getting new Tweets - Start")
        #^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        # only edit these if you're having problems
        delay = 3  # time to wait on each page load before reading the page
        driver = webdriver.Chrome()  # options are Chrome() Firefox() Safari()
        #^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        # Starting Day Processing
        #^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        conn = sqlite3.connect(location_db)
        cur_db_user = "SELECT DISTINCT tweet_created_date from UserTimeline where tweet_grouping_1 =''"
        db_grouping_1 = conn.execute(cur_db_user).fetchall()
        DaysUserTimeline = []
        for u in db_grouping_1:
            DaysUserTimeline.extend(u)
        print('Toronto-Dominion Bank - Total Database UserTimeline Days: ', len(DaysUserTimeline))
        Dates_to_process_final = []
        Dates_to_process_final = [item for item in Dates_to_process_pre if item not in DaysUserTimeline]
        conn.close()
        print('Number of Days for processing: %d' % (len(Dates_to_process_final)))
        for processdate in Dates_to_process_final:
            for twitter_handle_hashtag in track_items1_a:
                print("For Date: %s | Currently Processing: %s"%(processdate,twitter_handle_hashtag))
                selenium_processing(processdate,twitter_handle_hashtag)
        print("Getting new Tweets - End")
    else:
        print("Chrome Driver File Missing. No new Tweets IDs Can be downloaded.")
    #^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    #Updating Twitter Database
    #^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    if os.path.exists(os.path.join(os.getcwd(),filename_twitter_api_keys)) and os.path.exists(os.path.join(os.getcwd(),location_twitter_ids)):
        print("Twitter API Credentials File Exists. Updating Twitter Database - Start.")
        conn = sqlite3.connect(location_db)
        downloadtwitterdata()
        updategrouping_1()

        cur_db_user = "SELECT DISTINCT tweet_id_str from UserTimeline "
        dbgrouping = conn.execute(cur_db_user).fetchall()
        print('Number of IDs processed: %d' % (len(dbgrouping)))

        cur_db_user = "SELECT DISTINCT tweet_id_str from UserTimeline where tweet_grouping_1 is not null"
        dbgrouping = conn.execute(cur_db_user).fetchall()
        print('Number of IDs for Toronto-Dominion Bank processing: %d' % (len(dbgrouping)))

        cur_db_user = "SELECT DISTINCT tweet_id_str from UserTimeline where tweet_grouping_1 is null "
        dbgrouping = conn.execute(cur_db_user).fetchall()
        print('Number of IDs to delete: %d' % (len(dbgrouping)))

        updateDailyWordCounts()
        UpdateFollowersGeoData()
        conn.close()
        print("Updating Twitter Database - Complete.")
    else:
        print("Twitter API Credentials and/or Twitter IDS JSON is File Missing.")
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

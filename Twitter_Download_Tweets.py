#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
#Defining Required Libraries
import os, time, json, tweepy, math
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
#- Globals --------------------------------------------------------------------
#------------------------------------------------------------------------------
# Setting Working Directory
# working_directory= ''
#os.chdir(working_directory)
#print('Working Directory: %s'%(working_directory))
# Setting Twitter All IDs Filename
filename_twitter_ids = 'all_tracked_twitter_ids.json'
#location_twitter_ids = os.path.join(os.getcwd(),filename_twitter_ids)
location_twitter_ids = filename_twitter_ids
# Temporary Files being used in this Script
filename_twitter_output_file_temp = 'TwitterData.json'
#Twitter API Credentials
filename_twitter_api_keys = 'api_keys.json'
#------------------------------------------------------------------------------
def downloadtwitterdata():
    print('Twitter Download and Database Update Process - Starting')
    with open(filename_twitter_ids, 'r', encoding = 'utf8') as json_data:
                data = json.load(json_data)
    ToDownload_UserTimelineIDs = sorted(set(data))
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
        print('Metadata collection - Complete')
    print('------------------------------------------------')
    print('Twitter Download and Database Update Process - Completed')
#------------------------------------------------------------------------------
#- Downloading Twitter Data ---------------------------------------------------
#------------------------------------------------------------------------------
downloadtwitterdata()

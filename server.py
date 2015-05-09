from flask import Flask
from flask import render_template
from flask import jsonify
from flask import Flask, render_template, request, url_for

import datetime
import Queue
import threading
import time
import sys
import os
import urllib2
import csv
import os.path
import json
reload(sys)
sys.setdefaultencoding("utf-8")
import codecs
from bs4 import BeautifulSoup

import logging
from logging.handlers import RotatingFileHandler

from flask.ext.pymongo import PyMongo
from pymongo import MongoClient

app = Flask(__name__)
client = MongoClient()
db = client.app

# threads exit flag
exitFlag = 0
# number of threads to use. Naming is optional
threads_list = ["Scraper_Thread_1", "Scraper_Thread_2", "Scraper_Thread_3"]

# list of all urls to scrape
urls_list = ["....", "....", 
"....", "....", "...."]

queueLock = threading.Lock()
urlQueue = Queue.Queue(10)

def run_server():
	app.run()

class scraperThread (threading.Thread):
    def __init__(self, t_id, name, queue):
        threading.Thread.__init__(self)
        self.t_id = t_id
        self.name = name
        self.queue = queue
    def run(self):
        print "Starting " + self.name + " ..\n"
        process_queue(self.name, self.queue)
        print "Finishing " + self.name + " ..\n"

def process_queue(name, queue):
    while not exitFlag:
        queueLock.acquire()
        if not urlQueue.empty():
            url = queue.get()
            queueLock.release()
            print "Thread " + name + " beginning scraping on " + url + " ..\n"
            scrape(url)
            print "Thread " + name + " finished scraping on " + url + "\n"
        else:
            queueLock.release()
        time.sleep(1)

def scrape(url):
	data = db.data
	hdr = {'User-Agent' : 'Mozilla/5.0'}
	req = urllib2.Request(url, headers=hdr)
	page = urllib2.urlopen(req)
	soup = BeautifulSoup(page.read())

	table = soup.findAll('item')
	category = soup.find('title').text

	for item in table:
		msg_attrs = dict(item.attrs)
		# parse rss feed (xml) and extract
		title = item.find('title').text
		datetime = item.find('pubdate').text
		description = item.find('description').text
		# format into mongodb post 
		post = {
			"title" : title,
			"category" : category,
			"published_date" : datetime,
			"description" : description
		}

		# write to a text file as a safeguard. Optional
		with open("data_dump.txt", "a") as myfile:
			json.dump(post, myfile)

		# save into mongodb collection
		data.save(post)

@app.route("/multi")
def threads():
	thread_id = 1
	threads = []
	# Create 3 new threads 
	for thread_list in threads_list:
	    thread = scraperThread(thread_id, thread_list, urlQueue)
	    thread.start()
	    threads.append(thread)
	    thread_id += 1

	# Fill the url queue
	queueLock.acquire()
	for url_list in urls_list:
	    urlQueue.put(url_list)
	queueLock.release()

	while not urlQueue.empty():
		pass

	# Flg threads that it's time to exit
	global exitFlag
	exitFlag = 1
	for t in threads:
	    t.join()

	return 'OK'

# @app.route("/search/<term>")
# def searchTerm(term):
# cater for a search function in future

# get all data dumped into db printed on screen
# for checking
@app.route("/all")
def all():
	data = db.data
	for d in data.find():
		print d	
	return 'OK'

# dump the collection in db. useful for testing
@app.route("/dump")
def dump():
	data = db.data
	data.remove({})
	return 'DB dumped.'

if __name__ == "__main__":
	handler = RotatingFileHandler('error_log.log', maxBytes=10000, backupCount=1)
	handler.setLevel(logging.INFO)
	app.logger.addHandler(handler)
	run_server()
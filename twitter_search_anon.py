import twitter
import json
import io
import nltk
from nltk.util import tokenwrap
from nltk.collocations import *
import pprint
from collections import Counter
import urllib2
import requests
import re
from nltk.corpus import stopwords
from datetime import datetime
from pytz import timezone
fmt = "%Y-%m-%d %H:%M:%S %Z%z"
now_time = datetime.now(timezone('US/Eastern'))
file_time = now_time.strftime('%m%d%Y')

queries = 0

p = re.compile('growthhackers.com')

def save_json(filename, data):
    with io.open('{0}.json'.format(filename), 
                 'w', encoding='utf-8') as f:
        f.write(unicode(json.dumps(data, ensure_ascii=False)))

def load_json(filename):
    with io.open('{0}.json'.format(filename), 
                 encoding='utf-8') as f:
        return f.read()



def twitter_search(queries, twitter_api, q, max_results=200, **kw):
	  search_results = twitter_api.search.tweets(q=q, count=100, **kw)
	  print "query called"
	  print search_results['search_metadata']
	  statuses = search_results['statuses']
	  max_results = min(1000, max_results)
	  for _ in range(10):
	  	  try:
	  	  	  next_results = search_results['search_metadata']['next_results']
	  	  	  
	  	  except KeyError, e:
	  	  	  print "couldn't execute next results"
	  	  	  break
	  	  kwargs = dict([ kv.split('=')
	  	  							  for kv in next_results[1:].split("&") ])
	  	  search_results = twitter_api.search.tweets(**kwargs)
	  	  statuses += search_results['statuses']
	  	  print "query called"
	  	  if len(statuses) > max_results:
	  	  	 break
	  return statuses

# XXX: Go to http://dev.twitter.com/apps/new to create an app and get values
# for these credentials, which you'll need to provide in place of these
# empty string values that are defined as placeholders.
# See https://dev.twitter.com/docs/auth/oauth for more information 
# on Twitter's OAuth implementation.

CONSUMER_KEY = 'ntMZO2D4ssLF1DUqgrEeMQ'
CONSUMER_SECRET ='Ab1jaaHQgm2GVahyheUTYf0kmhziFmsdcJrpN23tkc'
OAUTH_TOKEN = '356958426-QEqw72LhmEjoMRCGXlQkpO8UC4yBhSLxqQ5UykDo'
OAUTH_TOKEN_SECRET = 'SA86q7qxm7LY2ZJqK2sx3NRfMxIv93C7oDOxWgyM2CDO2'

auth = twitter.oauth.OAuth(OAUTH_TOKEN, OAUTH_TOKEN_SECRET,
                           CONSUMER_KEY, CONSUMER_SECRET)

twitter_api = twitter.Twitter(auth=auth)
print twitter_api
q = "mobile shopping"
data_file = "mobile_shopping"



tweets = twitter_search(queries, twitter_api, q, max_results=1000)

#show how many, and save out to JSON file
print "retreived", len(tweets)
save_json('{0}_{1}_statuses'.format(data_file, file_time), tweets)

#load from JSON to prevent rate limit
raw_file = load_json('{0}_{1}_statuses'.format(data_file, file_time))
statuses = json.loads(raw_file)

#show diff between first and last tweets out to console
print statuses[0]['created_at']
print statuses[len(statuses)-1]['created_at']


#gather entities for output
status_texts = [ status['text'].encode('ascii', 'ignore')
								 for status in statuses]
screen_names = [ user_mention['screen_name']
								 for status in statuses 
								     for user_mention in status['entities']['user_mentions'] ]
urls = [ url['expanded_url']
							   for status in statuses
							      for url in status['entities']['urls'] ]



#test a single tweet out to console
print status_texts[0].encode('ascii', 'ignore')

#NLTK processing
words = [ w
			for t in status_texts
			    for w in t.split() ]

nltk_text = nltk.Text(words)
nltk_text.collocations()
ignored_words = stopwords.words('english')
finder = BigramCollocationFinder.from_words(words, 2)
finder.apply_freq_filter(2)
finder.apply_word_filter(lambda w: len(w) < 3 or w.lower() in ignored_words)
bigram_measures = nltk.collocations.BigramAssocMeasures()
collocations = finder.nbest(bigram_measures.likelihood_ratio, 20)
colloc_strings = [w1+' '+w2 for w1, w2 in collocations]
#finder = BigramCollocationFinder(word_fd, bigram_fd)
print tokenwrap(colloc_strings, separator="; ")




#create unstylized HTML
summarizedLinks = Counter(urls)

html_file = open('{0}_{1}_statuses.html'.format(data_file, file_time), 'w')
html_file.write('<!DOCTYPE html><html><head></head><body><h1>Analysis of past tweets: "{0}"</h1><h2>{1}</h2>'.format(q, now_time.strftime(fmt) ))
html_file.write('<br /><br /><h2>Collocations of commonly occuring pairs of words</h2>')
html_file.write('<ul>')
for collocation in colloc_strings:
	  html_file.write('<li>{0}</li>'.format(collocation))
html_file.write('</ul>')
html_file.write('<h2>Most common referenced URLs, unshortened and sorted</h2>')
html_file.write('<ul>')
for url, value in sorted(summarizedLinks.iteritems(), key=lambda item: item[1], reverse=True):
	  print url
	  try:

	      r = requests.get(url)
	      actual_page = r.url

	  except requests.exceptions.RequestException as e:
	  	  #print e.code
	  	  actual_page = url
	  #except urllib2.URLError as e:
	  		#print e.code
	  #		actual_page = url
	  if p.search(actual_page):
	      continue

	  html_file.write('<li>{1}<a href="{0}">{0}</a></li>'.format(actual_page, value))
html_file.write('</ul>')
html_file.write('<h2>Twitter Users</h2><ol>')
for status in statuses:
	  html_file.write('<li><a href="http://twitter.com/{0}">{0}</a> - {1}</li>'.format(status['user']['screen_name'], status['text'].encode('ascii', 'ignore')))
html_file.write('</ol>')
html_file.write('<h2>Screen Names</h2><ul>')
for screen_name in screen_names:
	  html_file.write('<li><a href="http://twitter.com/{0}">{0}</a></li>'.format(screen_name))
html_file.write('</ul>')
html_file.write('</body></html>')

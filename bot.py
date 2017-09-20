#!/usr/bin/env python3

from collections import OrderedDict
from json import loads, dumps
from verbose import *
import config
import praw
import re
import urllib.request
import urllib.parse

class Wiki:
	URL_BASE = 'http://destiny.wikia.com/api/v1/'

	@staticmethod
	@log('', format='[*] {2[0]}')
	def _open(url):
		with urllib.request.urlopen(url) as request:
			res = request.read()
		return res

	@staticmethod
	@log('looking up item url', format='[{0}] {1}: {2[0]}')
	def item_lookup(id):
		options = {'ids': id}
		params = urllib.parse.urlencode(options)
		url = '%sArticles/Details?%s' % (Wiki.URL_BASE, params)
		res = Wiki._open(url)
		json = loads(res.decode())
		# Wiki.pretty_print(json)
		return '%s%s' % (json['basepath'], json['items'][str(id)]['url'])

	@staticmethod
	@log('searching', format='[{0}] {1}: {2[0]}')
	def search(query, limit=1):
		options = {'query': query, 'limit': limit}
		params = urllib.parse.urlencode(options)
		url = '%sSearch/List?%s' % (Wiki.URL_BASE, params)
		res = Wiki._open(url)
		return loads(res.decode())

	@staticmethod
	@log('getting page source', format='[{0}] {1}: {2[0]}')
	def page_source(item_url):
		options = {'action': 'raw'}
		params = urllib.parse.urlencode(options)
		url = '%s?%s' % (item_url, params)
		res = Wiki._open(url)
		return res.decode()

	@staticmethod
	@log('parsing section', format='[{0}] {1}: {2[1]}')
	def page_section(raw, section):
		return re.findall('\{\{%s(.*?)\}\}' % section, raw, re.DOTALL)[0]

	@staticmethod
	@log('extracting Infobox data')
	def item_infobox(raw):
		match = Wiki.page_section(raw, 'Infobox')
		info = {}
		for line in match.split('\n'):
			try:
				key, value = line.split('=', 1)
			except:
				pass
			else:
				key = key[1:]
				if key and value:
					info[key] = value
		return info

	@staticmethod
	def pretty_print(json):
		print(dumps(json, indent=2))

class Reddit:
	def __init__(self):
		self.__config = None
		self.r = praw.Reddit(username      = config.username,
		                     password      = config.password,
		                     client_id     = config.client_id,
		                     client_secret = config.client_secret,
		                     user_agent    = 'destiny item bot v0.1')
		self.replies = []

	@property
	def subreddits(self):
		return ['DestinyTheGame', 'CruciblePlaybook']

	def run(self):
		subreddit = self.r.subreddit('+'.join(self.subreddits))
		for comment in subreddit.stream.comments():
			if comment.id in self.replies:
				continue
			try:
				matches = re.findall('\[\[(.*?)\]\]', comment.body, re.DOTALL)
				for m in matches:
					weapon_info = find_weapon(m)
					msg = create_weapon_reply(weapon_info)
					self.replies.append(comment.id)
					comment.reply(msg)
			except Exception as e:
				print(e)
			else:
				print('Successfully replied')

def create_weapon_reply(info):
	url = info['url'].replace('(', '\(')
	url = url.replace(')', '\)')
	msg = '[%s](%s)' % (info['name'], url)
	msg += ' - %s %s (%s)' % (info['rarity'], info['type'], info['slot'])
	msg += '\n\n     Stat     |  Value  \n--------------|---------\n'
	for k in info:
		if k in ['name', 'rarity', 'type', 'slot', 'url']:
			continue
		msg += '%s | %s\n' % (k.ljust(13), info[k].ljust(9))
	return msg

def format_weapon_info(info):
	key_filter = ['name',
	              'slot',
	              'rarity',
	              'type',
	              # 'manufacturer',
	              'impact',
	              'range',
	              'recoil',
	              'stability',
	              ('magazine', 'magazine size'),
	              ('reload', 'reload speed'),
	              'zoom',
	              ('rate', 'rate of fire'),
	              ('aim', 'aim assist'),
	              ('equipspeed', 'equip speed')]
	d = OrderedDict()
	for k in key_filter:
		try:
			if type(k) is tuple:
				d[k[1]] = info[k[0]]
			else:
				d[k] = info[k]
		except:
			pass
	return d

def find_weapon(name):
	json_search = Wiki.search(name)
	item_id = json_search['items'][0]['id']
	item_url = Wiki.item_lookup(item_id)
	source = Wiki.page_source(item_url)
	info = Wiki.item_infobox(source)
	weapon_info = format_weapon_info(info)
	weapon_info['url'] = item_url # include url with weapon info
	Wiki.pretty_print(weapon_info)
	return weapon_info

if __name__ == '__main__':
	Reddit().run()

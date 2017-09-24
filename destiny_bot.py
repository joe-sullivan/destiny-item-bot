#!/usr/bin/env python3

from bot import *
from collections import OrderedDict
from json import loads, dumps
import re
import urllib.request
import urllib.parse

class Wiki:
	URL_BASE = 'http://destiny.wikia.com/api/v1/'

	@staticmethod
	@Log.wrap('', format='[*] {2}')
	def _open(url):
		with urllib.request.urlopen(url) as request:
			res = request.read()
		return res

	@staticmethod
	@Log.wrap('looking up item url', format='[{0}] {1}: {2}')
	def item_lookup(id):
		options = {'ids': id}
		params = urllib.parse.urlencode(options)
		url = '%sArticles/Details?%s' % (Wiki.URL_BASE, params)
		res = Wiki._open(url)
		json = loads(res.decode())
		# Wiki.pretty_print(json)
		return '%s%s' % (json['basepath'], json['items'][str(id)]['url'])

	@staticmethod
	@Log.wrap('searching', format='[{0}] {1}: {2}')
	def search(query, limit=1):
		options = {'query': query, 'limit': limit}
		params = urllib.parse.urlencode(options)
		url = '%sSearch/List?%s' % (Wiki.URL_BASE, params)
		res = Wiki._open(url)
		return loads(res.decode())

	@staticmethod
	@Log.wrap('getting page source', format='[{0}] {1}: {2}')
	def page_source(item_url):
		options = {'action': 'raw'}
		params = urllib.parse.urlencode(options)
		url = '%s?%s' % (item_url, params)
		res = Wiki._open(url)
		return res.decode()

	@staticmethod
	@Log.wrap('extracting Infobox data')
	def item_infobox(raw):
		pattern = '\{\{Infobox(.*?)\}\}'
		match = re.findall(pattern, raw, re.DOTALL)[0]
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
		Log.print(dumps(json, indent=2), format='{1}', level=Log.DEFAULT)

class DestinyBot(RedditBot):
	def __init__(self):
		user_agent = 'destiny item bot v0.1'
		subreddits = ['DestinyTheGame']
		super().__init__(user_agent, subreddits, 'DestinyBot')

def create_weapon_reply(info):
	url = info['url'].replace('(', '\(')
	url = url.replace(')', '\)')
	msg = '[%s](%s)' % (info['name'], url)
	rarity = info.get('rarity') or ''
	weapon_type = info.get('type') or ''
	msg += ' - %s %s' % (rarity, weapon_type)
	slot = info.get('slot')
	if slot:
		msg += ' (%s)' % slot
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
	# Wiki.pretty_print(weapon_info)
	return weapon_info

if __name__ == '__main__':
	def callback(weapon):
		weapon_info = find_weapon(weapon)
		msg = create_weapon_reply(weapon_info)
		return DestinyBot.signature(usr=config.author, msg=msg, src=config.source)
	if config.debug:
		Log.print('Debugging', format='--- {1} ---')
	bot = DestinyBot()
	item_pattern = '\[\[(.*?)\]\]'
	weapon_matcher = Matcher('weapon_matcher', item_pattern, callback)
	bot.register_matcher(weapon_matcher)
	bot.run()

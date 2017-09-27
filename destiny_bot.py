#!/usr/bin/env python3

from bot import *
from collections import OrderedDict
from json import loads, dumps
import re
import urllib.request
import urllib.parse
import sys

class Wiki:
	URL_BASE = 'http://destiny.wikia.com/api/v1/'
	WEAPON_PRIMARY = ['Scout Rifle', 'Pulse Rifle', 'Auto Rifle', 'Hand Cannon', 'Submachine Gun', 'Sidearm']
	WEAPON_HEAVY = ['Shotgun', 'Sniper Rifle', 'Fusion Rifle', 'Sword', 'Rocket Launcher', 'Grenade Launcher']
	WEAPON = WEAPON_PRIMARY + WEAPON_HEAVY
	ARMOR = ['Helmet', 'Gauntlets', 'Chest Armor', 'Leg Armor']

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
		pattern = '\{\{Infobox(.*?)\n\}\}'
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

def create_reply(info):
	url = info['url'].replace('(', '\(')
	url = url.replace(')', '\)')
	msg = '[%s](%s)' % (info['name'], url)
	rarity = info.get('rarity') or ''
	item_type = info.get('type') or ''
	if rarity or item_type:
		msg += ' - %s %s' % (rarity, item_type)
	slot = info.get('slot')
	if slot:
		msg += ' (%s)' % slot
	table = ''
	for stat in info:
		if stat in ['name', 'rarity', 'type', 'slot', 'url']:
			continue
		k = stat.title()
		v = info[stat]
		table += '%s | %s\n' % (k.ljust(13), v.ljust(9))
	if table:
		msg += '\n\n     Stat     |  Value  \n------------- | --------\n'
		msg += table
	return msg.replace('[[', '').replace(']]', '')

def format_info(info):
	key_filter = [# weapons
	              'name',
	              'slot',
	              'rarity',
	              'type',
	              'manufacturer',
	              'impact',
	              'range',
	              'recoil',
	              'stability',
	              ('magazine', 'magazine size'),
	              ('reload', 'reload speed'),
	              'zoom',
	              ('rate', 'rate of fire'),
	              ('aim', 'aim assist'),
	              ('equipspeed', 'equip speed'),
	              # armor
	              ('armorset', 'set'),
	              # armor d1
	              'discipline',
	              'strength',
	              'intellect',
	              # armor d2
	              'mobility',
	              'resilience',
	              'recovery']
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

def find_item(name):
	json_search = Wiki.search(name)
	item_id = json_search['items'][0]['id']
	item_url = Wiki.item_lookup(item_id)
	source = Wiki.page_source(item_url)
	try:
		info = Wiki.item_infobox(source)
	except:
		info = None
	info = format_info(info)
	info['url'] = item_url # include url with info
	if not info.get('name'):
		info['name'] = name
	# Wiki.pretty_print(info)
	return info

if __name__ == '__main__':
	def callback(item):
		info = find_item(item)
		msg = create_reply(info)
		return DestinyBot.signature(usr=config.author, msg=msg, src=config.source)

	if config.debug:
		Log.print('Debugging', format='--- {1} ---')

	if len(sys.argv) > 1: # test item lookup
		print(callback(' '.join(sys.argv[1:])))
	else:
		bot = DestinyBot()
		item_pattern = '\[\[(.*?)\]\]'
		item_matcher = Matcher('item_matcher', item_pattern, callback)
		bot.register_matcher(item_matcher)
		bot.run()

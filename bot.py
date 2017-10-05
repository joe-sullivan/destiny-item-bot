#!/usr/bin/env python3

from verbose import Log
try:
	import config
except ImportError:
	print('Missing config.py: see README for more information')
	raise SystemExit
import pickle
import praw
import re

Log.ENABLED = config.debug

class Matcher:
	@Log.wrap('Initializing matcher')
	def __init__(self, name, ptrn, func):
		self.__name = name
		self.__ptrn = ptrn
		self.__func = func

	@property
	def name(self):
		return self.__name

	@property
	def function(self):
		return self.__func

	@property
	def pattern(self):
		return self.__ptrn

	def get(self, text):
		return re.findall(self.pattern, text, re.DOTALL)

	def safe_execute(self, context):
		try:
			return self.function(context)
		except Exception as e:
			Log.print(e, tag=self.name, level=Log.ERROR)

class RedditBot:
	@Log.wrap('Initializing bot')
	def __init__(self,
	             user_agent='sample bot user agent v0.0',
	             subreddits=['all'],
	             name='bot'):
		self.__config = None
		self.__viewed = []
		self.__matchers = []
		self.__name = name
		self.subreddits = subreddits
		self.r = praw.Reddit(username      = config.username,
		                     password      = config.password,
		                     client_id     = config.client_id,
		                     client_secret = config.client_secret,
		                     user_agent    = user_agent)

	@property
	def name(self):
		return self.__name

	@property
	def viewed(self):
		if not self.__viewed:
			try:
				with open('cache', 'rb') as f:
					self.__viewed = pickle.load(f)
			except:
				Log.print('could not load previously viewed comments', level=Log.WARN)
				self.__viewed = []
			else:
				Log.print('loaded previously viewed comments', tag=self.name)
		self.__viewed = self.__viewed[-100:] # save latest 100 viewed comments
		return self.__viewed

	@Log.wrap('registered new matcher', format='[{0}] {1}: {3.name}')
	def register_matcher(self, matcher):
		self.__matchers.append(matcher)

	@Log.wrap('starting', format='[{0}] {1}: {2.name}')
	def run(self):
		if not self.__matchers:
			Log.print('No matchers found', level=Log.WARN)
		if not self.subreddits:
			Log.print('No subreddits found', level=Log.WARN)
		try:
			subreddit = self.r.subreddit('+'.join(self.subreddits))
			for comment in subreddit.stream.comments():
				try: # remain in this loop even if error occurs
					# Log.print('New comment: %s' % comment.body[:20], tag=comment.subreddit)
					if comment.id in self.viewed: continue
					self.viewed.append(comment.id)
					for matcher in self.__matchers:
						for m in matcher.get(comment.body):
							msg = matcher.safe_execute(m)
							if not config.debug: # suppress writing to reddit
								comment.reply(msg)
							else:
								Log.print(msg, tag='reply', format='---{0}---\n{1}', level=Log.DEFAULT)
							Log.print('Replied to %s (%s):\n%s' % (comment.id, m, comment.body), tag=matcher.name, level=Log.SUCCESS)
				except Exception as e:
					Log.print(e, tag=comment.permalink(fast=True), level=Log.ERROR)
		except KeyboardInterrupt:
			Log.print('Manual shut down', tag=self.name)
		finally:
			Log.print('Storing data...', tag=self.name)
			with open('cache', 'wb') as f:
				pickle.dump(self.viewed, f)

	@staticmethod
	@Log.wrap('Building signature')
	def signature(usr=None, msg=None, src=None):
		sig = '---\n' # horizontal line
		info = []
		if usr:
			info.append('^^made ^^by ^^[/u/{0}](http://reddit.com/user/{0})'.format(usr))
		if src:
			info.append('^^[github](%s)' % src)
		sig += ' ^^| '.join(info)
		if msg:
			return msg + '\n\n' + sig
		return sig

if __name__ == '__main__':
	config.debug = True
	bot = RedditBot()
	matcher = Matcher('test', '\.(.*?)\.', lambda _: 'hello world')
	bot.register_matcher(matcher)
	bot.run()

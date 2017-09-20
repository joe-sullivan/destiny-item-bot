#!/usr/bin/env python3

from verbose import Log
import config
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
		self.__replies = None
		self.__matchers = []
		self.subreddits = subreddits
		self.__name = name
		self.r = praw.Reddit(username      = config.username,
		                     password      = config.password,
		                     client_id     = config.client_id,
		                     client_secret = config.client_secret,
		                     user_agent    = user_agent)

	@property
	def name(self):
		return self.__name

	@property
	def replies(self):
		if self.__replies is None:
			try:
				with open('cache', 'rb') as f:
					self.__replies = pickle.load(f)
			except:
				Log.print('could not load previous replies', level=Log.WARN)
				self.__replies = []
			else:
				Log.print('loaded replies', tag=self.name)
		return self.__replies

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
				# Log.print('New comment: %s' % comment.body[:20], tag=comment.subreddit)
				if comment.id in self.replies: continue
				for matcher in self.__matchers:
					matches = re.findall(matcher.pattern, comment.body, re.DOTALL)
					for m in matches:
						msg = matcher.safe_execute(m)
						if not config.debug: # suppress writing to reddit
							self.replies.append(comment.id)
							comment.reply(msg)
						Log.print('Replied to %s (%s)' % (comment.id, m), tag=matcher.name)
		except KeyboardInterrupt:
			Log.print('Shutting down', tag=self.name)
		finally:
			Log.print('Storing data...', tag=self.name)
			with open('cache', 'wb') as f: # save latest 100 replies
				pickle.dump(self.__replies[-100:], f)

if __name__ == '__main__':
	config.debug = True
	bot = RedditBot()
	matcher = Matcher('test', '\.(.*?)\.', lambda _: 'hello world')
	bot.register_matcher(matcher)
	bot.run()

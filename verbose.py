import os
import time
from functools import wraps

class Log:
	ENABLED = True

	FILE_PATH = os.getcwd() # set to None to disable file log
	FILE_LINE_LIMIT = 1000 # set to 0 for no limit

	def __make_color(code):
		return '\033[0;' + str(30 + code) + 'm'
	DEFAULT   = {'name': 'DEFAULT',   'color': '\033[0m'}
	ERROR     = {'name': 'ERROR',     'color': __make_color(1)} # red
	SUCCESS   = {'name': 'SUCCESS',   'color': __make_color(2)} # green
	WARN      = {'name': 'WARN',      'color': __make_color(3)} # yellow
	INFO      = {'name': 'INFO',      'color': __make_color(4)} # blue
	IMPORTANT = {'name': 'IMPORTANT', 'color': __make_color(5)} # purple

	@staticmethod
	def print(msg, tag='>', format='{0} - {1}', level=INFO, args=[], force=False):
		def color(msg):
			"""Add color to strings"""
			if os.name == 'posix':
				return level['color'] + msg + Log.DEFAULT['color']
			else:
				return msg
		if Log.ENABLED or force:
			formatted_msg = format.format(tag, msg, *args)
			print(color(formatted_msg))
		Log.write(msg, tag, format, level, args)

	@staticmethod
	def wrap(msg, tag='-', format='[{0}] {1}', level=INFO):
		"""Decorator used to display log as '[tag] msg'"""
		def print_msg(func):
			@wraps(func)
			def wrapper(*args, **kwargs):
				Log.print(msg, tag, format, level, args=args)
				return func(*args, **kwargs)
			return wrapper
		return print_msg

	@staticmethod
	def write(msg, tag='*', format='[{0}] {1}', level=INFO, args=[]):
		"""Write log to file"""
		if not Log.FILE_PATH: return
		timestamp = time.strftime('%Y-%m-%d_%H:%M:%S')
		log_msg = ' - '.join([timestamp, level['name'], format.format(tag, msg, *args)])
		filename = os.path.join(Log.FILE_PATH, 'log')
		if not os.path.isfile(filename):
			with open(filename, 'w'): pass
		with open(filename, 'r+') as f:
			data = f.readlines()
			data.append(log_msg + os.linesep)
			f.seek(0)
			f.truncate()
			f.writelines(data[-Log.FILE_LINE_LIMIT:])

if __name__ == '__main__':
	# sample usage
	Log.ENABLED = True # comment this line to turn off logging

	@Log.wrap('this is a messages for the method', tag='test-tag', level=Log.SUCCESS)
	def hello_world():
		Log.print('hello world')
		Log.print('this will always be printed', level=Log.WARN, force=True)
		Log.write('done', tag='verbose test', level=Log.SUCCESS)

	hello_world()

import os
from functools import wraps

__all__ = ['log', 'DEFAULT', 'ERROR_C', 'SUCCESS_C', 'IMPORTANT_C', 'INFO_C', 'WARN_C']

def _make_color(code):
	return '\033[0;' + str(30 + code) + 'm'
DEFAULT     = '\033[0m'
ERROR_C     = _make_color(1) # red
SUCCESS_C   = _make_color(2) # green
WARN_C      = _make_color(3) # yellow
INFO_C      = _make_color(4) # blue
IMPORTANT_C = _make_color(5) # purple

def color(c, msg):
	"""Add color to strings"""
	if os.name == 'posix':
		return c + msg + DEFAULT
	else:
		return msg

def log(msg, tag='-', format='[{0}] {1}', level=INFO_C):
	"""Decorator used to display log as '[tag] msg'"""
	def print_msg(func):
		@wraps(func)
		def wrapper(*args, **kwargs):
			print(color(level, format.format(tag, msg, args)))
			return func(*args, **kwargs)
		return wrapper
	return print_msg

if __name__ == '__main__':
	# sample usage
	@log('this is a messages for the method', tag='test-tag', level=SUCCESS_C)
	def hello_world():
		print('hello world')
	hello_world()

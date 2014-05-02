'''
	An example of non-blocking input I found online. Maybe a place to start.
'''

"""Treat input if available, otherwise exit without
blocking"""

import sys
import select

def something(line):
  print('read input:', line)

def something_else():
  print('no input')

# If there's input ready, do something, else do something
# else. Note timeout is zero so select won't block at all.
while sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
  line = sys.stdin.readline()
  if line:
    something(line)
  else: # an empty line means stdin has been closed
    print('eof')
    exit(0)
else:
  something_else()
"""
	This is a thread that manages a single end-to-end chat session.
"""

import socket
import threading

class ChatThread(threading.Thread):

	def __init__(self, sock, username):
		super(ChatThread, self).__init__()
		self.sock = sock      # The socket maintaining the chat connection
		#self.sock.setBlocking(0)
		self.receiver_username = username        # The receiver's username.

		# This will hold (username, chatline) pairs that record the conversation.
		self.log = []

	# Store, send, and print lines of the conversation.
	# TODO: Both recv and write need to be nonblocking...
	def run(self):
		while True:
			try:
				data = self.sock.recv(1024)
				self.log.append(self.receiver_username, data)
				print self.receiver_username + "> " + data
			except:
				print "."

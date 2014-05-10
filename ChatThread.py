"""
	CSCI 334: Distributed Systems
	Williams College
	Spring 2014

	Final Project: XChat*
	Authors: 
		Jeremy Boissevain
		Nile Livingston
		Nehemiah Paramore

	(*TEMPORARY NAME)

	This is a thread that manages a single end-to-end chat session.
"""

import socket
import threading

class ChatThread(threading.Thread):

	def __init__(self, peer, sock, username, gui):
		super(ChatThread, self).__init__()
		self.peer = peer
		self.sock = sock      # The socket maintaining the chat connection
		self.receiver_username = username        # The receiver's username.

		# This will hold (username, message) pairs that record the conversation.
		self.log = []

		self.running = True
		self.gui = gui

	# Store, send, and print lines of the conversation.
	# TODO: Both recv and write need to be nonblocking?
	def run(self):
		while self.running:
			data = self.sock.recv(1024)
			self.log.append((self.receiver_username, data))
			self.gui.updateChatLog()

	#########################################
	#	ACCESSOR METHODS
	#########################################

	# Return the chat log.
	def getLog(self):
		return self.log

	# Return the username of the receiver of this chat session.
	def getReceiver(self):
		return self.receiver_username

	#########################################
	#	MUTATOR METHODS
	#########################################

	# End the thread.
	def exit(self):
		self.sock.close()
		self.running = False

	# Send a message to the receiver of this chat session.
	def sendMessage(self, message):
		self.log.append((self.peer.getUsername(), message))
		self.sock.sendall(message)
		self.gui.updateChatLog()


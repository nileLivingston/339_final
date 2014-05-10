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

	This is a thread that manages incoming chat requests.
	On accepting a request, a new ChatThread is created and tasked with 
	managing the chat.
"""

import socket
import threading
import ChatThread as ch

class ServerThread(threading.Thread):

	# Dedicate a socket to listening.
	def __init__(self, peer, port=50007):
		super(ServerThread, self).__init__()
		HOST = ''			# Symbolic name meaning all available interfaces
		PORT = port         

		# Establish socket.
		try:
			self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		except:
			print "SERVER: Socket error: socket()"
			return

		# Bind socket.
		try:	
			self.s.bind((HOST, PORT))
			print "Server initialized with port: " + str(PORT)
		except:
			print "SERVER: Socket error: bind()"
			return

		self.peer = peer	# The peer that contains this ServerThread.

		# Should the server be running?
		self.running = True

	# Close the socket.
	def exit(self):
		print "SERVER QUITTING"
		self.s.close()
		self.running = False
	
	# Accept connections as they come, asking the peer to create new ChatThreads.
	def run(self):	
		print "Server is listening..."
		while self.running:	

			# TODO: Make nonblocking? Thread can't stop...
			self.s.listen(1)
			conn, addr = self.s.accept()

			# If user is logged in, set up a new ChatThread and add it.
			# TODO: confirm connections?
			# TODO: Authenticate/trade keys.
			print "Incoming connection from: " + str(addr)
			self.peer.addNewChatThread(conn, str(addr))


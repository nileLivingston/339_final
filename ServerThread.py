"""
	This is a thread that manages incoming chat requests.
	On accepting a request, a new ChatThread is created and tasked with 
	managing the chat.
"""

import socket
import threading
import ClientThread as cl
import ChatThread as ch

class ServerThread(threading.Thread):

	# Dedicate a socket to listening
	def __init__(self, peer, port=50007):
		super(ServerThread, self).__init__()
		HOST = ''			# Symbolic name meaning all available interfaces
		PORT = port         

		# Establish socket.
		try:
			self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		except:
			print "Socket error: socket()"
			return

		# Bind socket.
		try:	
			self.s.bind((HOST, PORT))
			print "Server initialized. Port: " + str(PORT)
		except:
			print "Socket error: bind()"
			return

		self.peer = peer	# The peer that contains this ServerThread.
	
	# Accept connections as they come, asking the peer to create new ChatThreads.
	def run(self):	
		print "Listening..."
		while True:	
			self.s.listen(1)
			conn, addr = self.s.accept()

			# If user is logged in, set up a new ChatThread and add it.
			# TODO: confirm connections?
			# TODO: Authenticate/trade keys.
			if self.peer.isLoggedIn():
				print "Incoming connection from: " + str(addr)
				self.peer.addNewChatThread(conn, addr)
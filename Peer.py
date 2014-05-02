"""
	This is going to be the main executable for the chat program.
	Each Peer is composed of various threaded processes:
		-A ServerThread that manages incoming chat requests.
		-A ClientThread that manages outgoing chat requests.
		-Some number of ChatThreads, each of which individually
		manages an end-to-end chat session.

	To Do:
		-User input needs to be nonblocking, so that incoming
		connections can be serviced. How are we going to support
		multiple chats inside the terminal? Can we? We might
		need a bare bones GUI.
		-For Jeremy: User authentication is currently trivial. We need
		to find a P2P way to do this. 
		-No RSA system yet. This is for much later.
"""

import sys
import threading

import ServerThread as sv
import ClientThread as cl
import ChatThread as ch

class Peer():

	def __init__(self):
		# A list to hold ChatThreads.
		self.chats = []

		# Start up the listener (server) and the requester (client)
		self.client = cl.ClientThread(self)
		port = int(sys.argv[1])
		self.server = sv.ServerThread(self, port)

		# Is the user logged into the chat system?
		self.logged_in = False

	def run(self):
		# Start both threads.
		self.server.start()
		self.client.start()

		# Server and client threads run until program is terminated.
		self.server.join()
		self.client.join()

	# Add a ChatThread to the list and start it.
	def addNewChatThread(self, socket, addr):
		chat = ch.ChatThread(socket, addr)
		self.chats.append(chat)
		chat.start()

	# Is the user logged into the chat system?
	def isLoggedIn(self):
		return self.logged_in

	# Set whether or not the user is logged in.
	def setLoggedIn(self, b):
		self.logged_in = b

	# Have all the threads stop so we can exit.
	#def stop(self):


if __name__ == '__main__':
	peer = Peer()
	peer.run()


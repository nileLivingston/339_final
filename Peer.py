"""
	CSCI 334: Distributed Systems
	Williams College
	Spring 2014

	Final Project: BLiP: Peer-to-Peer Chat
	Authors: 
		Jeremy Boissevain
		Nile Livingston
		Nehemiah Paramore

	This is going to be the main executable for the chat program.
	Each Peer is composed of various threaded processes:
		-A ServerThread that manages incoming chat requests.
		-Some number of ChatThreads, each of which individually
		manages an end-to-end chat session.

	To Do:
		-Maintain user state via simple text files:
			-public and private user keys
			-list of (username, public user key) pairs
		-Provide feedback in case of authentication failure. (Nile)
		-More sophisticated "chunking" for RSA. (Nile)
		-Address resolution via DHT. (Not Nile)
"""

# Libraries
import sys
import threading
import socket
import rsa

# Local files
import ServerThread as sv
import ChatThread as ch
import BLiPGUI as gui
import LoginGUI as lgui


class Peer():

	def __init__(self):
		# A list to hold ChatThreads.
		self.chats = []

		# A list to hold friends.
		self.friends = ["That guy at port 50007"]

		# The port for the listener server.
		self.port = int(sys.argv[1])

		# To hold the listener server.
		self.server = None

		# Is the user logged into the chat system?
		self.authenticated = False

		# The TKinter GUI used for BLiP.
		self.gui = None

		# To hold the username and password of the user.
		self.username = None
		self.password = None

		# The key size for the public and private user keys.
		self.key_size = 1024

		# To hold the user's public and private user keys.
		# TODO: Read from file, store them first time.
		(self.public_user_key, self.private_user_key) = rsa.newkeys(self.key_size)
		#self.public_user_key = None
		#self.private_user_key = None

	#########################################
	#	ACCESSOR METHODS
	#########################################

	# Return the list of active ChatThreads
  	def getActiveChats(self):
  		return self.chats

  	# Returns the (IP, port) pair associated with a username.
	# TODO: Address resolution stuff with a real DHT.
	def getAddress(self, username):
		return ("137.165.169.58", 50007)

  	# Returns the chat thread associated with a particular username.
	def getChatSession(self, username):
		for chat in self.chats:
			if chat.getReceiver() == username: return chat
		return "ERROR: No such chat session"

	# Return the list of friend usernames.
	def getFriends(self):
		return self.friends

	# Return the private user key.
	def getPrivateKey(self):
		return self.private_user_key

	# Return the public user key.
	def getPublicKey(self):
		return self.public_user_key

	# Return the username.
  	def getUsername(self):
  		return self.username

  	# Is the user logged into the chat system?
	def isAuthenticated(self):
		return self.authenticated


	#########################################
	#	MUTATOR METHODS
	#########################################

	# Add a username to the friends list.
	def addFriend(self, username):
		if not username in self.friends:
			self.friends.append(username)
			self.friends.sort()
			self.gui.updateFriends()

	# Add a ChatThread to the list and start it.
	def addNewChatThread(self, socket, auth_stance):
		chat = ch.ChatThread(self, socket, self.gui, auth_stance)	
		self.chats.append(chat)
		chat.start()

	def endChat(self, username):
		for chat in self.chats:
			if chat.getReceiver() == username:
				chat.exit()
				self.chats.remove(chat)
				self.gui.updateChatSessions()
				self.gui.updateChatLog()
				return

	# Make a TCP connection and start a new chat thread.
	def initiateChat(self, username):
		(IP, port) = self.getAddress(username)
		sock = self.makeConnection(IP, port)
		self.addNewChatThread(sock, "ACTIVE")

	# Authenticate the user.
	# TODO: Generate or read user keys.
	def login(self, username, password):
		self.username = username
		self.password = password
		self.server = sv.ServerThread(self, self.port)
		self.server.start()
		self.authenticated = True

	# Exit out of everything.
	def logout(self):
		for chat in self.chats:
			chat.exit()
		self.server.exit()
		self.authenticated = False

	# Make a TCP connection with (IP, port) and return socket.
	def makeConnection(self, IP, port):
		# DEBUGGING tool
		print "Connecting to " + IP + ":" + str(port) + "..."

		try:
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		except:
			print "CLIENT: Socket error: socket()"

		try:
			sock.connect((IP, port))
			return sock
		except:
			print "CLIENT: Socket error: connect()"	
		
	# Remove a username from the friends list.
	def removeFriend(self, username):
		if username in self.friends:
			self.friends.remove(username)
			self.gui.updateFriends()

	# Start up the BLiP GUI.
	def startGUI(self):
		self.gui = gui.BLiPGUI(self)
		self.gui.start()

	# Send a message to the receiving end of an active chat.
	# If no such user is active, just print a message.
	def sendMessage(self, username, message):
		for thread in self.chats:
			if thread.getReceiver() == username:
				thread.sendMessage(message)
				return
		print "ERROR: no such active chat; looking for " + username


	#########################################
	#	PRIVATE METHODS
	#########################################


def run(peer):
	loginwindow = lgui.LoginGUI(peer)
	loginwindow.run()
	while not peer.isAuthenticated():
		pass
	peer.startGUI()
	while peer.isAuthenticated():
		pass
	run(peer)

if __name__ == '__main__':
	peer = Peer()
	run(peer)



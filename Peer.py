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

	This is going to be the main executable for the chat program.
	Each Peer is composed of various threaded processes:
		-A ServerThread that manages incoming chat requests.
		-Some number of ChatThreads, each of which individually
		manages an end-to-end chat session.

	To Do:
		-P2P user authentication (Jeremy)
		-RSA encryption/decryption for privacy. (Jeremy/Nile)
		-Address resolution via Chord. (Nile/whoever else)
		-A chat protocol (Nehemiah)
"""

import sys
import threading
import socket

import ServerThread as sv
import ChatThread as ch
import XChatGUI as gui
import LoginGUI as lgui

class Peer():

	def __init__(self):
		# A list to hold ChatThreads.
		self.chats = []

		# A list to hold friends.
		self.friends = ["That guy at port 50007"]

		# Start up the listener (server).
		self.port = int(sys.argv[1])
		self.server = None

		# Is the user logged into the chat system?
		#self.logged_in = False
		self.authenticated = False

		# The TKinter GUI used for XChat.
		self.gui = None

		self.username = None
		self.password = None

	#########################################
	#	ACCESSOR METHODS
	#########################################

	# Return the list of active ChatThreads
  	def getActiveChats(self):
  		return self.chats

  	# Returns the (IP, port) pair associated with a username.
	# TODO: Chord stuff. Currently hard-coded for testing.
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
	def addNewChatThread(self, socket, username):
		chat = ch.ChatThread(self, socket, username, self.gui)	
		self.chats.append(chat)
		self.gui.updateChatSessions()
		chat.start()

	def endChat(self, username):
		for chat in self.chats:
			if chat.getReceiver() == username:
				chat.exit()
				self.chats.remove(chat)
				self.gui.updateChatSessions()
				return

	# Make a TCP connection and start a new chat thread.
	def initiateChat(self, username):
		(IP, port) = self.getAddress(username)
		sock = self.makeConnection(IP, port)
		self.addNewChatThread(sock, username)

	# Authenticate the user.
	# TODO: make real. 
	def login(self, username, password):
		self.username = username
		self.password = password
		self.server = sv.ServerThread(self, self.port)
		self.server.start()
		self.authenticated = True

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

	# Start up the XChat GUI.
	def startGUI(self):
		self.gui = gui.XChatGUI(self)
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
	#	DEBUGGING/PRINT METHODS
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



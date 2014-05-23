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
		-Address resolution via DHT.
		-Evaluation

	Bugs to fix:
		-Sending too much chat data breaks receiver,
		due to RSA VARBLOCK stuff. You have to send
		around 1000 chars at once to break it.
"""

# Libraries
import sys
import threading
import socket
import rsa
import os
import os.path
import random

# Local files
import ServerThread as sv
import ChatThread as ch
import BLiPGUI as gui
import LoginGUI as lgui


class Peer():

	def __init__(self, gui_enabled=True):
		# A list to hold ChatThreads.
		self.chats = []

		# To hold (username, public user key) pairs.
		self.friends = dict()

		# The file path for the persistent friends list.
		# This file contains lines of the form:
		# 	friend_username,key.n,key.e
		self.friendsFilePath = "friends.txt"

		# The filename storing the user keys
		self.userKeyFilePath = 'user_keys.pem'

		# Grab the friends file and extract to self.friends.
		if os.path.isfile(self.friendsFilePath):
			f = open(self.friendsFilePath, "r")
			lines = f.readlines()
			f.close()
			for line in lines:
				parts = line.split(",")
				username = parts[0]
				key_n = long(parts[1])
				key_e = long(parts[2])
				self.friends[username] = rsa.PublicKey(key_n, key_e)
		# Make the friends file.
		else:
			f = open(self.friendsFilePath, "w")
			f.close()

		# The port for the listener server.
		# TODO: Currently a command line argument for testing. Set to constant later.
		self.port = int(sys.argv[1])

		# To hold the listener server.
		self.server = None

		# Is the user logged into the chat system?
		self.authenticated = False

		self.gui_enabled = gui_enabled

		if not self.gui_enabled:
			self.port = random.randint(40000, 50000)

		# The TKinter GUI used for BLiP.
		self.gui = None

		self.username = None

		# The key size for the public and private user keys.
		self.key_size = 1024

		# To hold the user's public and private user keys.
		self.public_user_key = None
		self.private_user_key = None
	

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
  	# Return None if no such chat session exists.
	def getChatSession(self, username):
		for chat in self.chats:
			if chat.getReceiver() == username: return chat
		return None

	# Return the list of friend usernames.
	def getFriends(self):
		output = self.friends.keys()
		output.sort()
		return output

	# Return the private user key.
	def getPrivateKey(self):
		return self.private_user_key

	# Return the public user key.
	def getPublicKey(self):
		return self.public_user_key

	# Return the username.
  	def getUsername(self):
  		return self.username

  	# Get the public user key for a particular username.
  	def getUserKeyFor(self, username):
  		return self.friends[username]

  	# Is the user logged into the chat system?
	def isAuthenticated(self):
		return self.authenticated


	#########################################
	#	MUTATOR METHODS
	#########################################

	# Add a username to the friends list without knowing public key.
	def addFriend(self, username):
		if username in self.friends:
			if self.gui_enabled:
				self.gui.showMessage("This username is already in your friends list.")
			return

		# Forever alone
		if username == self.username:
			if self.gui_enabled:
				self.gui.showMessage("You cannot be friends with yourself.")
			return
		
		self.addUserAndKey(username, None)

	# Add a username and associated key to friends list.
	def addUserAndKey(self, username, key):

		# Name already in file, just need to update key.
		if username in self.friends:

			# Get all of the current content of the friends file, but
			# overwrite the line with the username we're looking for.
			f = open(self.friendsFilePath, "r")
			lines = f.readlines()
			contents = ""
			for line in lines:
				cur = line[:line.index(',')]
				if not cur == username:
					contents += line
				else:
					contents += cur + "," + str(key.n) + "," + str(key.e) + "\n"
			f.close()

			# Remove the file.
			os.remove(self.friendsFilePath)

			# Rewrite the file with the updated info.
			f = open(self.friendsFilePath, "w+")
			f.write(contents)
			f.close()

		# Name not in file, just append the line.
		else:
			f = open(self.friendsFilePath, "a")
			if key == None:
				f.write(username + ",None,None\n")
			else:
				f.write(username + "," + str(key.n) + "," + str(key.e) + "\n")
			f.close()

		# Update the dict and the GUI.
		self.friends[username] = key
		if self.gui_enabled:
			self.gui.updateFriends()

	# Add a ChatThread to the list and start it.
	def addNewChatThread(self, socket, auth_stance):
		chat = ch.ChatThread(self, socket, self.gui, auth_stance)	
		self.chats.append(chat)
		chat.start()

	# End the chat session associated with a particular username.
	# stance describes whether we're leaving or being left.
	# values are "ACTIVE" and "PASSIVE", respectively.
	def endChat(self, username, stance):
		for chat in self.chats:
			if chat.getReceiver() == username:
				chat.exit(stance)
				self.chats.remove(chat)
				if self.gui_enabled:
					self.gui.updateChatSessions()
					self.gui.updateChatLog()
				return

	# Make a TCP connection and start a new chat thread.
	def initiateChat(self, username):
		# Get the address and make the connection.
		(IP, port) = self.getAddress(username)
		sock = self.makeConnection(IP, port)

		# If socket fails, friend is not online.
		if sock == None:
			if self.gui_enabled:
				self.gui.showMessage("Friend is not online.")
			return
		
		# Create chat thread.
		self.addNewChatThread(sock, "ACTIVE")

	# Authenticate the user.
	def login(self, username):
		self.username = username

		# .pem file exists, read from it.
		if os.path.isfile(self.userKeyFilePath): 
			keyFile = open(self.userKeyFilePath, 'r').read()
			self.public_user_key = rsa.PublicKey.load_pkcs1(keyFile)
			self.private_user_key = rsa.PrivateKey.load_pkcs1(keyFile)
			
		# .pem file doesn't exist, generate new keys and write to file.
		else:
			(self.public_user_key, self.private_user_key) = rsa.newkeys(self.key_size)
			keyFile = open(self.userKeyFilePath, 'w')
			public_Pem = self.public_user_key.save_pkcs1()
			private_Pem = self.private_user_key.save_pkcs1()
			keyFile.write(public_Pem)
			keyFile.write(private_Pem)
		
		self.authenticated = True

		# Start up the listener server.
		self.server = sv.ServerThread(self, self.port)
		self.server.start()
		

	# Exit out of everything.
	def logout(self):
		for chat in self.chats:
			chat.exit("ACTIVE")
		self.server.exit()
		self.authenticated = False

	# Make a TCP connection with (IP, port) and return socket.
	# Return None if socket fails.
	def makeConnection(self, IP, port):
		# DEBUGGING tool
		print "Connecting to " + IP + ":" + str(port) + "..."

		try:
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		except:
			print "CLIENT: Socket error: socket()"
			return None

		try:
			sock.connect((IP, port))
			return sock
		except:
			print "CLIENT: Socket error: connect()"	
			return None
		
	# Remove a username from the friends list.
	def removeFriend(self, username):
		if username in self.friends:
			# Remove friend from file.
			f = open(self.friendsFilePath, "r")
			lines = f.readlines()
			contents = ""
			for line in lines:
				cur = line[:line.index(',')]
				if not cur == username:
					contents += line
			f.close()
			os.remove(self.friendsFilePath)
			f = open(self.friendsFilePath, "w+")
			f.write(contents)
			f.close()

			# Update dict and GUI.
			self.friends.pop(username)
			if self.gui_enabled:
				self.gui.updateFriends()
		else:
			if self.gui_enabled:
				self.gui.showMessage("This username is not in your friends list.")
			return

	# Start up the BLiP GUI.
	def startGUI(self):
		self.gui = gui.BLiPGUI(self)
		self.gui.start()

	# Send a message to the receiving end of an active chat.
	# If no such user is active, return None.
	def sendMessage(self, username, message):
		for thread in self.chats:
			if thread.getReceiver() == username:
				thread.sendMessage(message)
				return
		return None

	def stressSendMessage(self, username, message):
		while True:
			for thread in self.chats:
				if thread.getReceiver() == username:
					while thread.isAuthenticating():
						pass
					for i in range(1, 11):
						thread.sendMessage("[" + str(i) + "]" + message)
					return

################################################################
#	Main method stuff below.
################################################################

# Login/logout loop for BLiP.
def run(peer):
	loginwindow = lgui.LoginGUI(peer)
	loginwindow.run()
	while not peer.isAuthenticated():
		pass
	peer.startGUI()
	while peer.isAuthenticated():
		pass
	run(peer)

# Used for stress testing number of concurrent chats.
def stressRun(the_peer, receiver):
	# Use random username to avoid conflicts
	the_peer.login(str(random.getrandbits(20)))
	the_peer.addFriend(receiver)
	the_peer.initiateChat(receiver)
	the_peer.stressSendMessage(receiver, "This is a stress message. It is pretty short.")
	the_peer.endChat(receiver, "ACTIVE")
	the_peer.logout()

if __name__ == '__main__':
	peer = Peer()
	run(peer)



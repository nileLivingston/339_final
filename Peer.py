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
		-More sophisticated "chunking" for RSA. (Nile)
		-Address resolution via DHT.
		-Evaluation 
"""

# Libraries
import sys
import threading
import socket
import rsa
import os
import os.path
import json
import entangled.kademlia.node
import twisted
import ast

# Local files
import ServerThread as sv
import ChatThread as ch
import BLiPGUI as gui
import LoginGUI as lgui
import NodeThread as nt


class Peer():

	def __init__(self):
		# A list to hold ChatThreads.
		self.chats = []

		# To hold (username, public user key) pairs.
		self.friends = dict()
		self.friendObjects = dict()

		# The file path for the persistent friends list.
		# This file contains lines of the form:
		# 	friend_username,key.n,key.e
		self.friendsJson = 'friends.json'

		# The filename storing the user keys


		self.userKeyFilePath = 'user_keys.pem'

		# Given that I'm now treating the friends file as a Json File
		if os.path.isfile(self.friendsJson):
			f = open(self.friendsJson, "r+")
			try:
				data = json.load(f)
				for info in data.itervalues():
					for key, val in info.iteritems():
						if isinstance(val, unicode):
							info[key] = val.encode('utf-8')
					info["key"] = rsa.PublicKey.load_pkcs1(info["key"])

				self.friendObjects = data

				for friend, info in self.friendObjects.iteritems():
					self.friends[friend] = info["key"]

			except ValueError, e:
				print "ValueError"
				print e
			except Exception, e:
				print e

			f.close()

		else:
			data = open(self.friendsJson, "w")
			data.close()

		# The port for the listener server.
		# TODO: Currently a command line argument for testing. Set to constant later.
		self.port = int(sys.argv[1])

		#the port for the kademlia node
		self.udp_port = int(sys.argv[2])

		# To hold the listener server.
		self.server = None

		# Is the user logged into the chat system?
		self.authenticated = False

		# The TKinter GUI used for BLiP.
		self.gui = None

		self.username = None

		# The key size for the public and private user keys.
		self.key_size = 1024

		# To hold the user's public and private user keys.
		self.public_user_key = None
		self.private_user_key = None

		# DHT node thread
		self.node = None

	#########################################
	#	ACCESSOR METHODS
	#########################################

	# Return the list of active ChatThreads
	def getActiveChats(self):
		return self.chats

	def getOwnAddress(self):
		return (str(socket.gethostbyname(socket.getfqdn())), self.port)

	# Returns the (IP, port) pair associated with a username.
	# TODO: Address resolution stuff with a real DHT.
	def getAddress(self, username):
		ret = []
		def gotValue(result):
			print result
			ret = result
			
		df = self.node.searchForKeywords([username])
		df.addCallback(gotValue)
		return ret

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
		# Forever alone
		if username == self.username:
			self.gui.showMessage("You cannot be friends with yourself.")
			return
		self.addUserAndKey(username, None, None, None)

				
	# Add a username and associated key to friends list.
	def addUserAndKey(self, username, key, ip, port):
		#change friend dictionary
		friend = {"key":key, "ip": ip, "port":port}

		self.friendObjects[username] = friend
		self.friends[username] = key

		#remove existing file
		os.remove(self.friendsJson)

		#copy the friendObjects, and then change the value of key so that it can be saved in a file
		tmp = self.friendObjects.copy()
		tmp[username]["key"] = tmp[username]["key"].save_pkcs1()

		#write to file
		f = open(self.friendsJson, "w")
		json.dump(tmp, f)

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

		#Create entangled node and start node thread
		self.node = nt.NodeThread(self.udp_port)
		self.node.start()

		#Generate list of known friend IPs
		ipList = []
		portList = []
		for info in self.friendObjects.itervalues():
			if info["ip"] != None:
				ipList.append( info["ip"])
				portList.append( info["port"])
		#Attempt to join network using list of known IPs
		result = zip(ipList, portList)
		print result
		self.node.joinNetwork(result)

		self.node.printContacts()
		#TODO: Add notification if none of the IPs found were online and able to be joined.

		#Publish own data to the network
		def completed(result):
			print result
		df = self.node.publishData(self.username, self.getOwnAddress())
		df.addCallback(completed)

	# Exit out of everything.
	def logout(self):
		for chat in self.chats:
			chat.exit("ACTIVE")
		self.server.exit()
		self.node.exit()
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
			self.gui.updateFriends()

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

if __name__ == '__main__':
	peer = Peer()
	run(peer)
	twisted.internet.reactor.run()


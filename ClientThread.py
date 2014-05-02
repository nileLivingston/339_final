"""
	This is a thread that manages outgoing chat requests.
"""

import socket
import getpass
import threading

class ClientThread(threading.Thread):

	def __init__(self, peer=None):
		super(ClientThread, self).__init__()
		self.peer = peer
		self.username = ""
		self.password = ""
		self.friends = ["Andy","Beth","Chuck"]

	def run(self):		
		# Master loop.	
		while True:
			self.authenticate()

			# Input command loop.
			print "Welcome, " + self.username + "! What would you like to do?"
			print "/friends"
			print "/addfriend"
			print "/removefriend"
			print "/connect"
			print "/logout"
			print "/help"
			while True:
				command = raw_input("> ").lower()
				if command == "/friends":
					print "Friends list: "
					for friend in self.friends:
						print "   " + friend

				elif command == "/addfriend":
					print "Please enter your friend's XChat username:"
					username = raw_input("> ")
					self.friends.append(username)
					self.friends.sort()
					print username + " added to your friends list!"

				elif command == "/removefriend":
					print "Please enter your friend's XChat username to remove:"
					username = raw_input("> ")
					try:
						self.friends.remove(username)
						print username + " successfully removed from your friends list."
					except:
						print username + " was not in your friends list."

				elif command == "/connect":
					print "Who do you want to connect to?"
					username = raw_input("> ")
					(IP, port) = self.getAddress(username)
					self.makeConnection(IP, port)

				elif command == "/logout":
					self.username = ""
					self.password = ""
					self.peer.setLoggedIn(False)
					print "Successfully logged out."
					break

				elif command == "/help":
					print "/friends - Display your friends list"
					print "/addfriend - Add a username to your friends list"
					print "/connect - Connect to a friend."
					print "/logout - Logout of the XChat system."
					print "/help - Prints this list of commands."

				else:
					print "That's not a valid command. Use \'/help\' if you need assistance."

				'''
				while True:
					try:
						self.makeConnection()
						break
					except socket.error:
						print "Something went wrong, connection failed. Did you enter the right address?"
					except:
						return
				print "You're now chatting with " + self.receiver_host + ":" + str(self.receiver_port) + "!"
				self.sendMessages()
				'''

	# Authenticate the user's login information.
	# TODO: Make this real authentication.
	def authenticate(self):
		print "Welcome to XChat! Please login."
		self.username = raw_input("username: ")
		self.password = getpass.getpass("password: ")

		realpass = "1234"
		while not self.password == realpass:
			print "Sorry, that login info didn't match. Try again."
			self.username = raw_input("username: ")
			self.password = getpass.getpass("password: ")
		if not self.peer == None:
			self.peer.setLoggedIn(True)

	def makeConnection(self, IP, port):
		print "Connecting you to " + IP + ":" + str(port) + "..."

		try:
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		except:
			print "Socket error: socket()"

		try:
			sock.connect((IP, port))
		except:
			print "Socket error: connect()"

		self.peer.addNewChatThread(sock, IP)

	# NOT IMPLEMENTED: hardcoded return.
	def getAddress(self, username):
		return ("137.165.169.58", 50007)

	'''
		Should be handled inside of ChatThread
	'''
	# def sendMessages(self):
	# 	while True:
	# 		message = raw_input(self.username + "> ")
	# 		if message == "/leave":
	# 			self.sock.close()
	# 			print "Connection closed."
	# 			return	
	# 		else:
	# 			self.sock.sendall(message)
	# 			data = self.sock.recv(1024)
	# 			print self.receiver_host + ":" + str(self.receiver_port) + "> " + repr(data)


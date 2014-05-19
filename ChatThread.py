"""
	CSCI 334: Distributed Systems
	Williams College
	Spring 2014

	Final Project: BLiP: Peer-to-Peer Chat
	Authors: 
		Jeremy Boissevain
		Nile Livingston
		Nehemiah Paramore

	This is a thread that manages a single end-to-end chat session.
"""

import socket
import threading
import rsa
from rsa.bigfile import *
import random

class ChatThread(threading.Thread):

	def __init__(self, peer, sock, gui, auth_stance):
		# Required for threading purposes.
		super(ChatThread, self).__init__()

		# The Peer managing this ChatThread.
		self.peer = peer	

		# The socket maintaining the chat connection.
		self.sock = sock 

		# This will hold strings that record the conversation.
		self.log = []

		# For control logic in run()
		self.running = True

		# The BLiPGUI window containing this chat. Used to call updates.
		self.gui = gui

		# To hold session RSA keys.
		# (We don't compute until AFTER authentication because it's expensive.)
		self.public_session_key = None
		self.private_session_key = None

		# To hold the username of the receiver.
		self.receiver_username = None

		# To hold the public user key of the receiver.
		self.receiver_user_key = None

		# To hold the public session key of the receiver.
		self.receiver_public_session_key = None

		# Describes whether the chat thread is requesting or receiving the chat request;
		# important for authentication purposes. Value is either "ACTIVE" or "PASSIVE".
		self.auth_stance = auth_stance

		# The bit size of the session keys.
		self.key_size = 512 

	# Store, send, and print lines of the conversation.
	def run(self):
		# Exchange usernames and keys, authenticate, exchange session keys.
		if self.auth_stance == "ACTIVE":
			self.activeHandshake()
			success = self.activeAuthenticate()
			if not success:
				return
			self.peer.addUserAndKey(self.receiver_username, self.receiver_user_key)
			self.activeSessionKeyExchange()
		elif self.auth_stance == "PASSIVE":
			self.passiveHandshake()
			success = self.passiveAuthenticate()
			if not success:
				return
			self.peer.addUserAndKey(self.receiver_username, self.receiver_user_key)
			self.passiveSessionKeyExchange()

		self.gui.updateChatSessions()

		self.log.append("----Secure connection established----")
		self.log.append("----Now chatting with " + self.receiver_username + "----")
		self.gui.updateChatLog()
		

		while self.running:
			data = self.sock.recv(1024)

			if data == "/FAREWELL":
				self.peer.endChat(self.receiver_username, "PASSIVE")
				return

			# Decrypt the message.
			decrypted = rsa.decrypt(data, self.private_session_key)

			# Append the message to the log and call the GUI update.
			self.log.append(self.receiver_username + " > " + decrypted)
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
	# stance describes whether we're leaving or being left.
	# Values are "ACTIVE" and "PASSIVE", respectively.
	def exit(self, stance):

		if stance == "ACTIVE":
			# Send leaving message to receiver
			self.sendFarewell()
		elif stance == "PASSIVE":
			self.gui.showMessage(self.receiver_username + " has ended the chat session.")

		# Close the socket.
		self.sock.close()

		# So we can leave the run() loop.
		self.running = False

	# Send a message to the receiver of this chat session.
	def sendMessage(self, message):
		# Split message into (self.key_size / 8) - 11 chunks
		# TODO: TEMPORARY SOLUTION, For encryption purposes
		chunk_size = int((self.key_size / 8) - 11)
		messages = []
		for i in xrange(0, len(message), chunk_size):
			messages.append(message[i:i+chunk_size])

		for message in messages:
			# Update the chat log.
			self.log.append(self.peer.getUsername() + " > " +  message)

			# Encrypt the message.
			message = rsa.encrypt(message, self.receiver_public_session_key)

			# Send the message
			self.sock.sendall(message)

		# Update the GUI.
		self.gui.updateChatLog()

	# Verify identity of receiver.
	# From perspective of chat session initiator.
	def activeAuthenticate(self):
		# Grab key for receiver username and compare it against what the receiver gave us.
		# try:
		key = self.peer.getUserKeyFor(self.receiver_username)
		# Friend was added but never authenticated:
		if key == None:
			my_congruent_state = "True"
		else:
			my_congruent_state = str(self.receiver_user_key == key)
		# No key was found, so this person is new.
		# TODO: I don't think this is needed...
		# except KeyError:
		# 	my_congruent_state = "True"

		# If key is empty or matches, proceed.
		if my_congruent_state == "True":
			self.sock.sendall("True")
			# Receive congruent state message from receiver.
			their_congruent_state = self.sock.recv(1024)

			# If their state is congruent, proceed.
			if their_congruent_state == "True":
				# Compose verifier int V and send it.
				my_verifier = str(random.getrandbits(512))
				self.sock.sendall(my_verifier)

				# Receive initiator's verifier string
				their_verifier = self.sock.recv(1024)

				# Sign and send
				my_signature = rsa.sign(their_verifier, self.peer.getPrivateKey(), 'SHA-1')
				self.sock.sendall(my_signature) 

				# Receive initiator's signature
				their_signature = self.sock.recv(1024)

				# Verify the signature and send the response.
				try:
					my_decision = rsa.verify(my_verifier, their_signature, self.receiver_user_key)
					self.sock.sendall(str(my_decision))
				except rsa.VerificationError:
					self.sock.sendall("False")
					self.peer.endChat(self.receiver_username)
					return False

				# Receive initiator's authorization status.
				their_decision = self.sock.recv(1024)
				if not their_decision == "True":
					self.peer.endChat(self.receiver_username)
					return False
				else:
					return True
			# Their state was incongruent, session should end.
			else:
				self.gui.showMessage("Authentication failure: your credentials were rejected.")
				self.peer.endChat(self.receiver_username)
				return False
		# State is incongruent; reject session.
		else: 
			self.sock.sendall("False")
			self.peer.endChat(self.receiver_username)
			return False

	# Exchange usernames and public user keys.
	# From perspective of chat session initiator.
	def activeHandshake(self):
		username = self.peer.getUsername()
		pub_key = self.peer.getPublicKey()
		# Pack into protocol and send.
		encoded = username + "," + str(pub_key.n) + "," + str(pub_key.e)
		self.sock.sendall(encoded)

		# Receive (initiator username, initiator public key)
		decoded = self.sock.recv(1024).split(",")
		# Decode and assign.
		self.receiver_username = decoded[0]
		self.receiver_user_key = rsa.PublicKey(long(decoded[1]), long(decoded[2]))

	# Generate and exchange public session keys with the receiver.
	# From perspective of chat session initiator.
	def activeSessionKeyExchange(self):
		# Generate (public, private) session keys.
		(self.public_session_key, self.private_session_key) = rsa.newkeys(self.key_size)
		my_n = str(self.public_session_key.n)
		my_e = str(self.public_session_key.e)
		# Pack into protocol and send.
		encoded = my_n + "," + my_e
		self.sock.sendall(encoded)

		# Receive (n, e) from receiver.
		decoded = self.sock.recv(1024).split(",")
		# Decode and assign
		receiver_n = long(decoded[0])
		receiver_e = long(decoded[1])
		self.receiver_public_session_key = rsa.PublicKey(receiver_n, receiver_e)

	# Exchange usernames and public user keys with receiver, then authenticate.
	# From perspective of chat session reciprocator.
	# Returns whether or not authentication
	def passiveAuthenticate(self):
		# Receive congruent state message from receiver.
		their_congruent_state = self.sock.recv(1024)
		# If their state is congruent, proceed.
		if their_congruent_state == "True":

			# Grab key for receiver username and compare it against what the receiver gave us.
			try:
				key = self.peer.getUserKeyFor(self.receiver_username)
				# Friend was added, but never authenticated.
				if key == None:
					my_congruent_state = "True"
				else:
					my_congruent_state = str(self.receiver_user_key == key)
			# No key found, so new person.
			except KeyError:
				my_congruent_state = "True"

			# If key is empty or matches, proceed.
			if my_congruent_state == "True":
				self.sock.sendall("True")

				# Receive initiator's verifier string
				their_verifier = self.sock.recv(1024)

				# Compose verifier int V and send it.
				my_verifier = str(random.getrandbits(512))
				self.sock.sendall(my_verifier)

				# Receive initiator's signature
				their_signature = self.sock.recv(1024)

				# Sign and send
				my_signature = rsa.sign(their_verifier, self.peer.getPrivateKey(), 'SHA-1')
				self.sock.sendall(my_signature) 

				# Receive initiator's authorization status.
				their_decision = self.sock.recv(1024)
				if not their_decision == "True":
					self.peer.endChat(self.receiver_username)
					return False

				# Verify the signature and send the response.
				try:
					my_decision = rsa.verify(my_verifier, their_signature, self.receiver_user_key)
					self.sock.sendall(str(my_decision))
					return True
				# Verification failed, reject.
				except rsa.VerificationError:
					self.sock.sendall("False")
					self.peer.endChat(self.receiver_username)
					return False

			# Our state was incongruent, reject.
			else:
				self.sock.sendall("False")
				self.peer.endChat(self.receiver_username)
				return False
		# Their state was incongruent, session should end.
		else: 
			self.gui.showMessage("Authentication failure: your credentials were rejected.")
			self.peer.endChat(self.receiver_username)
			return False

	# Exchange usernames and public user keys.
	# From perspective of chat session reciprocator.
	def passiveHandshake(self):
		# Receive (initiator username, initiator public key)
		decoded = self.sock.recv(1024).split(",")
		# Decode and assign.
		self.receiver_username = decoded[0]
		self.receiver_user_key = rsa.PublicKey(long(decoded[1]), long(decoded[2]))
 
		username = self.peer.getUsername()
		pub_key = self.peer.getPublicKey()
		# Pack into protocol and send.
		encoded = username + "," + str(pub_key.n) + "," + str(pub_key.e)
		self.sock.sendall(encoded)

	# Generate and exchange public session keys with the receiver.
	# From perspective of chat session reciprocator.
	def passiveSessionKeyExchange(self):
		# Receive (n, e) from receiver.
		decoded = self.sock.recv(1024).split(",")
		# Decode and assign
		receiver_n = long(decoded[0])
		receiver_e = long(decoded[1])
		self.receiver_public_session_key = rsa.PublicKey(receiver_n, receiver_e)

		# Generate (public, private) session keys.
		(self.public_session_key, self.private_session_key) = rsa.newkeys(self.key_size)
		my_n = str(self.public_session_key.n)
		my_e = str(self.public_session_key.e)
		# Pack into protocol and send.
		encoded = my_n + "," + my_e
		self.sock.sendall(encoded)
		
	# End the chat according to the protocol.
	def sendFarewell(self):
		self.sock.sendall("/FAREWELL")

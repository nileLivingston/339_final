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

		# This will hold (username, message) pairs that record the conversation.
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
	# TODO: Add protocol functionality.
	def run(self):
		# Exchange usernames and keys, authenticate, exchange session keys.
		print "RUNNING"
		if self.auth_stance == "ACTIVE":
			self.activeHandshake()
			print "Handshake completed"
			success = self.activeAuthenticate()
			if not success:
				return
			print "Authentication completed"
			self.activeSessionKeyExchange()
			print "Session key exchange completed"
		elif self.auth_stance == "PASSIVE":
			self.passiveHandshake()
			print "Handshake completed"
			success = self.passiveAuthenticate()
			if not success:
				return
			print "Authentication completed"
			self.passiveSessionKeyExchange()
			print "Session key exchange completed"
		self.gui.updateChatSessions()

		while self.running:
			data = self.sock.recv(1024)

			if data == "/FAREWELL":
				self.peer.endChat(self.getReceiver())
				return

			# Pass the data through the protocol decoder.
			# protocol_decoded = decoder.getMessage(data)
			# protocol_decoded = data

			# Decrypt the message
			decrypted = rsa.decrypt(data, self.private_session_key)

			self.log.append((self.receiver_username, decrypted))
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
		# Send leaving message to receiver
		self.sendFarewell()

		# Close the socket.
		self.sock.close()

		# So we can leave the run() loop.
		self.running = False

		# DEBUG MESSAGE
		print "CHAT THREAD EXITING"

	# Send a message to the receiver of this chat session.
	def sendMessage(self, message):
		# Split message into (self.key_size / 8) - 11 chunks
		# TEMPORARY SOLUTION, For encryption purposes
		chunk_size = int((self.key_size / 8) - 11)
		messages = []
		for i in xrange(0, len(message), chunk_size):
			messages.append(message[i:i+chunk_size])

		for message in messages:
			# Update the chat log.
			self.log.append((self.peer.getUsername(), message))

			# Encrypt the message.
			message = rsa.encrypt(message, self.receiver_public_session_key)

			# Send the message
			self.sock.sendall(message)

		# Update the GUI.
		self.gui.updateChatLog()

	# Verify identity of receiver.
	# From perspective of chat session reciprocator.
	def activeAuthenticate(self):
		# TODO: check if we have (initator username, initiator public key) in state or have nothing for receiver username:
		# ...

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
			self.peer.endChat(self.getReceiver())
			return False

		# Receive initiator's authorization status.
		their_decision = self.sock.recv(1024)
		if not their_decision:
			self.peer.endChat(self.getReceiver())
			return False
		else:
			return True
		# else if we have an incongruent key:
			# reject

	# Exchange usernames and public user keys.
	# From perspective of chat session initiator.
	def activeHandshake(self):
		username = self.peer.getUsername()
		pub_key = self.peer.getPublicKey()
		# Pack into protocol and send.
		encoded = username + "," + str(pub_key.n) + "," + str(pub_key.e)
		self.sock.sendall(encoded)

		# Receive (initiator username, initiator public key)
		encoded = self.sock.recv(1024).split(",")
		# Decode and assign.
		self.receiver_username = encoded[0]
		self.receiver_user_key = rsa.PublicKey(long(encoded[1]), long(encoded[2]))

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
		encoded = self.sock.recv(1024).split(",")
		# Decode and assign
		receiver_n = long(encoded[0])
		receiver_e = long(encoded[1])
		self.receiver_public_session_key = rsa.PublicKey(receiver_n, receiver_e)

	# Exchange usernames and public user keys with receiver, then authenticate.
	# From perspective of chat session reciprocator.
	# Returns whether or not authentication
	def passiveAuthenticate(self):
		# TODO: check if we have (initator username, initiator public key) in state or have nothing for receiver username:
		# ...
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
		if not their_decision:
			self.peer.endChat(self.getReceiver())
			return False

		# Verify the signature and send the response.
		try:
			my_decision = rsa.verify(my_verifier, their_signature, self.receiver_user_key)
			self.sock.sendall(str(my_decision))
			return True
		except rsa.VerificationError:
			self.peer.endChat(self.getReceiver())
			return False

		# else if we have an incongruent key:
			# reject

	# Exchange usernames and public user keys.
	# From perspective of chat session reciprocator.
	def passiveHandshake(self):
		# Receive (initiator username, initiator public key)
		encoded = self.sock.recv(1024).split(",")
		# Decode and assign.
		self.receiver_username = encoded[0]
		self.receiver_user_key = rsa.PublicKey(long(encoded[1]), long(encoded[2]))
 
		username = self.peer.getUsername()
		pub_key = self.peer.getPublicKey()
		# Pack into protocol and send.
		encoded = username + "," + str(pub_key.n) + "," + str(pub_key.e)
		self.sock.sendall(encoded)

	# Generate and exchange public session keys with the receiver.
	# From perspective of chat session reciprocator.
	def passiveSessionKeyExchange(self):
		# Receive (n, e) from receiver.
		encoded = self.sock.recv(1024).split(",")
		# Decode and assign
		receiver_n = long(encoded[0])
		receiver_e = long(encoded[1])
		self.receiver_public_session_key = rsa.PublicKey(receiver_n, receiver_e)

		# Generate (public, private) session keys.
		(self.public_session_key, self.private_session_key) = rsa.newkeys(self.key_size)
		my_n = str(self.public_session_key.n)
		my_e = str(self.public_session_key.e)
		# Pack into protocol and send.
		encoded = my_n + "," + my_e
		self.sock.sendall(encoded)
		
	# End the chat according to the protocol.
	# TODO: ??
	def sendFarewell(self):
		self.sock.sendall("/FAREWELL")

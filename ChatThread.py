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
import os
import Queue as q

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

		#receiver ip
		self.receiver_ip = None

		#receiver udp port
		self.receiver_udp_port = None

		# Describes whether the chat thread is requesting or receiving the chat request;
		# important for authentication purposes. Value is either "ACTIVE" or "PASSIVE".
		self.auth_stance = auth_stance

		self.authenticating = True

		# The bit size of the session keys.
		self.key_size = 512 

		# The bit size of chat messages.
		self.message_size = 1024

		# Port to use
		self.udp_port = self.peer.udp_port

	# Store, send, and print lines of the conversation.
	def run(self):
		# Exchange usernames and keys, authenticate, exchange session keys.
		if self.auth_stance == "ACTIVE":
			self.activeHandshake()
			success = self.activeAuthenticate()
			if not success:
				return
			self.peer.addUserAndKey(self.receiver_username, self.receiver_user_key, self.receiver_ip, self.receiver_udp_port)
			self.activeSessionKeyExchange()

		elif self.auth_stance == "PASSIVE":
			self.passiveHandshake()
			success = self.passiveAuthenticate()
			if not success:
				return
			self.peer.addUserAndKey(self.receiver_username, self.receiver_user_key, self.receiver_ip, self.receiver_udp_port)
			self.passiveSessionKeyExchange()

		if not self.gui == None:
			self.gui.updateChatSessions()

		self.log.append("----Secure connection established----")
		self.log.append("----Now chatting with " + self.receiver_username + "----")
		if not self.gui == None:
			self.gui.updateChatLog()
		
		# To hold a queue of chat messages.
		message_queue = q.Queue()
		self.authenticating = False
		while self.running:
			
			# Get data from the socket.
			# Push individual messages into the queue.
			if message_queue.empty():
				data = self.sock.recv(self.message_size)
				messages = data.split("/END_MESSAGE")
				for message in messages:
					if not message == "":
						message_queue.put(message)

			data = message_queue.get()

			# Kick out if we're not running.
			# Redundant but necessary.
			if not self.running:
				return

			# On receiving this command, chat should end.
			if data == "/FAREWELL":
				self.peer.endChat(self.receiver_username, "PASSIVE")
				return

			# Filepaths for temp files.
			encr_filepath = "encr"
			decr_filepath = "decr"

			# For multiple threads sharing a directory.
			# encr_filepath = str(random.randint(1, 50000))
			# decr_filepath = str(random.randint(1, 50000))

			# Write the encrypted message into a file.
			f = open(encr_filepath, "w+")
			f.write(data)
			f.close()

			# Decrypt the message using VARBLOCK format.
			with open(encr_filepath, 'rb') as infile, open(decr_filepath, 'w+') as outfile:
				decrypt_bigfile(infile, outfile, self.private_session_key)

			# Copy the contents of the decrypted file to a string.
			f = open(decr_filepath, "r")
			decrypted = f.read(os.stat(decr_filepath).st_size)
			f.close()

			# Remove the temporary files.
			os.remove(encr_filepath)
			os.remove(decr_filepath)

			# Append the message to the log and call the GUI update.
			self.log.append(self.receiver_username + " > " + decrypted)
			if not self.gui == None:
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

	# Is the chat session in the middle of authentication?
	# Used to delay sending messages for stress testing.
	def isAuthenticating(self):
		return self.authenticating

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
			if not self.gui == None:
				self.gui.showMessage(self.receiver_username + " has ended the chat session.")

		# Close the socket.
		self.sock.close()

		# So we can leave the run() loop.
		self.running = False

	# Send a message to the receiver of this chat session.
	def sendMessage(self, message):
		
		num_blocks = self.message_size / (64 * 8)
		# Chunk size = Message size - encryption overhead - protocol overhead (all in bits).
		chunk_size = self.message_size - (11 * 8 * num_blocks) - (12 * 8)
		
		# Split up messages into chunks.
		messages = []
		for i in xrange(0, len(message), chunk_size):
			messages.append(message[i:i+chunk_size])

		# For each chunk.
		for message in messages:

			# Update the chat log.
			self.log.append(self.peer.getUsername() + " > " +  message)

			
			# Filepaths for temp files.
			in_filepath = "plaintext"
			out_filepath = "ciphertext"

			# For threads sharing the same directory
			# in_filepath = str(random.randint(1, 50000))
			# out_filepath = str(random.randint(1, 50000))

			# Write the plaintext message to a file.
			f = open(in_filepath, "w")
			f.write(message)
			f.close()

			# Encrypt the message file.
			with open(in_filepath, 'rb') as infile, open(out_filepath, 'wb') as outfile:
				encrypt_bigfile(infile, outfile, self.receiver_public_session_key)

			# Copy the encrypted file contents to a string.
			f = open(out_filepath, "r")
			encrypted = f.read(os.stat(out_filepath).st_size)
			f.close()

			# Remove the temporary files.
			os.remove(in_filepath)
			os.remove(out_filepath)

			# Pack the encrypted data into a wrapper.
			wrapped = encrypted + "/END_MESSAGE"

			# Send the encrypted message.
			self.sock.sendall(wrapped)

		# Update the GUI.
		if not self.gui == None:
			self.gui.updateChatLog()

	# Verify identity of receiver.
	# From perspective of chat session initiator.
	def activeAuthenticate(self):
		# Grab key for receiver username and compare it against what the receiver gave us.
		key = self.peer.getUserKeyFor(self.receiver_username)

		# Friend was added but never authenticated:
		if key == None:
			my_congruent_state = "True"
		else:
			my_congruent_state = str(self.receiver_user_key == key)

		# If key is empty or matches, proceed.
		if my_congruent_state == "True":
			self.sock.sendall("True")
			# Receive congruent state message from receiver.
			their_congruent_state = self.sock.recv(self.message_size)

			# If their state is congruent, proceed.
			if their_congruent_state == "True":
				# Compose verifier int V and send it.
				my_verifier = str(random.getrandbits(512))
				self.sock.sendall(my_verifier)

				# Receive initiator's verifier string
				their_verifier = self.sock.recv(self.message_size)

				# Sign and send
				my_signature = rsa.sign(their_verifier, self.peer.getPrivateKey(), 'SHA-1')
				self.sock.sendall(my_signature) 

				# Receive initiator's signature
				their_signature = self.sock.recv(self.message_size)

				# Verify the signature and send the response.
				try:
					my_decision = rsa.verify(my_verifier, their_signature, self.receiver_user_key)
					self.sock.sendall(str(my_decision))
				except rsa.VerificationError:
					self.sock.sendall("False")
					self.peer.endChat(self.receiver_username)
					return False

				# Receive initiator's authorization status.
				their_decision = self.sock.recv(self.message_size)
				if not their_decision == "True":
					self.peer.endChat(self.receiver_username)
					return False
				else:
					return True
			# Their state was incongruent, session should end.
			else:
				if not self.gui == None:
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
		ip = str(socket.gethostbyname(socket.getfqdn()))

		# Pack into protocol and send.
		# UDP port is static for now, but may later allow it to be changed, so we exchange ports for now.
		encoded = username + "," + str(pub_key.n) + "," + str(pub_key.e) + "," + ip + "," + str(self.udp_port)
		self.sock.sendall(encoded)

		# Receive (initiator username, initiator public key)
		decoded = self.sock.recv(self.message_size).split(",")
		
		# Decode and assign.
		self.receiver_username = decoded[0]
		self.receiver_user_key = rsa.PublicKey(long(decoded[1]), long(decoded[2]))
		self.receiver_ip = decoded[3]
		self.receiver_udp_port = decoded[4]

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
		decoded = self.sock.recv(self.message_size).split(",")

		# Decode and assign
		receiver_n = long(decoded[0])
		receiver_e = long(decoded[1])
		self.receiver_public_session_key = rsa.PublicKey(receiver_n, receiver_e)

	# Exchange usernames and public user keys with receiver, then authenticate.
	# From perspective of chat session reciprocator.
	# Returns whether or not authentication
	def passiveAuthenticate(self):
		# Receive congruent state message from receiver.
		their_congruent_state = self.sock.recv(self.message_size)
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
				their_verifier = self.sock.recv(self.message_size)

				# Compose verifier int V and send it.
				my_verifier = str(random.getrandbits(512))
				self.sock.sendall(my_verifier)

				# Receive initiator's signature
				their_signature = self.sock.recv(self.message_size)

				# Sign and send
				my_signature = rsa.sign(their_verifier, self.peer.getPrivateKey(), 'SHA-1')
				self.sock.sendall(my_signature) 

				# Receive initiator's authorization status.
				their_decision = self.sock.recv(self.message_size)
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
			if not self.gui == None:
				self.gui.showMessage("Authentication failure: your credentials were rejected.")
			self.peer.endChat(self.receiver_username)
			return False

	# Exchange usernames and public user keys.
	# From perspective of chat session reciprocator.
	def passiveHandshake(self):
		# Receive (initiator username, initiator public key)
		decoded = self.sock.recv(self.message_size).split(",")
		
		# Decode and assign.
		self.receiver_username = decoded[0]
		self.receiver_user_key = rsa.PublicKey(long(decoded[1]), long(decoded[2]))
		self.receiver_ip = decoded[3]
		self.receiver_udp_port = decoded[4]
 
		username = self.peer.getUsername()
		pub_key = self.peer.getPublicKey()
		ip = str(socket.gethostbyname(socket.getfqdn()))
		
		# Pack into protocol and send.
		# UDP port is static for now, but may later allow it to be changed, so we exchange ports for now.
		encoded = username + "," + str(pub_key.n) + "," + str(pub_key.e) + "," + ip + "," + str(self.udp_port)
		self.sock.sendall(encoded)

	# Generate and exchange public session keys with the receiver.
	# From perspective of chat session reciprocator.
	def passiveSessionKeyExchange(self):
		# Receive (n, e) from receiver.
		decoded = self.sock.recv(self.message_size).split(",")

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

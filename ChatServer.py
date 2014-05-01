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

	This is the server part of our chat system. Description to follow.
"""

import socket

class ChatServer:

	def __init__(self, port=50007):
		HOST = ''                 # Symbolic name meaning all available interfaces
		PORT = port              # Arbitrary non-privileged port
		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.s.bind((HOST, PORT))
		print "Server initialized. Port: " + str(PORT)

		# We need our server socket to not block. We want to send messages as well.
		# I'm thinking multiple threads/processes will facilitate this.
		#self.s.setblocking(0)
	
	# Run the server and accept connections as they come.
	def run(self):		
		print "Listening..."
		self.s.listen(1)
		conn, addr = self.s.accept()
		print 'Connection made with: ', addr
		while 1:
			data = conn.recv(1024)
			if not data: break
			# Echo data
			conn.sendall(data)
		conn.close()
		print "Connection closed."


if __name__ == '__main__':
	server = ChatServer()
	server.run()
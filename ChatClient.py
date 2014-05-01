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

	This is the client part of our chat system. Description to follow.
"""


# Echo client program
import socket
import getpass
import ChatServer as serv

if __name__ == '__main__':
	print "Welcome to XChat! Please login."
	username = raw_input("username: ")
	password = getpass.getpass("password: ")

	# Authenticate password here!
	# TODO: This authentication is obviously fake. We need the real deal.
	realpass = "1234"
	while not password == realpass:
		print "Sorry, that login info didn't match. Try again."
		username = raw_input("username: ")
		password = getpass.getpass("password: ")

	# TODO: Set up chat server. We need to be expecting connections
	#       before they come in. Possibly a master thread that sits
	#       and waits for connections.
	#server = serv.ChatServer();
	#server.run()

	print "Welcome, " + username + "! Who do you want to talk to?"
	HOST = raw_input("IP address: ")
	PORT = int(raw_input("Port #: ")) 
	print "Connecting you to " + HOST + ":" + str(PORT) + "..."

	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	
	try:
		s.connect((HOST, PORT))
		print "Write a message to your friend."
		s.sendall(raw_input("> "))
		data = s.recv(1024)
		s.close()
		print 'Received', repr(data)
		print "Connection closed.\n"

	except:
		print "Something went wrong, connection failed. Was that address right?"


	


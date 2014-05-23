"""
	CSCI 334: Distributed Systems
	Williams College
	Spring 2014

	Final Project: BLiP: Peer-to-Peer Chat
	Authors: 
		Jeremy Boissevain
		Nile Livingston
		Nehemiah Paramore

	This class contains the GUI for the BLiP login window.
"""

from Tkinter import *

class LoginGUI():

	def __init__(self, peer):
		# The Peer associated with this 
		self.peer = peer

		# The login window.
		self.root= Tk()
		self.root.wm_title("BLiP Login")

		# The instructional label.
		Label(self.root, text="Please enter your user information.").pack(side=TOP)
		
		# The username entry frame.
		username_frame = Frame(self.root)
		username_frame.pack()
		Label(username_frame, text="Username: ").pack(side=LEFT)
		self.username_entry = Entry(username_frame)
		self.username_entry.pack(side=RIGHT)

		# The login button.
		self.login_button = Button(self.root, text="Login", command=self.login)
		self.login_button.pack()

	# Ask the peer to log the user in.
	def login(self):
		username = self.username_entry.get()

		self.peer.login(username)
		self.destroy()
		
	# Run the GUI loop.
	def run(self):
		self.root.mainloop()

	# Destroy this window.
	def destroy(self):
		self.root.destroy()
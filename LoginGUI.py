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

	def __init__(self, parent):
		self.parent = parent

		self.root= Tk()
		self.root.wm_title("BLiP Login")

		Label(self.root, text="Please enter your user information.").pack(side=TOP)
		
		username_frame = Frame(self.root)
		username_frame.pack()
		Label(username_frame, text="Username: ").pack(side=LEFT)
		self.username_entry = Entry(username_frame)
		self.username_entry.pack(side=RIGHT)

		password_frame = Frame(self.root)
		password_frame.pack()
		Label(password_frame, text="Password: ").pack(side=LEFT)
		self.password_entry = Entry(password_frame, show="*")
		self.password_entry.pack(side=RIGHT)

		self.login_button = Button(self.root, text="Login", command=self.authenticate)
		self.login_button.pack()

		self.login_message = StringVar()
		Label(self.root,textvariable=self.login_message).pack()

	def authenticate(self):
		username = self.username_entry.get()
		password = self.password_entry.get()

		# Replace with actual authentication
		login_success = True

		if login_success:	
			self.parent.login(username, password)
			self.destroy()
		else:
			self.login_message.set("Login failed: user information incorrect.")
		
	def run(self):
		self.root.mainloop()
		#return

	def destroy(self):
		self.root.destroy()
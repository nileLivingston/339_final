"""
	CSCI 334: Distributed Systems
	Williams College
	Spring 2014

	Final Project: BLiP: Peer-to-Peer Chat
	Authors: 
		Jeremy Boissevain
		Nile Livingston
		Nehemiah Paramore

	This class contains the GUI for the main BLiP program.
"""

from Tkinter import *
import tkMessageBox

class BLiPGUI():

	# Constructs all of the components and packs them.
	def __init__(self, peer):

		# The peer associated with this GUI.
		self.peer = peer

		############################################################################
		#	GUI INITIALIZATION/FRAMING
		############################################################################
		# Main window.
		self.root = Tk()
		self.root.wm_title("BLiP Chat")
		
		
		# The left frame, which contains the active chat list, the friends list, and
		# accompanying buttons/entries.
		left_frame = Frame(self.root)
		left_frame.pack(side=LEFT)

		# chats_frame includes: a label, the list of active chats, and the "Leave Chat" button.
		chats_frame = Frame(left_frame)
		chats_frame.pack(side=TOP)

		Label(chats_frame, text="Active Chats:").pack(side=TOP)
		self.active_chats = Listbox(chats_frame, relief="sunken")
		self.active_chats.bind('<<ListboxSelect>>', self.chatSelect)
		self.updateChatSessions() # TEST!
		self.active_chats.pack()
		self.leavechat_button = Button(chats_frame, text="Leave Chat", command=self.leaveChat)
		self.leavechat_button.pack(side=BOTTOM)

		# friends_frame includes: a label, the friends list, and the "Chat" button.
		friends_frame = Frame(left_frame)
		friends_frame.pack()

		Label(friends_frame, text="Friends:").pack(side=TOP)
		self.friends = Listbox(friends_frame, relief="sunken")
		self.updateFriends()
		self.friends.pack()
		self.chat_button = Button(friends_frame, text="Chat", command=self.startChat)
		self.chat_button.pack(side=BOTTOM)

		# contains: add/remove friend entry box, "Add friend" and "Remove friend" buttons
		friend_manipulation_frame = Frame(left_frame)
		friend_manipulation_frame.pack()

		self.friend_entry = Entry(friend_manipulation_frame)
		self.friend_entry.pack(side=TOP)

		friend_buttons_frame = Frame(friend_manipulation_frame)
		friend_buttons_frame.pack(side=BOTTOM)

		self.addfriend_button = Button(friend_buttons_frame, text="Add Friend", command=self.addFriend)
		self.addfriend_button.pack(side=LEFT)
		self.removefriend_button = Button(friend_buttons_frame, text="Remove Friend", command=self.removeFriend)
		self.removefriend_button.pack(side=RIGHT)

		self.logout_button = Button(left_frame, text="Logout", command=self.exit)
		self.logout_button.pack(side=BOTTOM)

		# The right frame, which contains the chat log and the entry box.
		right_frame = Frame(self.root, width=600, height=100)
		right_frame.pack(side=RIGHT)

		# The chat log.
		self.chat_log = Text(right_frame, width=100, bd=2, relief="sunken")
		self.chat_log.insert(INSERT, "Welcome to BLiP!\n")
		self.chat_log.pack(side=TOP)
		self.chat_log.config(state=DISABLED)

		# The message entry box.
		entry_frame = Frame(right_frame, bd=2, width=100)
		entry_frame.pack(side = BOTTOM)
		Label(entry_frame, text="Message:", bd=2).pack(side = LEFT)
		self.E1 = Entry(entry_frame, bd=2, width=50)
		self.E1.bind('<Return>', self.submitMessage)
		self.E1.pack(side = RIGHT)

	
		############################################################################

		# The username of the receiver we're actively chatting with.
		self.active_chat_session = None
	

	#########################################
	#	MUTATOR METHODS
	#########################################

	# Add a friend to the friends list.
	def addFriend(self):
		# Have peer add the username in the entry box.
		username = self.friend_entry.get()
		if username == "": return
		self.peer.addFriend(username)

		# Clear the friend entry box.
		self.friend_entry.delete(0, END)

	# Propogate updates  (e.g., chat log) when
	# selection of the chats menu changes.
	def chatSelect(self, event):
		if self.active_chats.size() == 0:
			self.active_chat_session = None
		if not self.active_chats.curselection() == ():
			self.active_chat_session = self.active_chats.get(self.active_chats.curselection())	
		self.updateChatLog()

	# Tell the peer to end an active chat session.
	def leaveChat(self):
		self.peer.endChat(self.active_chat_session, "ACTIVE")
		self.chatSelect(None)

	# Remove a friend from the friends list.
	def removeFriend(self):
		# Have peer remove the username in the entry box.
		username = self.friend_entry.get()
		if username == "": return
		self.peer.removeFriend(username)

		# Clear the friend entry box.
		self.friend_entry.delete(0, END)

	# Initiate a chat with the selected friend.
	def startChat(self):
		if not self.friends.curselection() == ():
			username = self.friends.get(self.friends.curselection())
			if username == None:
				return
			self.peer.initiateChat(username)

	# Send a message to the active chat receiver and
	# update the chat log.
	def submitMessage(self, event):
		message = event.widget.get()
		receiver = self.active_chat_session

		# Let the peer sent the message.
		self.peer.sendMessage(receiver, message)

		# Update the chat log.
		self.updateChatLog()

		# Clear the entry box.
		self.E1.delete(0, END)
		
	#########################################
	#	UPDATE METHODS
	#########################################

	# Update the friends list.
	def updateFriends(self):
		self.friends.delete(0, END)

		friends = self.peer.getFriends()
		index = 0
		for friend in friends:
			self.friends.insert(index, friend)
			index += 1

	# Update the list of active chat sessions.
	def updateChatSessions(self):
		self.active_chats.delete(0, END)
		
		index = 0
		for chat in self.peer.getActiveChats():
			self.active_chats.insert(index, chat.getReceiver())
			index += 1

		self.active_chat_session = self.active_chats.get(0)

	# Update the chat log.
	def updateChatLog(self):
		# Make the log editable.
		self.chat_log.config(state=NORMAL)

		# Clear the log.
		self.chat_log.delete(0.0, END)

		# Only update if there is an active chat. Leave empty otherwise.
		if not (self.active_chat_session == None or self.active_chat_session == ""):
			# Get the chat log from the chat thread and update the text log.
			chat_session = self.peer.getChatSession(self.active_chat_session)
			if not chat_session == None:
				log = chat_session.getLog()
				
				for line in log:
					self.chat_log.insert(INSERT, line + "\n")
				self.chat_log.see(END)

		# Make the log uneditable.
		self.chat_log.config(state=DISABLED)

	#########################################
	#	MESSAGE METHODS
	#########################################

	# Displays a pop-up message.
	def showMessage(self, text):
		tkMessageBox.showinfo("BLiP Warning", text)

	#########################################
	#	START/STOP METHODS
	#########################################

	# Run the GUI loop.
	def start(self):
		self.root.mainloop()

	# Exit the GUI loop.
	# TODO: Working?
	def exit(self):
		self.root.destroy()
		self.peer.logout()
	


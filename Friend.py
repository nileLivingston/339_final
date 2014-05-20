"""
	CSCI 334: Distributed Systems
	Williams College
	Spring 2014

	Final Project: BLiP: Peer-to-Peer Chat
	Authors: 
		Jeremy Boissevain
		Nile Livingston
		Nehemiah Paramore
       
        I'm considering adding a friends class so that we can manage more
        information with the friends.
        Each friend would have both keys, an ip_address, and the list 
        close ip addressess. 
        In this way, the friends file can be converted to a json file, so        loading and decoding is much simpler.
"""


import rsa

class Friend():
        def __init__(self, username=None, key_e = None, key_n = None):
            # both parts of stored key
            self.username = username
            self.key_e = key_e
            self.key_n = key_n
            self.IPAddress = None
            self.udp # udp port

        def getRSAKey(self):
            return rsa.PublicKey(self.key_n, self.key_e)
        
        def getAddress(self):
            # tuple format that entangled uses to join networks
            return (self.IPAdress, self.upd)

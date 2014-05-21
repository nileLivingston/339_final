"""
	CSCI 334: Distributed Systems
	Williams College
	Spring 2014

	Final Project: BLiP: Peer-to-Peer Chat
	Authors: 
		Jeremy Boissevain
		Nile Livingston
		Nehemiah Paramore

        This is a very simple thread wrapper for the entangled node. 

"""

import threading
import entangled.node

class NodeThread(threading.Thread):
    """
    @param : username - Username of caller [string]
    @param : IPAddress - address of caller ('ipaddress', port)
    """
    def __init__(self):
        super(NodeThread, self).__init__()

        self.node = None

    def run(self):
        #Create the node
        self.node = entangled.node.EntangledNode()

    #def exit(self):


    def publishData(self, username, address):
        self.node.publishData(username, address)

    def joinNetwork(ipList):
        self.node.joinNetwork(ipList)
    ####################################
    # Node Method Wrappers             #
    ####################################

    # I'm not going to define any methods just yet, simply call
    # all methods through NodeThread.node.(entangled node method)
    

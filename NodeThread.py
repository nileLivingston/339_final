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

class NodeThread(threading.Thread, username, IPAddress):
    """
    @param : username - Username of caller [string]
    @param : IPAddress - address of caller ('ipaddress', port)
    """
    def __init__(self):
        self.node = entangled.node.EntangledNode()
        # publish own connection info. not sure if this should 
        # happen later after attempting to join nodes or before. 
        self.node.publishData(self, username, IPAddress)
        
    ####################################
    # Node Method Wrappers             #
    ####################################
    
    # I'm not going to define any methods just yet, simply call
    # all methods through NodeThread.node.(entangled node method)
    

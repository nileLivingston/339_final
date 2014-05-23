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
import entangled.kademlia.node
import twisted

class NodeThread(threading.Thread):
    """
    @param : username - Username of caller [string]
    @param : IPAddress - address of caller ('ipaddress', port)
    """
    def __init__(self, udp_port):
        super(NodeThread, self).__init__()
        self.udp_port = udp_port
        self.node = None

    def run(self):
        #Create the node
        self.node = entangled.node.EntangledNode( udpPort = self.udp_port )

    def exit(self):
        self.node = None

    ####################################
    # Node Method Wrappers             #
    ####################################

    def publishData(self, username, address):
        return self.node.publishData(username, address)

    def joinNetwork(self, ipList):
        print ipList
        return self.node.joinNetwork(ipList)

    def findValue(self, key):
        return self.node.findValue(key)

    def searchForKeywords(self, keyword):
        return self.node.searchForKeywords(keyword)

    def printContacts(self):
        return self.node.printContacts()
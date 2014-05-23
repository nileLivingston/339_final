'''
	CSCI 334: Distributed Systems
	Williams College
	Spring 2014

	Final Project: BLiP: Peer-to-Peer Chat
	Authors: 
		Jeremy Boissevain
		Nile Livingston
		Nehemiah Paramore

	This program was used to investigate the average time needed for RSA key
	generation, encryption, and decryption using 512-bit keys.

'''

import rsa
import time

gen_times = []
encr_times = []
decr_times = []
# Each iteration is a trial.
for i in range (1, 101):
	print str(i) + "..."

	# Record key generation time.
	start_time = time.time()
	(pub, priv) = rsa.newkeys(512)
	gen_times.append(time.time() - start_time)

	# Record encryption time.
	start_time = time.time()
	encrypted = rsa.encrypt("xxxxxxxxxx", pub)
	encr_times.append(time.time() - start_time)

	# Record decryption time.
	start_time = time.time()
	rsa.decrypt(encrypted, priv)
	decr_times.append(time.time() - start_time)

# Print averages.
print "Generation:"
print reduce(lambda x, y: x + y, gen_times) / len(gen_times)
print "Encryption:"
print reduce(lambda x, y: x + y, encr_times) / len(encr_times)
print "Decryption:"
print reduce(lambda x, y: x + y, decr_times) / len(decr_times)
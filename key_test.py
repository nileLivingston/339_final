'''
	CSCI 334: Distributed Systems
	Williams College
	Spring 2014

	Final Project: BLiP: Peer-to-Peer Chat
	Authors: 
		Jeremy Boissevain
		Nile Livingston
		Nehemiah Paramore

	This program was used to investigate time needed for RSA key
	generation, encryption, and decryption for various key sizes.

'''

import time
import rsa
import os

sizes = []

# Key sizes from 200 to 2000 in 200-bit increments.
for i in range(200, 2001, 200):
 	sizes.append(i)

gen_times = []
encr_times =[]
decr_times = []

for size in sizes:
	print str(size) + "..."

	# Record key generation time.
	start_time = time.time()
	(pub,priv) = rsa.newkeys(size)
	gen_times.append(time.time() - start_time)

	# Record encryption time.
	start_time = time.time()
	encrypted = rsa.encrypt("xx", pub)
	encr_times.append(time.time() - start_time)

	# Record decryption time.
	start_time = time.time()
	rsa.decrypt(encrypted, priv)
	decr_times.append(time.time() - start_time)

# Write output to files.

f = open("gen_times", "w+")
for time in gen_times:
	f.write(str(time)+"\n")
f.close()

f = open("encr_times", "w+")
for time in encr_times:
	f.write(str(time)+"\n")
f.close()

f = open("decr_times", "w+")
for time in decr_times:
	f.write(str(time)+"\n")
f.close()
import rsa
import random

(pub, priv) = rsa.newkeys(512)
message = str(random.getrandbits(512))
print message
signature = rsa.sign(message, priv, 'SHA-1')
answer = rsa.verify(message, signature, pub)
if answer:
	print "Authenticated!"
else:
	print "Authentication failure."

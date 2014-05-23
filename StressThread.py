import threading
import Peer as p
import sys

class StressThread(threading.Thread):

	def __init__(self, receiver):
		# Required for threading purposes.
		super(StressThread, self).__init__()

		self.peer = p.Peer(False)
		self.receiver = receiver

	def run(self):
		p.stressRun(self.peer, self.receiver)

if __name__ == '__main__':
	threads = []
	for i in range(1, 51):
		new_thread = StressThread(sys.argv[2])
		threads.append(new_thread)
	for thread in threads:
		thread.start()
	

#!/usr/bin/python

# test program that is a dummy for proposed major-mode interface.
#
# program runs forever, or until it gets a SIGUSR1 signal,
# at which time it cleans up and exits.
#
import sys, time, signal

totally_done = False

def cleanup(signum, frame):
	global totally_done

	print "Cleaning up."
	totally_done = True

signal.signal(signal.SIGUSR1, cleanup)

while not totally_done:
	print sys.argv[1]
	time.sleep(1)

print "Done with the program"


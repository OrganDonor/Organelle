#!/usr/bin/env python
#
# Null GUI (Dark Screen) for Organ Donor Organelle
#
# 2015-11 ptw

from Tkinter import *

import sys
import signal

from os.path import isfile, join

root_bg = "black"

deployed_mode = isfile("deployed.txt")		# Create this file to go full-screen, etc.

root = Tk()
root.config(bg=root_bg)

# This program ends normally when we receive a SIGUSR1 signal from the supervisor.
def handle_sigusr1(signum, frame):
	root.quit()
signal.signal(signal.SIGUSR1, handle_sigusr1)

# There might be no events going through the event loop. That makes it unresponsive
# to things like SIGUSR1 signals. So generate some event chatter to break the impasse.
def kludge():
	root.after(100, kludge)
root.after(100, kludge)

if deployed_mode:
	root.attributes("-fullscreen", True)
else:
# for debug, use the same screen size as the real screen, in a handy screen position.
	root.geometry("800x480+50+50")

root.mainloop()
print("Here we are cleaning up.")

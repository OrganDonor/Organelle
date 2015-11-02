#!/usr/bin/python

import mido
import signal
import sys
import re

#get the MidiFile, MidiTrack, and Message commands working
from mido import MidiFile
from mido import Message

#for using the rtmidi port manager
import time
import rtmidi
from rtmidi.midiutil import open_midiport
from rtmidi.midiconstants import *

def initialize_MIDI_inout():
	"""Initialize a MIDI input and output port using RTMIDI through mido
	"""

	#select rtmidi as our backend
	mido.set_backend('mido.backends.rtmidi')
	#print "Backend selected is %s " % mido.backend

	# Enumerate the available port names
	outports = mido.get_output_names()
	inports = mido.get_input_names()

	# Now try to pick the right port to output on.
	# If we're in the deployed configuration, it's a MIO adapter, but
	# if we're in the lab, it might be something else.
	# In either event, there might be more than one matching adapter!
	# In that case, we'll punt and take the first one we find.
	outport = None
	for name in outports:
		if re.match(r'mio', name):
			try:
				outport = mido.open_output(name)
				break
			except:
				pass

	if not outport:
		for name in outports:
			try:
				outport = mido.open_output(name)
				break
			except:
				pass

	if not outport:
		print("Sorry, unable to open any MIDI output port.")
		sys.exit(1)
	
	# Now try to pick the right port to input on.
	# If we're in the deployed configuration, it's a MIO adapter, but
	# if we're in the lab, it might be something else.
	# In either event, there might be more than one matching adapter!
	# In that case, we'll punt and take the first one we find.
	inport = None
	for name in inports:
		if re.match(r'mio', name):
			try:
				inport = mido.open_input(name)
				break
			except:
				pass

	if not inport:
		for name in inports:
			try:
				inport = mido.open_input(name)
				break
			except:
				pass

	if not inport:
		print("Sorry, unable to open any MIDI input port.")
		sys.exit(1)

	return (inport, outport)


inport,_ = initialize_MIDI_inout()

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#   Set up for interruption by the supervisor program
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
totally_done = False

def cleanup(signum, frame):
	global totally_done
	
	#print "Cleaning up!"
	out.reset()
	everything_off()
	totally_done = True

signal.signal(signal.SIGUSR1, cleanup)


def handle_note(rank, num):
	print "%d' rank, note=%d" % (rank, num)

def handle_cursor(dir):
	print dir


pitch = 0

while not totally_done:
	for message in inport.iter_pending():
		if "note_on" in message.type:
			if 0 == message.channel:
				handle_note(4, message.note-35)
			elif 1 == message.channel:
				handle_note(8, message.note-35)
			else:
				print "Unknown channel", message.channel
		elif "pitchwheel" in message.type:
			if pitch == 0 and message.pitch != 0:
				if message.pitch < 0:
					handle_cursor("-")
				elif message.pitch > 0:
					handle_cursor("+")
			pitch = message.pitch

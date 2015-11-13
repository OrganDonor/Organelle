#!/usr/bin/env python
#
# GUI Keyboards Visualization for Organ Donor Organelle
#
# 2015-11 ptw

from Tkinter import *
import tkFont

import random
import sys
import signal
import re
import time
import itertools

import os
from os import listdir
from os.path import isfile, join

import mido
from mido import MidiFile, MetaMessage
import rtmidi

root_bg = "#bbb"

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


inport,outport = initialize_MIDI_inout()


root = Tk()
root.config(bg=root_bg)

# This program ends normally when we receive a SIGUSR1 signal from the supervisor.
def handle_sigusr1(signum, frame):
	root.quit()
signal.signal(signal.SIGUSR1, handle_sigusr1)

pitch = 0
autorepeat = None
autorepeat_interval = 200
def poll_midi():
	"""Poll the MIDI input port.
	
	Polling might seem ugly here, but it is apparently the only way that works.
	Mido can provide a callback when each message comes in, but that callback runs
	on another thread, and Tkinter prohibits doing much of anything on another thread.
	The other thread could enqueue a message to the main thread, but then apparently
	the recommended way to check such a queue would be ... polling. If there were a
	thread-safe way to put an event into Tkinter's main event queue, we could avoid
	polling, but there apparently isn't.
	"""	
	for message in inport.iter_pending():
		if "note_on" in message.type and message.velocity > 0:
			if 0 == message.channel:
				handle_note_on((4, message.note-35))
			elif 1 == message.channel:
				handle_note_on((8, message.note-35))
			else:
				print "Unknown channel", message.channel
		if "note_off" in message.type or ("note_on" in message.type and message.velocity==0):
			if 0 == message.channel:
				handle_note_off((4, message.note-35))
			elif 1 == message.channel:
				handle_note_off((8, message.note-35))
			else:
				print "Unknown channel", message.channel

	root.after(50, poll_midi)

def do_quit():
	"""Exit the program.
	"""
	root.quit()
	
def configure_console(flagMidi=1, flagKBecho=1, flagGhostBuster=1):
	"""Send a SysEx to the console to set the configuration flags.
	Definitions copied from the Arduino code:
// SysEx format:
//  Byte#   Value     Meaning
//    0       F0      Start of SysEx command, defined by MIDI standard
//    1       7D      Manufacturer code reserved for "educational use"
//    2       55      my command code for setting the flags
//    3     0,1,2     flagMidi
//    4    0 or 1     flagKBecho
//	  5    0 or 1     flagGhostBuster
//    etc. for more flags
//    N       F7      End of SysEx command, defined by MIDI standard
	"""
	outport.send(mido.Message('sysex', data=[0x7d, 0x55, flagMidi, flagKBecho, flagGhostBuster]))

def handle_note_on(note_heard):
	"""Handle a note received over the MIDI interface.
	"""
	rank,pitch = note_heard
	if rank == 4:
		kb4.note_on(pitch)
	elif rank == 8:
		kb8.note_on(pitch)
	else:
		print "Unknown rank"

def handle_note_off(note_heard):
	"""Handle a note_off received over the MIDI interface.
	"""
	rank,pitch = note_heard
	if rank == 4:
		kb4.note_off(pitch)
	elif rank == 8:
		kb8.note_off(pitch)
	else:
		print "Unknown rank"

def white_and_black_for_total_keys(total):
	"""Return the number of white and black keys in a keyboard of so many keys.
	Assumes the keyboard starts on a C.
	"""
	whole_octaves = int(total/12)
	white = 7 * whole_octaves
	black = 5 * whole_octaves
	extra = total - (white + black)
	for i in range(1,extra+1):
		if iswhite(i):
			white += 1
		else:
			black += 1
	return (white,black)

def iswhite(key_number):
	"""Return True if the 1-based key number is a white key, False if it's black.
	Assumes the keyboard starts on a C.
	"""
	octave = (True, False, True, False, True, True, False, True, False, True, False, True)
	return octave[(key_number-1) % 12]

def key_position_offset(key_number):
	"""Return the relative position of the left edge of this key. 1-based key numbers.
	If it's a white key, return 0.0
	If it's a black key, the fraction of a white key width where the left edge falls.
	"""
	octave = (0.0, 0.56, 0.0, 0.75, 0.0, 0.0, 0.50, 0.0, 0.62, 0.0, 0.79, 0.0)
	return octave[(key_number-1) % 12]

class WhiteKey():
	"""On-screen widget displaying a white key on the keyboard.	
	"""
	def __init__(self, parent, key_number, offset, keyspacing, keyheight):
		"""Initializer for white keys.
					
		Arguments:
		parent -- the parent widget, typically a KeyboardDisplay
		key_number -- the key number (1-based) within the KeyboardDisplay
		offset -- the offset in pixels of the left edge of this key from the left edge of parent
		keyspacing -- number of pixels used by each white key
		keyheight -- number of pixels high for a white key
		"""
		self.key_number = key_number
		self.parent = parent
		self.rect = parent.create_rectangle(offset, 0, offset+keyspacing, keyheight-1, fill='white', outline='black', tags='white')

	def note_on(self):
		"""Visually highlight a key as being currently played."""
		self.parent.itemconfig(self.rect, fill='red')
		
	def note_off(self):
		"""Remove visual highlighting from a key."""
		self.parent.itemconfig(self.rect, fill='white')
		
class BlackKey():
	"""On-screen widget displaying a black key on the keyboard.
	"""
	def __init__(self, parent, key_number, offset, keyspacing, keyheight):
		self.key_number = key_number
		self.parent = parent
		actual_offset = offset + key_position_offset(key_number)*keyspacing - keyspacing
		black_key_width = int(0.57*keyspacing)
		black_key_height = int(0.5*keyheight)
		self.rect = parent.create_rectangle(actual_offset, 0, actual_offset+black_key_width, black_key_height-1, fill='black', outline='black', tags='black')
	
	def note_on(self):
		"""Visually highlight a key as being currently played."""
		self.parent.itemconfig(self.rect, fill='red')
		
	def note_off(self):
		"""Remove visual highlighting from a key."""
		self.parent.itemconfig(self.rect, fill='black')
	
class KeyboardDisplay(Canvas):
	"""Display-only keyboard widget.
	"""
	def __init__(self, *args, **kwargs):
		numkeys = kwargs.pop('keys', 61)
		Canvas.__init__(self, *args, **kwargs)
		self.config(bg='red', bd=0, highlightthickness=0)
		height=self.winfo_reqheight()
		white_count, black_count = white_and_black_for_total_keys(numkeys)
		white_key_spacing = int((self.winfo_reqwidth()-1)/ white_count)
		total_width = white_key_spacing * white_count + 1
		self.config(width=total_width)
		self.keys = [None]	# dummy value for keys[0] to make 1-based addressing work
		offset = 0
		for key in range(1, numkeys+1):
			if iswhite(key):
				self.keys.append(WhiteKey(parent=self, key_number=key, offset=offset, keyspacing=white_key_spacing, keyheight=height))
				offset += white_key_spacing
			else:
				self.keys.append(BlackKey(parent=self, key_number=key, offset=offset, keyspacing=white_key_spacing, keyheight=height))
		self.tag_raise('black')
		
	def note_on(self, pitch):
		self.keys[pitch].note_on()
	
	def note_off(self, pitch):
		self.keys[pitch].note_off()
		

button_quit = Button(root, text="Quit", command=do_quit)
kb4 = KeyboardDisplay(root, width=750, height=125, bg="#fff", bd=0)
button_dummy = Button(root, text="Dummy")
kb8 = KeyboardDisplay(root, width=750, height=125, bg="#eee", bd=0)

button_quit.pack()
kb4.pack()
button_dummy.pack()
kb8.pack()

poll_midi()					# kick off a frequent poll of the MIDI input port

# for debug, use the same screen size as the real screen, in a handy screen position.
#root.geometry("800x480+50+50")
# for real hardware, go full screen
root.attributes("-fullscreen", True)

"""
random_key = 0
def bang_on_keyboard():
	global random_key
	
	random_key = random.randint(1,61)
	print "playing", random_key
	button_dummy.config(state=NORMAL)
	kb4.note_on(random_key)
	root.after(1000, unbang)

def unbang():
	global random_key
	
	kb4.note_off(random_key)
	button_dummy.config(state=DISABLED)
	root.after(200, bang_on_keyboard)
	
bang_on_keyboard()
"""

root.mainloop()
print("Here we are cleaning up.")

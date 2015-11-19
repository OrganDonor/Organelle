#!/usr/bin/env python
#
# GUI Keyboard+Waterfall Visualization for Organ Donor Organelle
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

from sequence_recognizer import SequenceRecognizer

root_bg = "#bbb"

deployed_mode = isfile("deployed.txt")		# Create this file to go full-screen, etc.

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
		wf4.note_on(pitch)
	elif rank == 8:
		kb8.note_on(pitch)
		wf8.note_on(pitch)
	else:
		print "Unknown rank"

def handle_note_off(note_heard):
	"""Handle a note_off received over the MIDI interface.
	"""
	rank,pitch = note_heard
	if rank == 4:
		kb4.note_off(pitch)
		wf4.note_off(pitch)
	elif rank == 8:
		kb8.note_off(pitch)
		wf8.note_off(pitch)
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


class KeyboardDisplay(Canvas):
	"""Display-only keyboard widget.
	"""
	def __init__(self, *args, **kwargs):
		numkeys = kwargs.pop('keys', 61)
		Canvas.__init__(self, *args, **kwargs)
		self.config(bg='red', bd=0, highlightthickness=0)
		self.height=self.winfo_reqheight()
		white_count, black_count = white_and_black_for_total_keys(numkeys)
		self.key_spacing = int((self.winfo_reqwidth()-1)/ white_count)
		total_width = self.key_spacing * white_count + 1
		self.config(width=total_width)
		self.keyrects = [None]	# dummy value for keys[0] to make 1-based addressing work
		offset = 0
		for key in range(1, numkeys+1):
			if iswhite(key):
				self.keyrects.append(self.__create_white_keyrect(key_number=key, offset=offset))
				offset += self.key_spacing
			else:
				self.keyrects.append(self.__create_black_keyrect(key_number=key, offset=offset))
		self.tag_raise('black')
				
	def __create_white_keyrect(self, key_number, offset):
		return self.create_rectangle(offset, 0, offset+self.key_spacing, self.height-1, fill='white', outline='black', tags='white')
		
	def __create_black_keyrect(self, key_number, offset):
		actual_offset = offset + key_position_offset(key_number)*self.key_spacing - self.key_spacing
		key_width = int(0.57 * self.key_spacing)
		key_height = int(0.62 * self.height)
		return self.create_rectangle(actual_offset, 0, actual_offset+key_width, key_height-1, fill='black', outline='black', tags='black')
		
	def note_on(self, pitch):
		self.itemconfig(self.keyrects[pitch], fill='red')
	
	def note_off(self, pitch):
		if iswhite(pitch):
			self.itemconfig(self.keyrects[pitch], fill='white')
		else:
			self.itemconfig(self.keyrects[pitch], fill='black')


lt = "#f00"
dk = "#c00"
waterfall_offsets = (1, 13, 24, 36, 47, 59, 71, 82, 94, 105, 117, 128) # + 140*octaves
waterfall_widths = (11, 10, 11, 10, 11, 11, 10, 11, 10,  11,  10,  11)
waterfall_colors = (lt, dk, lt, dk, lt, lt, dk, lt, dk,  lt,  dk,  lt)

class WaterfallDisplay(Canvas):
	"""Waterfall-style display for played notes.
	
	When a note starts, we create a rectangle for it that's almost completely outside
	the window. Then, as time passes, all the partially-exposed rectangles move together,
	so that more and more of the rectangle is exposed. Once the complete rectangle is
	fully on-screen, it stops moving. Meanwhile, if a note ends, the part of it that is
	still off-screen is trimmed off, and, if stopped, it resumes moving. It will
	eventually scroll off entirely, at which time it is destroyed.
	
	There can be many rectangles in flight for each note on the keyboard. They all go
	independently.
	
	The status of each rectangle is kept track of using tags. Each rectangle that is to
	be moved is tagged "moving". Each rectangle that has been trimmed is tagged
	"complete". In addition to the tags, there is an array of items for each note
	containing the current item (between the note_on and the note_off for that note)
	or None the rest of the time.
	"""
	def __init__(self, *args, **kwargs):
		Canvas.__init__(self, *args, **kwargs)
		self.config(width=721, bg=root_bg, bd=0, highlightthickness=0)
		self.height=self.winfo_reqheight()
		self.key_spacing = 20
		self.note_items = [None] * 62
		self.vstep = 1		# pixel per animation cycle
		self.tstep = 30		# milliseconds per animation cycle
		
		self._animate()
		
	def note_on(self, pitch):
		# create a rectangle as high as the waterfall,
		# but positioned to show just one pixel on screen.
		if self.note_items[pitch] is not None:
			return			# should not usually happen: two note_on in a row
		
		note_offset = waterfall_offsets[(pitch-1) % 12] + 140 * int((pitch-1)/12)
		note_width = waterfall_widths[(pitch-1) % 12]
		note_color = waterfall_colors[(pitch-1) % 12]
		self.note_items[pitch] = self.create_rectangle(note_offset, 1 - self.height, note_offset+note_width, 1, fill=note_color, outline="", tags='moving')
	
	def note_off(self, pitch):
		# if we are currently drawing a rectangle for this note, trim it off
		# and let it scroll out of the waterfall.
		item = self.note_items[pitch]
		if item is not None:
			x1,y1,x2,y2 = self.coords(item)
			fill = self.itemcget(item, 'fill')
			self.delete(item)
			self.note_items[pitch] = None
			self.create_rectangle(x1, 1, x2, y2, fill=fill, outline="", tags=('moving', 'complete'))

	def _animate(self):
		for item in self.find_withtag('moving'):
			self.move(item, 0, self.vstep)
			x1,y1,x2,y2 = self.coords(item)
			if (y1 >= self.height):
				self.delete(item)
			elif (y1 == 1):
				self.itemconfig(item, tags="")		# remove the 'moving' tag
		self.after(self.tstep, self._animate)		# reschedule the animation
		

spacer = Canvas(root, height=10, bd=0, bg=root_bg, highlightthickness=0)
kb4 = KeyboardDisplay(root, width=750, height=80, bd=0)
wf4 = WaterfallDisplay(root, width=720, height=160, bd=0)
kb8 = KeyboardDisplay(root, width=750, height=80, bd=0)
wf8 = WaterfallDisplay(root, width=720, height=160, bd=0)

spacer.pack()
kb4.pack(expand=1)
wf4.pack(expand=1)
kb8.pack(expand=1)
wf8.pack(expand=1)

poll_midi()					# kick off a frequent poll of the MIDI input port

configure_console(flagKBecho=1)			# Make sure console is relaying keyboard input

if deployed_mode:
	root.attributes("-fullscreen", True)
else:
# for debug, use the same screen size as the real screen, in a handy screen position.
	root.geometry("800x480+50+50")


root.mainloop()
print("Here we are cleaning up.")

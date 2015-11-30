#!/usr/bin/env python
#
# GUI External MIDI Passthrough for Organ Donor Organelle
#
# 2015-11 ptw

from Tkinter import *
import tkFont

import sys
import signal
import re
import time
import itertools

from os.path import isfile

import mido
import rtmidi

root_bg = "#bbb"

deployed_mode = isfile("deployed.txt")		# Create this file to go full-screen, etc.

def initialize_MIDI_inout():
	"""Initialize MIDI input and output ports using RTMIDI through mido
	
	We will go ahead and initialize all four of the input ports from the MIDIPLUS
	interface, plus the output port to the console.
	"""

	#select rtmidi as our backend
	mido.set_backend('mido.backends.rtmidi')
	#print "Backend selected is %s " % mido.backend

	# Enumerate the available port names
	outports = mido.get_output_names()

	# Now try to pick the right port to output on.
	# If we're in the deployed configuration, it's a MIO adapter.
	outport = None
	for name in outports:
		if re.match(r'mio', name):
			try:
				outport = mido.open_output(name)
				break
			except:
				pass
				
	if not outport:
		print("Unable to open the MIO MIDI output port.")
		sys.exit(1)
	
	# Now locate the ports of the MIDIPLUS interface and open them for input.
	port_prefix = 'MIDI4x4.*:'
	inports = []
	for port in ('0', '1', '2', '3'):
		inports.append(open_midi_input_port(port_prefix + port))
	
	if len(inports) != 4:
		print("Unable to open MIDI input ports. Is the MIDIPLUS connected?")
		sys.exit(1)

	return (inports, outport)

def open_midi_input_port(regex):
	"""Open a MIDI input port matching a given regular expression, and return it.
	"""
	inports = mido.get_input_names()
	for name in inports:
		if re.match(regex, name):
			try:
				p = mido.open_input(name)
			except:
				pass
			else:
				return p


inports,outport = initialize_MIDI_inout()

root = Tk()
root.config(bg=root_bg)

# This program ends normally when we receive a SIGUSR1 signal from the supervisor.
def handle_sigusr1(signum, frame):
	root.quit()
signal.signal(signal.SIGUSR1, handle_sigusr1)

def poll_midi():
	"""Poll the MIDI input ports.
	
	Polling might seem ugly here, but it is apparently the only way that works.
	Mido can provide a callback when each message comes in, but that callback runs
	on another thread, and Tkinter prohibits doing much of anything on another thread.
	The other thread could enqueue a message to the main thread, but then apparently
	the recommended way to check such a queue would be ... polling. If there were a
	thread-safe way to put an event into Tkinter's main event queue, we could avoid
	polling, but there apparently isn't.
	"""
	for passthru in passthrus:
		for message in passthru.port.iter_pending():
			passthru.handle_message(message)

	root.after(50, poll_midi)

def everything_off():
	"""Turn off every note, in case it's stuck playing.
	"""
	for mynote in range(1,128):
		outport.send(mido.Message('note_off', note=mynote, velocity=100))
	
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

enabledColor = 'green'
class MidiPortPassthru():
	"""Object to handle configuration and passthrough of MIDI notes from an input port.
	
	The object knows its port, and creates a GUI to set how messages from that port
	are to be passed through to the console. It then handles messages according to
	the user settings.
	"""
	def __init__(self, port):
		self.port = port
		self.enabled = IntVar()
		self.enabled.set(1)				# defaults to enabled
		self.gui = Frame(root, height=110, width=800, bg=root_bg, bd=2, relief=SUNKEN)
		port_name = "MIDI In " + chr(ord(port.name[-1])+1)
		self.portlabel = Label(self.gui, text=port_name+':', font=("Helvetica", 24), fg='black', bg=root_bg)
		self.portlabel.pack(side=LEFT)
		self.enabledButton = Checkbutton(self.gui, text="Enabled ", font=("Helvetica", 18), padx=0, pady=0, bg=enabledColor, activebackground=enabledColor, highlightbackground=enabledColor, variable=self.enabled, command=self._enabledCallback)
		self.enabledButton.pack(side=LEFT)
		#!!! construct rest of GUI here
	
	def _enabledCallback(self):
		if self.enabled.get() == 1:
			self.portlabel.config(fg='black')
			self.enabledButton.config(bg=enabledColor, activebackground=enabledColor, highlightbackground=enabledColor)
			#!!! enable secondary controls here
		else:
			self.portlabel.config(fg='gray')
			self.enabledButton.config(bg=root_bg, activebackground=root_bg, highlightbackground=root_bg)
			#!!! disable secondary controls here
			everything_off()		# just in case there are notes left playing
									# This disrupts the other channels, but to avoid that
									# we'd need to keep track of all the notes played. Ugh.
		pass
		
	def handle_message(self, msg):
		if self.enabled.get() == 1:
			#!!! lots more logic here
			outport.send(msg)
	

configure_console(flagMidi=2)			# Make sure console allows access to both ranks

Label(root, text="Play From MIDI Devices", font=("Helvetica", 36), fg='red', bg=root_bg, padx=4, pady=2).pack()


# Associate each input port with a MidiPortPassthru and put their GUIs on the screen.
passthrus = []
for port in inports:
	passthru = MidiPortPassthru(port)
	passthrus.append(passthru)
	passthru.gui.pack(fill=BOTH, expand=1)

poll_midi()					# kick off a frequent poll of the MIDI input port

if deployed_mode:
	root.attributes("-fullscreen", True)
else:
# for debug, use the same screen size as the real screen, in a handy screen position.
	root.geometry("800x480+50+50")

root.mainloop()
print("Here we are cleaning up.")

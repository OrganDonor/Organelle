#!/usr/bin/env python
#
# One of the functions of the Organ Donor Opus 1.2 Organelle,
# this program plays a number of randomly selected MIDI files.
# It can be interrupted cleanly by sending a SIGUSR1 signal,
# as required by the rotary switch supervisor.
#

SONGS_SUBDIRECTORY = "songs"


#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#   Imports
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

#import mido library
import mido
from mido import MidiFile

#import random
import random

#import sys for command line arguments
import sys

#import signal for interruptions from supervisor program
import signal

#import regular expression matching
import re

#import os
import os
from os import listdir
from os.path import isfile, join

#for using the rtmidi port manager
import rtmidi


#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#	Turn off everything now playing
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
def everything_off():
	for mynote in range(1,128):
		out.send(mido.Message('note_off', note=mynote, velocity=100))


#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# Select a random midi file 
# from the /songs directory
# and return a MIDO object from that file.
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
def select_random_song():

	songspath = join(os.getcwd(), SONGS_SUBDIRECTORY)
	onlyfiles = [ f for f in listdir(songspath) if isfile(join(songspath,f)) ]

	if len(onlyfiles) == 0:
		print "Oh no! We don't have any song files to choose from."
		sys.exit(1)

	mysong = onlyfiles[random.randint(0, len(onlyfiles)-1)]

	#create a midi object from the midi file
	mid = MidiFile(join(songspath, mysong))
	mid.organ_donor_title = mysong
	
	#return the midi object
	return mid


#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# Play a song from a MIDO object
#
# This function can take a very long time,
# so it has to check for the totally_done flag.
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

def play_song(mid):
	global totally_done

	for message in mid.play():
		if totally_done:
			clean_exit()
			
		# Disregard all other message types which may be cluttering up the file.
		if 'note_on' in message.type or 'note_off' in message.type:
			try:
				out.send(message)
			except:
				print "Oops. MIDI output failed. Jukebox cain't play no mo."
				sys.exit(1)


#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#   play n random midi files
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
def jukebox(n):
	global totally_done
	
	for x in xrange(1, n+1):
		if totally_done:
			clean_exit()

		mid = select_random_song()
		print "Selecting a random midi file ... %s" % mid.organ_donor_title
		
		print "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
		print "Song number %d (of %d) will play for %d seconds." % (x,n,int(mid.length))
		print "You can also play the organ using the keyboards!"
		print "Turn the rotary switch below to stop auto-play."
		print "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
	
		play_song(mid)
		
		print
		print "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
		print "Song number %d has ended." % x
		print "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
				
		everything_off()


#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# setup rtmidi as our backend
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

#select rtmidi as our backend
mido.set_backend('mido.backends.rtmidi')
#print "Backend selected is %s " % mido.backend

# Enumerate the available port names
outports = mido.get_output_names()

# Now try to pick the right port to output on.
# If we're in the deployed configuration, it's a MIO adapter, but
# if we're in the lab, it might be something else.
# In either event, there might be more than one matching adapter!
# In that case, we'll punt and take the first one we find.
out = None
for name in outports:
	if re.match(r'mio', name):
		try:
			out = mido.open_output(name)
			break
		except:
			pass

if not out:
	for name in outports:
		try:
			out = mido.open_output(name)
			break
		except:
			pass

if not out:
	print("Sorry, unable to open any MIDI output port.")
	sys.exit(1)

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#   Set up for interruption by the supervisor program
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
totally_done = False

def sig_handler(signum, frame):
	global totally_done
	totally_done = True

def clean_exit():
	print "Rotary switch turned, going on to the next thing."
	out.reset()
	everything_off()
	sys.exit(0)

signal.signal(signal.SIGUSR1, sig_handler)

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#   Process Command Line arguments
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

number_of_songs = 1
if len(sys.argv) > 1:
	number_of_songs = int(sys.argv[1])

print "Thank you for enjoying Organ Donor!"

if number_of_songs == 1:
	print("Playing a random song.")
elif number_of_songs > 1:
	print("\nPlaying %d random songs." % number_of_songs)

jukebox(number_of_songs)
# jukebox doesn't return unless interrupted until all the songs have been played.

print "You can play the keyboards now."
print "Reselect auto-play on the rotary switch to hear more."

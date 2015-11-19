#!/usr/bin/env python
#
# GUI Autoplay mode (Jukebox) for Organ Donor Organelle
#
# Tkinter GUI functions used to control MIDO MIDI interface library to play MIDI files
# from the filesystem and provide a fun, obvious user interface. This program runs under
# the GUI supervisor, so it expects to run forever until it receives a SIGUSR1, at which
# point it shuts down immediately and exits.
#
# 			Looks roughly like this:
# 
# 				Now Playing:                   3:56 of 9:21
# 				Title of Currently Playing Song
# 	
# 				^   Up Next:
# 				v   Title of candidate next song        *
#    				  |<     >       ||      >|
#
#
# 2015-10 ptw

from Tkinter import *
import tkFont

import random
import sys
import signal
import re
import time

import os
from os import listdir
from os.path import isfile, join

import mido
from mido import MidiFile, MetaMessage
import rtmidi

SONGS_SUBDIRECTORY = "songs"

deployed_mode = isfile("deployed.txt")		# Create this file to go full-screen, etc.

# Colors for the progress indicator
active_color = "#888"
inactive_color = "#ccc"
paused_color = "#aaa"

# colors for the three main frames of the UI
top_bg = "#eee"
mid_bg = "#8888ff"
bot_bg = "#b8b8b8"


def frac(x):
	"""Return the fractional part of a positive number.
	"""
	return x - int(x)


class TimeProgressLabel(Label):
	"""Text Label-based widget to display progress in the form "m:ss of m:ss"
	
	* Set it up with reset, passing in the total duration of the playback.
	* Update it incrementally with advance each time a known interval has passed.
	The first such update starts time running.
	Finalize it with done so the final time display exactly matches the duration.
	"""
	def __init__(self, parent, *args, **kwargs):
		Label.__init__(self, parent, *args, **kwargs)
		self.elapsed = 0
		self.displayed_seconds = 0
		self.duration = 0
		self.last_realignment = -1
		self.seconds_updater = None
		self._update_string(0.0)
		self.config(fg=inactive_color)
		
	def _update_string(self, t):
		self.config(text = "%d:%02d of %d:%02d" % (int(t/60),int(t%60),int(self.duration/60),int(self.duration%60)))
		print "displaying: %d:%02d of %d:%02d" % (int(t/60),int(t%60),int(self.duration/60),int(self.duration%60)), 
		
	def reset(self, seconds):
		"""Initialize the total duration and reset the elapsed time to zero.
		"""
		self.elapsed = 0
		self.duration = seconds
		if self.seconds_updater != None:
			self.after_cancel(self.seconds_updater)
			self.seconds_updater = None
		self._update_string(0.0)
		self.systime_offset = None
		self.config(fg=inactive_color)
		print "reset progress"
				
	def advance(self, midi_incremental_time):
		"""Advance the elapsed time by a specified amount.
		
		MIDI time is considered authoritative; we don't care about real time at all.
		So the cumulative sum of these advances is the definitive elapsed time for the song.
	
		This routine is responsible for scheduling the display update on integral seconds.
		We keep the timer updated with the latest idea of time from calls to advance().
		We also keep track of the offset between system time and MIDI time, so that the
		display updater can always compute the right time to display, even during long
		notes or rests.
		"""
		self.elapsed += midi_incremental_time
		self.systime_offset = time.time() - self.elapsed
		print "increment: ", midi_incremental_time, " elapsed: ", self.elapsed, "system offset: ", self.systime_offset
		
		# Update the timer to expire on the next second boundary.
		# There's a race here; the timer might be expiring right now.
		# That's OK because the timer handler is designed to display the right time
		# even if is called multiple times.
		# Is it possible for the handler to get called zero times? Maybe, depending on
		# the (undocumented) behavior of self.cancel_after(). If that does happen, the
		# handler would just update by 2 at the next second boundary, so at least the error
		# would be transient.
		if self.seconds_updater is not None:
			self.after_cancel(self.seconds_updater)
		self.seconds_updater = self.after(int(1000*(1.0-frac(self.elapsed))), self._next_second)
	
		self.config(fg=active_color)
		
	def	_next_second(self):
		"""Update the display once per second of elapsed (MIDI) time.
		
		We've tried to arrange for this event to fire very near the second boundary
		(in MIDI time) for every second boundary. Due to an unavoidable race condition,
		it might fire more than once for the same second boundary. Thus it is crucial
		that this function display the correct time without trying to count invocations.
		We do this by keeping track of the offset between system time and elapsed (MIDI)
		time. This function subtracts that offset from system time to get the time
		to display.
		
		This event reschedules itself for 1.0 seconds later, just in case there are
		no advance() events during the coming second. More often, there will be.
		"""	
		self.seconds_updater = self.after(1000, self._next_second)	# just in case
		if self.systime_offset is not None:
			self._update_string(round(time.time() - self.systime_offset))
		
	def pause(self):
		"""Pause timekeeping without disrupting elapsed time.
		After calling pause(), you may just start calling advance() again to resume.
		"""
		if self.seconds_updater is not None:
			self.after_cancel(self.seconds_updater)
			self.seconds_updater = None
		self.systime_offset = None
		self.config(fg=paused_color)
				
	def done(self):
		"""Stop timekeeping at the end of a song.
		"""
		self._update_string(self.duration)		# just to be sure it looks right!
		self.config(fg=inactive_color)
		if self.seconds_updater is not None:
			self.after_cancel(self.seconds_updater)
			self.seconds_updater = None
		self.systime_offset = None

	
def everything_off():
	"""Turn off every note, in case it's stuck playing.
	"""
	for mynote in range(1,128):
		out.send(mido.Message('note_off', note=mynote, velocity=100))


def play_next_message():
	"""Function that gets messages from the MIDI file and sends them out to the organ.
	
	This function runs whenever the timestamp of a message comes around. At that time,
	it sends out the message, gets a new one from the MIDI file, and re-schedules
	itself to run again when the new message is due to go out. Meanwhile, it keeps
	track of elapsed time and sends it to the GUI when there's a free moment to
	display it.
	"""
	global message
	global time_passed
	global playing
	global after_id
	global midifile_iter
		
	if not playing:
		return
	
	# Ship out the message we fetched last time we were here, if any.
	if message != None:
			
		# Disregard all other message types which may be cluttering up the file.
		if 'note_on' in message.type or 'note_off' in message.type:
			try:
				out.send(message)
			except:
				print "Oops. MIDI output failed. Jukebox cain't play no mo."
				sys.exit(1)

		time_passed += message.time

	# Now get the next message (that isn't a MetaMessage) and wait for it to be ready to ship out.
	try:
		message = midifile_iter.next()
		while isinstance(message, MetaMessage):
			message = midifile_iter.next()

		after_id = root.after(int(round(1000*message.time)), play_next_message)

		# Now, if we're actually waiting for this message to be ready, is a good time
		# to take care of less time-critical matters.
		if (message.time > 0.01):
			progressIndicator.advance(time_passed)
			time_passed = 0
		
	except StopIteration:
		playing = False
		if after_id is not None:
			root.after_cancel(after_id)
			after_id = None
		progressIndicator.done()
		done_action()


def init_playing_file(index):
	"""Initialize for playback of the MIDI file at the specified index.
	
	This function just sets up the MidiFile object, possibly discarding any existing
	MidiFile object previously in use.
	
	Playback doesn't actually start until the start_playback() function is called.
	"""
	global message
	global midifile
	global midifile_iter
	global after_id
	global time_passed
	
	# if we still have a message in flight, abort it
	if after_id != None:
		root.after_cancel(after_id)
	message = None
		
	midifile = songs.midifile(index)
	midifile_iter = iter(midifile)
	time_passed = 0
	progressIndicator.reset(midifile.length)
	

def start_playback():
	"""Begin playback of whatever MidiFile oject is currently open.
	
	This might be starting from the beginning, or resuming in the middle.
	Doesn't matter (much). All we do is kick off play_next_message(), which returns
	quickly but schedules itself to run again and again until the whole file
	has been played (or playback is paused or interrupted).
	"""
	global playing
	
	if not playing:
		playing = True
		play_next_message()			# kick things off


def stop_playback():
	"""Stops playing back the current song.
	
	Playback may be resumed later by just calling start_playback(), or not.
	"""
	global playing
	
	playing = False
	everything_off()
	
	
class SongList:
	"""List of songs taken from a subdirectory.
	
	You can get the title of the song by index, or you can ask it to create and
	return a MidiFile object for the song by index.
	"""
	def __init__(self):
		self.songspath = join(os.getcwd(), SONGS_SUBDIRECTORY)
		self.songlist = [ f for f in listdir(self.songspath) if isfile(join(self.songspath,f)) ]
		if len(self.songlist) == 0:
			print "Oh no! We don't have any song files to choose from."
			sys.exit(1)
	
	def __len__(self):
		return len(self.songlist)

	def title(self, index):
		filename,_ = os.path.splitext(self.songlist[index])
		return filename
	
	def midifile(self, index):
		return MidiFile(join(self.songspath, self.songlist[index]))


class DynamicLabel(Label):
	""" Subclass of Label that adds a method fit_text(), that scales the Label's font
	so as to fit the text within the specified max_width pixels, starting from a maximum
	font size of max_font.
	"""
	def __init__(self, *args, **kwargs):
		self.max_font = kwargs.pop("max_font", 12)
		self.max_width = kwargs.pop("max_width", 100)
		Label.__init__(self, *args, **kwargs)

		# There doesn't seem to be any way to obtain the Label's existing font object,
		# so we get its description instead and make a new font object that matches.
		# We can then manipulate that font object as needed to fit the text.
		
		font_string = self.cget("font")		# returns something like "Helvetica 48 bold"
		font_params = font_string.split()
		if len(font_params) < 3:
			weight=NORMAL
		else:
			weight=font_params[2]
		self.font = tkFont.Font(family=font_params[0], size=font_params[1], weight=weight)
		self.configure(font=self.font)
		
		
	def fit_text(self, new_text=None):
		self.configure(text=new_text)
		self.font.configure(size=self.max_font)
		
		size = self.font.actual("size")
		while self.font.measure(new_text) > self.max_width:
			size -= 1
			self.font.configure(size=size)


def set_current(index):
	"""Set the song at a specified index to be the current song.
	
	Update the display, and also initialize playback so we're ready to play it
	from the beginning.
	"""	
	global current_song_index
	
	current_song_index = index
	currentTitleLabel.fit_text(songs.title(index))
	init_playing_file(index)
	
def set_candidate(index):
	"""Set the song at a specified index to be the candidate next song.
	
	This is just a matter of remembering it and updating the display.
	"""
	global candidate_index
	
	candidate_index = index
	candidateTitleLabel.fit_text(songs.title(index))
	
def next_candidate_action():
	"""Button handler for the "next candidate song" button.
	"""
	index = candidate_index + 1
	if index >= len(songs):
		index = 0
	set_candidate(index)

def prev_candidate_action():
	"""Button handler for the "previous candidate song" button.
	"""
	index = candidate_index - 1
	if (index < 0):
		index = len(songs)-1
	set_candidate(index)

def random_candidate_action():
	"""Button handler for the "choose a random candidate song" button.
	"""
	index = random.randint(0, len(songs)-1)
	set_candidate(index)
	
def step_back_action():
	"""Button handler for the "rewind to the beginning of this song" button.
	
	If the song is currently playing, it restarts at the beginning.
	If the playback is currently paused, the progress indicator goes to 0:00 and
	when/if playback is resumed, the song restarts at the beginning.
	"""
	global current_song_index
	
	if playing:
		stop_playback()
		init_playing_file(current_song_index)
		start_playback()
	else:
		init_playing_file(current_song_index)

def step_forward_action():
	"""Button handler for the "advance to next song" button.
	
	This grabs the current candidate next song and makes it the current song.
	This doesn't start or stop playback, so:
	If playback is currently running, the new current song begins to play.
	If playback is currently paused, the progress indicator goes to 0:00 and
	when/if playback is resumed, the new current song begins to play.
	
	Meanwhile, the candidate song changes to the next song on the list.
	"""
	set_current(candidate_index)
	next_candidate_action()
	if playing:
		stop_playback()
		start_playback()

def play_action():
	"""Button handler for the "play" button.
	
	If playback is already running, this doesn't do anything.
	If playback is currently paused, this begins playback of the current song
	at the current time index, which is the beginning of the song unless it
	has previously been paused in the middle of playback.
	"""
	start_playback()
	playButton.config(state=DISABLED)
	pauseButton.config(state=NORMAL)

def pause_action():
	"""Button handler for the "pause" button.
	"""
	stop_playback()
	progressIndicator.pause()
	playButton.config(state=NORMAL)
	pauseButton.config(state=DISABLED)

def done_action():
	"""pseudo-button handler for the end of a song playback
	"""
	playButton.config(state=DISABLED)
	pauseButton.config(state=DISABLED)

def initialize_MIDI_out():
	"""Initialize a MIDI output port using RTMIDI through mido
	"""

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
	
	return out


out = initialize_MIDI_out()

root = Tk()

# This program ends normally when we receive a SIGUSR1 signal from the supervisor.
def handle_sigusr1(signum, frame):
	root.quit()
signal.signal(signal.SIGUSR1, handle_sigusr1)

# There might be no events going through the event loop. That makes it unresponsive
# to things like SIGUSR1 signals. So generate some event chatter to break the impasse.
def kludge():
	root.after(100, kludge)
root.after(100, kludge)

# Load up some icon images
upImage = PhotoImage(file="icons/previous.gif")
downImage = PhotoImage(file="icons/next.gif")
randomImage = PhotoImage(file="icons/random.gif")
playImage = PhotoImage(file="icons/play.gif")
pauseImage = PhotoImage(file="icons/pause.gif")
stepLeftImage = PhotoImage(file="icons/stepleft.gif")
stepRightImage = PhotoImage(file="icons/stepright.gif")

# Create all the on-screen widgets.
# Everything relating to the current song is in the top frame, everything relating to
# the candidate next song is in the middle frame, and the transport buttons are in the
# bottom frame.

top = Frame(root, height=150, width=800, bg=top_bg)
sep1 = Frame(root, height=2, width=800, bd=1, relief=SUNKEN)
middle = Frame(root, height=120, width=800, bg=mid_bg)
sep2 = Frame(root, height=2, bd=1, width=800, relief=SUNKEN)
bottom = Frame(root, height=206, width=800, bg=bot_bg)

nowPlayingLabel = Label(top, text="Now Playing:", font=("Helvetica", 24), fg="#888", bg=top_bg, padx=4, pady=2)
progressIndicator = TimeProgressLabel(top, font=("Helvetica", 24), fg="#888", bg=top_bg, padx=4, pady=2)
currentTitleLabel = DynamicLabel(top, font=("Helvetica", 48, "bold"), fg="red", bg=top_bg, max_font=48, max_width=780)

nowPlayingLabel.place(relx=0, anchor=NW)
progressIndicator.place(relx=1, anchor=NE)
currentTitleLabel.place(relx=0.5, rely=0.95, anchor=S)


upNextLabel = Label(middle, text="Up Next:",  font=("Helvetica", 24), fg="#555", bg=mid_bg, padx=4, pady=2)
candidateTitleLabel = DynamicLabel(middle, font=("Helvetica", 30), fg="#666", bg=mid_bg, max_font=30, max_width=500)
prevButton = Button(middle, text="Prev", image=upImage, bd=0, bg=mid_bg, highlightbackground=mid_bg, highlightcolor=mid_bg, activebackground=mid_bg, activeforeground=mid_bg, command=prev_candidate_action)
nextButton = Button(middle, text="Next", image=downImage, bd=0, bg=mid_bg, highlightbackground=mid_bg, highlightcolor=mid_bg, activebackground=mid_bg, activeforeground=mid_bg, command=next_candidate_action)
randomButton = Button(middle, text="Random", image=randomImage, bd=0, bg=mid_bg, highlightbackground=mid_bg, highlightcolor=mid_bg, activebackground=mid_bg, activeforeground=mid_bg, command=random_candidate_action)

upNextLabel.place(anchor=NW)
candidateTitleLabel.place(relx=0.02, rely=0.625, anchor=W)
prevButton.place(relx=0.69, rely=0.5, anchor=CENTER)
nextButton.place(relx=0.80, rely=0.5, anchor=CENTER)
randomButton.place(relx=0.995, rely=0.5, anchor=E)


stepBackButton = Button(master=bottom, text="|<", image=stepLeftImage, bd=0, bg=bot_bg, highlightbackground=bot_bg, highlightcolor=bot_bg, activebackground=bot_bg, activeforeground=bot_bg, command=step_back_action)
playButton = Button(bottom, text=">", image=playImage, bd=0, bg=bot_bg, highlightbackground=bot_bg, highlightcolor=bot_bg, activebackground=bot_bg, activeforeground=bot_bg, command=play_action)
pauseButton = Button(bottom, text="||", image=pauseImage, bd=0, bg=bot_bg, highlightbackground=bot_bg, highlightcolor=bot_bg, activebackground=bot_bg, activeforeground=bot_bg, command=pause_action)
stepForwardButton = Button(bottom, text=">|", image=stepRightImage, bd=0, bg=bot_bg, highlightbackground=bot_bg, highlightcolor=bot_bg, activebackground=bot_bg, activeforeground=bot_bg, command=step_forward_action)

stepBackButton.place(relx=0.02, rely=0.5, anchor=W)
playButton.place(relx=0.4, rely=0.5, anchor=CENTER)
pauseButton.place(relx=0.635, rely=0.5, anchor=CENTER)
stepForwardButton.place(relx=0.98, rely=0.5, anchor=E)


top.grid_propagate(0)
top.grid()
sep1.grid()
middle.grid_propagate(0)
middle.grid()
sep2.grid()
bottom.grid_propagate(0)
bottom.grid()

songs = SongList()

if deployed_mode:
	root.attributes("-fullscreen", True)
else:
# for debug, use the same screen size as the real screen, in a handy screen position.
	root.geometry("800x480+50+50")

after_id = None
playing = False

# Start with random songs as the current and next songs
set_current(random.randint(0, len(songs)-1))
set_candidate(random.randint(0, len(songs)-1))
play_action()

root.mainloop()
print("Here we are cleaning up.")

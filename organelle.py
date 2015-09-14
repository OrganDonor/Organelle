#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#	 
#	 Pull out delete old files to funtion OK
#   Set up a port OK
#   Parse a file for notes OK 
#   Parse notes for durations OK
#   Parse rests for durations OK
#   Make a markov chain from the notes OK/Users/w5nyv/Dropbox/Pipe_Organ/MIDI/nmo_track_4.mid
#   Make a markov chain from the durations OK
#   Choose a random file OK
#   Play that random file OK  
#   Create a file from the markov chain transition table OK
#   Make a simple user interface OK
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=


#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#   Imports
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

#import mido library
import mido

#import markov chain library
import pykov

#import pysparse
import pysparse

#import random
import random

#import os
import os
from os import listdir
from os.path import isfile, join

#get the MidiFile, MidiTrack, and Message commands working
from mido import MidiFile
from mido.midifiles import MidiTrack
from mido import Message


#get the ports setup stuff working
from mido.ports import MultiPort

#so it knows what a MetaMessage is?
from mido import MetaMessage

#for using the rtmidi port manager
import time
import rtmidi
from rtmidi.midiutil import open_midiport
from rtmidi.midiconstants import *

#for using sliding window in entropy_toy()
from itertools import islice
from collections import deque


#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# setup rtmidi as our backend
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

#select rtmidi as our backend
mido.set_backend('mido.backends.rtmidi')
print "Backend selected is %s " % mido.backend

#find out available APIs
print "Available APIs are:", mido.backend.module.get_api_names()

#find what the ports are called
print "Output port names are:", mido.get_output_names()

#open up a rtmidi output port for playing midi files

try:
	out = mido.open_output()
except:
	pass
	print "Failed to open a MIDO output port, but going on with the rest of the show."

##test port by generating some tones
##turn this off when you don't have anything hooked up
#print "Test tones!"
#for i in range(36,45):
#	my_on_message = mido.Message('note_on', note=i, velocity=100)
#	print my_on_message
#	out.send(my_on_message)
#	time.sleep(0.2)
#	my_off_message = mido.Message('note_off', note=i, velocity=100)
#	print my_off_message
#	out.send(my_off_message)
#	time.sleep(0.05)








#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# Play a midi file in MIDO
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=


#print "The current mido object is %s " % mid

##You can get the total playback time in seconds by accessing the length property:
#print "Total playback time of %s is %f." % (mysong, mid.length)

##turn this off when nothing is hooked up
#for message in mid.play():
#	out.send(message)
#	print message





#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#   custom functions
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=




#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#   sliding window function
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

def sliding_window(seq, n=2):
	#Returns a sliding window (of width n) over data from the iterable"
	#   s -> (s0,s1,...s[n-1]), (s1,s2,...,sn), ..."
	print "inside the window function"
	it = iter(seq)
	print "it is", it
	print "seq is ", seq
	result = tuple(islice(it, n))
	if len(result) == n:
		yield result
		print "the result is", result
	for elem in it:
		result = result[1:] + (elem,)
		yield result
		print result





#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# Define a function to check for 
# empty text files
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
import os
def is_non_zero_file(fpath):  
    return True if os.path.isfile(fpath) and os.path.getsize(fpath) > 0 else False



#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# erase all old files
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

def erase_old_files():
	mypath = os.getcwd()
	for i in range(0, 17):
		if os.path.isfile(mypath+"/{}_track_contents.txt".format(i)):
			os.remove(mypath+"/{}_track_contents.txt".format(i))
		if os.path.isfile(mypath+"/{}_track_durations.txt".format(i)):
			os.remove(mypath+"/{}_track_durations.txt".format(i))
		if os.path.isfile(mypath+"/{}_track_transition_table.txt".format(i)):
			os.remove(mypath+"/{}_track_transition_table.txt".format(i))
			
		if os.path.isfile(mypath+"/{}_track_notes.txt".format(i)):
			os.remove(mypath+"/{}_track_notes.txt".format(i))
		if os.path.isfile(mypath+"/{}_track_notes_transition_table.txt".format(i)):
			os.remove(mypath+"/{}_track_notes_transition_table.txt".format(i))
			
		if os.path.isfile(mypath+"/{}_rest_durations.txt".format(i)):
			os.remove(mypath+"/{}_rest_durations.txt".format(i))
		if os.path.isfile(mypath+"/{}_rest_durations_transition_table.txt".format(i)):
			os.remove(mypath+"/{}_rest_durations_transition_table.txt".format(i))

		if os.path.isfile(mypath+"/{}_note_durations.txt".format(i)):
			os.remove(mypath+"/{}_note_durations.txt".format(i))
		if os.path.isfile(mypath+"/{}_note_durations_transition_table.txt".format(i)):
			os.remove(mypath+"/{}_note_durations_transition_table.txt".format(i))

		if os.path.isfile(mypath+"/nmo_track_{}.txt".format(i)):
			os.remove(mypath+"/nmo_track_{}.txt".format(i))
		if os.path.isfile(mypath+"/nmo_track_{}.mid".format(i)):
			os.remove(mypath+"/nmo_track_{}.mid".format(i))
		print "\nErased the old files listed for track {}.".format(i)




#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# Define a function to check for 
# entropy in sliding window of midi file
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=


def entropy_toy():
	print "selecting a random midi file for you"
	#os.chdir(mypath+"/songs")
	#get current working directory for file list building
	mypath = os.getcwd()
	print "Home directory for all this work is ", mypath
	os.chdir(mypath+"/songs")
	songspath = os.getcwd()
	print "The songs directory is", songspath
	onlyfiles = [ f for f in listdir(songspath) if isfile(join(songspath,f)) ]

	print "here's all %d files in the song directory" % len(onlyfiles)
	print onlyfiles

	mysong = onlyfiles[random.randint(0, len(onlyfiles)-1)]
	print "%s is a random file from the songs directory" % mysong

	#create a midi object from the midi file
	mid = MidiFile(mysong)
	

	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
	# erase all old files
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
			
	erase_old_files()

			
			
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
	# initialize variables
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
	running_tick_total = 0
	tempo = 500000
	timestamps = {}
	end_of_rest = 0
	dictionary_non_zero_length = 0
	rest_length_start = 0
	double_on = 0
	rest_delta = '0'
	note_delta = '100'
	skip_empty_track = 0
	midi_write_pass_flag = 0
	previous_note = 60
	phrase_lengths = []
	
	

	
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
	# organize the notes by track
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
	print "#-=-=-=-=-=-=-=-=Track Listing-=-=-=-=-=-=-=-=-=-=-="
	print mid.tracks
	print "#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"
	#enumerate through the tracks.
	#for each track, put all the notes in that track in a text file.
	#name the text file with the track number
	for i, track in enumerate(mid.tracks):
		print('(notes and durations) Examining Track {}: {}'.format(i, track.name))
		notes_file_name = mypath+"/{}_track_notes.txt".format(i)
		contents_file_name = mypath+"/{}_track_contents.txt".format(i)
		durations_file_name = mypath+"/{}_track_durations.txt".format(i)
		rest_durations_file_name = mypath+"/{}_rest_durations.txt".format(i)
		note_durations_file_name = mypath+"/{}_note_durations.txt".format(i)
		
		n = open(notes_file_name, 'w+')
		h = open(contents_file_name, 'w+')
		g = open(durations_file_name, 'w+')
		f = open(rest_durations_file_name, 'w+')
		j = open(note_durations_file_name, 'w+')
		
		for message in track:
			#reset all our flags
			end_of_rest = 0
			dictionary_non_zero_length = 0
			if "note_on" in message.type:
				if message.velocity > 0:
					print >>n, message.note
					print >>h, message.note
					#print "message note_on for", message.note, "has ticks", message.time
					#update running_tick_total
					running_tick_total = running_tick_total + message.time
					#print "and then I updated running tick total to ", running_tick_total
					
					#if the dictionary has a transition from zero to one, 
					#then it's the end of a rest, and we need to record a rest duration
					#set end_of_rest = 1 to flag this
					if len(timestamps) == 0:
						end_of_rest = 1
						#print "length of timestamps is", len(timestamps)
					
					#mark this note as having a particular timestamp
					#print "so I set the timestamp for", message.note, "to", running_tick_total
					timestamps[message.note] = running_tick_total

					if len(timestamps) > 0:
						#if the dictionary is non-zero (has notes in it) then dictionary_non_zero_length is set
						#this means a rest ended, and the duration needs to be reported
						dictionary_non_zero_length = 1
						#print "length of timestamps is ", len(timestamps)
					
					if (end_of_rest * dictionary_non_zero_length) == 1:
						#print "transition from size 0 to size 1 occurred!"
						#print "if the rest is non-zero in length, record it."
						if (running_tick_total - rest_length_start) > 0:
							#print "a rest had tick duration", (running_tick_total - rest_length_start)
							print >>g, "a rest had tick duration", (running_tick_total - rest_length_start)
							print >>f, (running_tick_total - rest_length_start)
							print >>h, "rest"


				elif message.velocity == 0:
					#print "Message velocity was zero for note", message.note, "with ticks", message.time
					#update running_tick_total
					running_tick_total = running_tick_total + message.time
					#print "and then I updated running tick total to ", running_tick_total
					#calculate difference between two time stamps (running_tick_total)
					try:
						#print "Note", message.note, "had tick duration", (running_tick_total - timestamps[message.note])
						print >>g, "Note", message.note, "had tick duration", (running_tick_total - timestamps[message.note])
						print >>j, (running_tick_total - timestamps[message.note])
						del timestamps[message.note]
					except:
						#print "Double note off occurred"
						pass
					#print "and then I removed the timestamp entry for note", message.note
					#test if the dictionary is now empty.
					#if it is then make a timestamp because this is the start of a rest. 
					if len(timestamps) == 0:
						rest_length_start = running_tick_total
			elif "note_off" in message.type:
				#print "note_off for note", message.note, "has ticks ", message.time
				#update running_tick_total
				running_tick_total = running_tick_total + message.time
				#print "and then I updated running tick total to ", running_tick_total				#calculate difference between two time stamps (running_tick_total)
				try:
					#print "Note", message.note, "had tick duration", (running_tick_total - timestamps[message.note])
					print >>g, "Note", message.note, "had tick duration", (running_tick_total - timestamps[message.note])
					print >>j, (running_tick_total - timestamps[message.note])
					del timestamps[message.note]
				except:
					#print "Double note off occurred"
					pass				
				#print "and then I removed the timestamp entry for note", message.note
				#test if the dictionary is now empty.
				#if it is then make a timestamp because this is the start of a rest. 
				if len(timestamps) == 0:
					rest_length_start = running_tick_total
			elif "set_tempo" in message.type:
				#print "I GOT A SET TEMPO of ", message.tempo, "at time ", message.time
				tempo = message.tempo

			#print "#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"
			#print "timestamps from this message are:", timestamps
			#print "#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"
		n.close()
		h.close()
		g.close()
		f.close()
		
		
#The event time is measured in ticks. In the header of the midi file, you find the resolution, which tells you how many ticks are in one quarter note. The resolution is usually a multiple of 24, to allow using integral tick values for normal, dotted and triplet notes.
#
#This information is sufficient to calculate the note duration independent from tempo.
#
#If you need the duration in milliseconds, you need the initial tempo from the header, plus all tempo change meta events within the midi file. Using all tempo changes, you can build a tempo map. Then you can calculate the time of every tempo change. Since the tempo is unchanged between two tempo changes, you can calculate the exact begin, end and duration of every note.

# ticks = number of ticks until the following event

#Tempo is in microseconds per beat (quarter note). 
#The default tempo is 500000 microseconds per beat (quarter note), 
#which is half a second per beat or 120 beats per minute. 
		
		
		
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
	# Make entropy windows
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

	#go through all the text files we created
	#if the track is non-empty, then process it
	#into a markov chain
	#j is the track we're on
	#r, R = pykov.maximum_likelihood_probabilities(v,lag_time=1, separator='rest')

	
	#now make a set of notes that are based on the transition tables, and save to a file. 
	for j in range(0, i+1):

			
		file_name = mypath+"/{}_track_contents.txt".format(j)
		if not is_non_zero_file(file_name):
			print "{}_track_contents.txt is empty".format(j)
			#skip_empty_track is set whenever we have an empty track
			phrase_lengths.append(None)
			skip_empty_track = 1
		else:
			print "{}_track_contents.txt will be examined for entropy changes".format(j)
			t = pykov.readtrj(mypath+"/{}_track_contents.txt".format(j))
			p, P = pykov.maximum_likelihood_probabilities(t,lag_time=1)
			tt_file_name = mypath+"/{}_track_transition_table.txt".format(j)
			k = open(tt_file_name, 'w+')
			#p is a pykov vector. It's the probability distribution of all the notes in the track.
			#P is a pykov chain. It's a transition table. Probability of one note followed by another. 
			#Save our transition table to a file.
			print >>k, P
			print "The Kemeny constant of the track contents transition table is", P.kemeny_constant()
			#The presence or absence of the rests makes a differences in the Kemeny constant
			#results for the contents track vs. the notes track. 
			#This is an area of investigation that might make a difference. Maybe chart the % rest per track too?
			#also, from here, use the Kemeny constant to set the initial phrase length
			phrase_lengths.append(P.kemeny_constant())
			#Generate a phrase of length equal to the Kemeny constant of the track
			print "A phrase of kemeny length from this transition table is:", P.walk(int(P.kemeny_constant()))
			entropy_file_length = num_lines = sum(1 for line in open(mypath+"/{}_track_contents.txt".format(j)))
			print "{}_track_contents.txt is ".format(j), entropy_file_length, "lines long"
			print "Now we're going to use the Kemeny Constant length as a sliding window for entropy."
			
			
			#entropy_file_length = number of lines in file
			#P.kemeny_constant() = length of chunk
			
			#not working
			sliding_window(file_name, P.kemeny_constant())
			
#			def window(seq, n=2):
#			    "Returns a sliding window (of width n) over data from the iterable"
#			    "   s -> (s0,s1,...s[n-1]), (s1,s2,...,sn), ...                   "
#			    it = iter(seq)
#			    result = tuple(islice(it, n))
#			    if len(result) == n:
#			        yield result    
#			    for elem in it:
#			        result = result[1:] + (elem,)
#			        yield result
	
			
			
#			Here's a generalization that adds support for step, fillvalue parameters:
#
#			from collections import deque
#			from itertools import islice
#
#			def sliding_window(iterable, size=2, step=1, fillvalue=None):
#			    if size < 0 or step < 1:
#			        raise ValueError
#			    it = iter(iterable)
#			    q = deque(islice(it, size), maxlen=size)
#			    if not q:
#			        return  # empty iterable or size == 0
#			    q.extend(fillvalue for _ in range(size - len(q)))  # pad to size
#			    while True:
#			        yield iter(q)  # iter() to avoid accidental outside modifications
#			        q.append(next(it))
#			        q.extend(next(it, fillvalue) for _ in range(step - 1))
#			It yields in chunks size items at a time rolling step positions per iteration padding each chunk with fillvalue if necessary. Example for size=4, step=3, fillvalue='*':
#
#			 [a b c d]e f g h i j k l m n o p q r s t u v w x y z
#			  a b c[d e f g]h i j k l m n o p q r s t u v w x y z
#			  a b c d e f[g h i j]k l m n o p q r s t u v w x y z
#			  a b c d e f g h i[j k l m]n o p q r s t u v w x y z
#			  a b c d e f g h i j k l[m n o p]q r s t u v w x y z
#			  a b c d e f g h i j k l m n o[p q r s]t u v w x y z
#			  a b c d e f g h i j k l m n o p q r[s t u v]w x y z
#			  a b c d e f g h i j k l m n o p q r s t u[v w x y]z
#			  a b c d e f g h i j k l m n o p q r s t u v w x[y z * *]
			




#			#this doesn't read in overlapping blocks, but might be useful for something
#			with open(mypath+"/{}_track_contents.txt".format(j)) as entropy_file:
#				while True:
#					kemeny_chunk = list(islice(entropy_file, P.kemeny_constant()))
#					print "kemeny chunk is", kemeny_chunk
#					print "\n\n"
#					if not kemeny_chunk:
#						break
#			        # process next_n_lines
			
			
			
			


		file_name = mypath+"/{}_track_notes.txt".format(j)
		if not is_non_zero_file(file_name):
			print "{}_track_notes.txt is empty".format(j)
			skip_empty_track = 1
		else:
			print "{}_track_notes.txt will become a markov object and a new music object".format(j)
			t = pykov.readtrj(mypath+"/{}_track_notes.txt".format(j))
			m, M = pykov.maximum_likelihood_probabilities(t,lag_time=1)
			tt_file_name = mypath+"/{}_track_notes_transition_table.txt".format(j)
			k = open(tt_file_name, 'w+')
			#p is a pykov vector. It's the probability distribution of all the notes in the track.
			#P is a pykov chain. It's a transition table. Probability of one note followed by another. 
			#Save our transition table to a file.
			print >>k, M		
			#print "The Kemeny constant of the notes durations transition table"
			#print "doesn't seem to always exist. AI to find out why."
			#print "When it does, it is", M.kemeny_constant()
			
			#not working
			sliding_window(file_name, M.kemeny_constant())


		
		
		file_name = mypath+"/{}_rest_durations.txt".format(j)
		if not is_non_zero_file(file_name):
			print "{}_rest_durations.txt is empty".format(j)
			skip_empty_track = 1
		else:
			#process the track into a markov chain thing
			print "{}_rest_durations.txt will become a markov object and a new music object".format(j)
			u = pykov.readtrj(mypath+"/{}_rest_durations.txt".format(j))
			q, Q = pykov.maximum_likelihood_probabilities(u,lag_time=1)
			print "if there aren't any rests to give a transition table, don't try to write one."
			#print "sorted q is currently ", q.sort(reverse = True)
			#print "Q is currently ", Q
			if len(q) > 0:
				rest_delta = (q.sort(reverse = True)[0])[0]
				tt_file_name = mypath+"/{}_rest_durations_transition_table.txt".format(j)
				k = open(tt_file_name, 'w+')
				#p is a pykov vector. It's the probability distribution of all the notes in the track.
				#P is a pykov chain. It's a transition table. Probability of one note followed by another. 
				#Save our transition table to a file.
				print >>k, Q
				#print "The Kemeny constant of the rest durations transition table"
				#print "doesn't seem to always exist. AI to find out why."
				#print "When it does, it is", Q.kemeny_constant()
			
			
		file_name = mypath+"/{}_note_durations.txt".format(j)
		if not is_non_zero_file(file_name):
			print "{}_note_durations.txt is empty".format(j)
			skip_empty_track = 1
		else:
			#process the track into a markov chain thing
			print "{}_note_durations.txt will become a markov object and a new music object".format(j)
			v = pykov.readtrj(mypath+"/{}_note_durations.txt".format(j))
			r, R = pykov.maximum_likelihood_probabilities(v,lag_time=1)
			note_delta = (r.sort(reverse = True)[0])[0]
			
			tt_file_name = mypath+"/{}_note_durations_transition_table.txt".format(j)
			k = open(tt_file_name, 'w+')
			#p is a pykov vector. It's the probability distribution of all the notes in the track.
			#P is a pykov chain. It's a transition table. Probability of one note followed by another. 
			#Save our transition table to a file.
			print >>k, R
			print "The Kemeny constant of the note durations transition table is", R.kemeny_constant()


		
		#P.walk(n) gives a random walk of n notes based on the contents transition table. Returns an array.
		#P.move(state) gives the next state based on the transition table. Returns a string here.
		if skip_empty_track == 0:
			nmo_file_name = mypath+"/nmo_track_{}.txt".format(j)
			l = open(nmo_file_name, 'w+')
			print >>l, P.walk(100)
			
	
			
			#Determine chain entropy
			#entropy(p=None, norm=False)
			#Return the Chain entropy, defined as $H = \sum_i \pi_i H_i$, where $H_i=\sum_j T_{ij}\ln T_{ij}$. 
			#If p is not None, then the entropy is calculated with the indicated probability pykov.Vector().
			#>>> T = pykov.Chain({('A','B'): .3, ('A','A'): .7, ('B','A'): 1.})
			#>>> T.entropy()
			#0.46989561696530169
			#With norm=True entropy belongs to [0,1].
			#In this respect, entropy can be normalized by dividing it by information length. 
			#This ratio is called metric entropy and is a measure of the randomness of the information.
			
			print "The normalized chain entropy of {}_track_contents.txt is ".format(j), P.entropy(p, norm=True)
			
			#Determine vector entropy
			#Return the Shannon entropy, defined as $H(p) = \sum_i p_i \ln p_i$.
			print "The vector entropy of {}_track_contents.txt is ".format(j), p.entropy()
			#print "The vector sums to ", p.sum()
			#print "The vector sorted is: ", p.sort(reverse = True)

			#print "The first element of the sorted vector is a tuple: ", p.sort(reverse = True)[0]
			#print "The first element of this tuple is the most common note, namely: ", (p.sort(reverse = True)[0])[0]
			#http://en.wikipedia.org/wiki/First-hitting-time_model
			#print "The Mean First Passage Times of every note in the chain to the most common note is: ", P.mfpt_to((p.sort(reverse = True)[0])[0])

			#print "The second element of the sorted vector is a tuple: ", p.sort(reverse = True)[1]
			#print "The first element of this tuple is the second most common note, namely: ", (p.sort(reverse = True)[1])[0]
			#http://en.wikipedia.org/wiki/First-hitting-time_model
			#print "The Mean First Passage Times of every note in the chain to the second most common note is: ", P.mfpt_to((p.sort(reverse = True)[1])[0])
			#print "The type of the most common element in the table is ", type(p.sort(reverse = True)[0][0])
			
			
			
			if type(p.sort(reverse = True)[0][0]) is str:
				previous_note = p.sort(reverse = True)[1][0]
				#print "most common note was a rest, so pick up the second result as previous_note, which was ", previous_note, "and is type", type(previous_note)
			else:
				previous_note = p.sort(reverse = True)[0][0]
				#print "most common note was a note, which was ", previous_note, "and is type", type(previous_note)
			
			
			#print "The Mean First Passage Times of every note in the chain to the most common note is: ", P.mfpt_to(previous_note)
					
					

			with MidiFile() as outfile:
				track = MidiTrack()
				outfile.tracks.append(track)
				track.append(Message('program_change', program=12))
				
				for i in P.walk(100):
					#print "the message from P.walk(100) is", i, "and is type", type(i)
					if i == 'rest':
						#print "the message is a rest"
						#then extend previous note_off to make a rest? a longer rest?
						track.append(Message('note_off', note=int(previous_note), velocity=100, time=int(rest_delta)))
						#P.move(state) gives the next state based on the transition table. Returns a string here.
						#print "rest_delta is ", rest_delta
						rest_delta = Q.move(rest_delta)
					else:
						#print "the message is a note"
						#previous_note begins life from the transition table as an integer
						#M.move() expects a string, though, so we have to convert the type from int to str
						#to get the next note. When the note is written to the track, it has to be an int.
						note = M.move(previous_note)
						#note = int(i)
						#check this carefully
						track.append(Message('note_on', note=int(note), velocity=100, time=int(note_delta)))
						track.append(Message('note_off', note=int(note), velocity=100, time=int(rest_delta)))
						note_delta = R.move(note_delta)
						previous_note = note

				
				
				outfile.save('/Users/w5nyv/Dropbox/Pipe_Organ/MIDI/nmo_track_{}.mid'.format(j))
				#create and play a midi object from the midi file we just made
				nmo_file = MidiFile('/Users/w5nyv/Dropbox/Pipe_Organ/MIDI/nmo_track_{}.mid'.format(j))

				
				#now attempt to play the new music object
				#if no port is set up, then skip over trying to output to the midi port
				for message in nmo_file.play():
					if midi_write_pass_flag == 0:
						try:
							print 'Attempting to play this new music object created from track {}.'.format(j)
							out.send(message)
						except:
							print "I can't find a midi out port so setting a pass flag."
							midi_write_pass_flag = 1
							print "midi_write_pass_flag is ", midi_write_pass_flag
							pass
	
		else:
			print "track empty, so no transition table created"
			skip_empty_track = 0
		


		
		print "phrase lengths are", phrase_lengths







#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# Select a random midi file 
# from the songs directory
# and make a MIDO object from that file.
# Then play it.
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

def composer():

	print "selecting a random midi file for you"
	#os.chdir(mypath+"/songs")
	#get current working directory for file list building
	mypath = os.getcwd()
	print "Home directory for all this work is ", mypath
	os.chdir(mypath+"/songs")
	songspath = os.getcwd()
	print "The songs directory is", songspath
	onlyfiles = [ f for f in listdir(songspath) if isfile(join(songspath,f)) ]

	print "here's all %d files in the song directory" % len(onlyfiles)
	print onlyfiles

	mysong = onlyfiles[random.randint(0, len(onlyfiles)-1)]
	print "%s is a random file from the songs directory" % mysong


	#create a midi object from the midi file
	mid = MidiFile(mysong)

	#Get the timing under control
	#Timing in MIDI files is all centered around beats. 
	#A beat is the same as a quarter note.
	#Tempo is given in microseconds per beat, and beats are divided into ticks.
	#The default tempo is 500000 microseconds per beat, 
	#which is half a second per beat or 120 beats per minute. 
	#The meta message 'set_tempo' can be used to change tempo during a song.
	#class mido.MidiFile(filename=None, type=1, ticks_per_beat=480, charset='latin1')


	#print "mid.ticks_per_beat is %s " % mid.ticks_per_beat
	#print "mid.tempo is %s " % mid.tempo


	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
	# erase all old files
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
	erase_old_files()


	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
	# initialize variables
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
	running_tick_total = 0
	tempo = 500000
	timestamps = {}
	end_of_rest = 0
	dictionary_non_zero_length = 0
	rest_length_start = 0
	double_on = 0
	rest_delta = '0'
	note_delta = '100'
	skip_empty_track = 0
	midi_write_pass_flag = 0
	previous_note = 60
	phrase_lengths = []
	
	

	
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
	# organize the notes by track
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
	print "mid.ticks_per_beat is %s " % mid.ticks_per_beat
	print "#-=-=-=-=-=-=-=-=Track Listing-=-=-=-=-=-=-=-=-=-=-="
	print mid.tracks
	print "#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"
	#enumerate through the tracks.
	#for each track, put all the notes in that track in a text file.
	#name the text file with the track number
	for i, track in enumerate(mid.tracks):
		print('(notes and durations) Examining Track {}: {}'.format(i, track.name))
		notes_file_name = mypath+"/{}_track_notes.txt".format(i)
		contents_file_name = mypath+"/{}_track_contents.txt".format(i)
		durations_file_name = mypath+"/{}_track_durations.txt".format(i)
		rest_durations_file_name = mypath+"/{}_rest_durations.txt".format(i)
		note_durations_file_name = mypath+"/{}_note_durations.txt".format(i)
		
		n = open(notes_file_name, 'w+')
		h = open(contents_file_name, 'w+')
		g = open(durations_file_name, 'w+')
		f = open(rest_durations_file_name, 'w+')
		j = open(note_durations_file_name, 'w+')
		
		for message in track:
			#reset all our flags
			end_of_rest = 0
			dictionary_non_zero_length = 0
			if "note_on" in message.type:
				if message.velocity > 0:
					print >>n, message.note
					print >>h, message.note
					#print "message note_on for", message.note, "has ticks", message.time
					#update running_tick_total
					running_tick_total = running_tick_total + message.time
					#print "and then I updated running tick total to ", running_tick_total
					
					#if the dictionary has a transition from zero to one, 
					#then it's the end of a rest, and we need to record a rest duration
					#set end_of_rest = 1 to flag this
					if len(timestamps) == 0:
						end_of_rest = 1
						#print "length of timestamps is", len(timestamps)
					
					#mark this note as having a particular timestamp
					#print "so I set the timestamp for", message.note, "to", running_tick_total
					timestamps[message.note] = running_tick_total

					if len(timestamps) > 0:
						#if the dictionary is non-zero (has notes in it) then dictionary_non_zero_length is set
						#this means a rest ended, and the duration needs to be reported
						dictionary_non_zero_length = 1
						#print "length of timestamps is ", len(timestamps)
					
					if (end_of_rest * dictionary_non_zero_length) == 1:
						#print "transition from size 0 to size 1 occurred!"
						#print "if the rest is non-zero in length, record it."
						if (running_tick_total - rest_length_start) > 0:
							#print "a rest had tick duration", (running_tick_total - rest_length_start)
							print >>g, "a rest had tick duration", (running_tick_total - rest_length_start)
							print >>f, (running_tick_total - rest_length_start)
							print >>h, "rest"


				elif message.velocity == 0:
					#print "Message velocity was zero for note", message.note, "with ticks", message.time
					#update running_tick_total
					running_tick_total = running_tick_total + message.time
					#print "and then I updated running tick total to ", running_tick_total
					#calculate difference between two time stamps (running_tick_total)
					try:
						#print "Note", message.note, "had tick duration", (running_tick_total - timestamps[message.note])
						print >>g, "Note", message.note, "had tick duration", (running_tick_total - timestamps[message.note])
						print >>j, (running_tick_total - timestamps[message.note])
						del timestamps[message.note]
					except:
						#print "Double note off occurred"
						pass
					#print "and then I removed the timestamp entry for note", message.note
					#test if the dictionary is now empty.
					#if it is then make a timestamp because this is the start of a rest. 
					if len(timestamps) == 0:
						rest_length_start = running_tick_total
			elif "note_off" in message.type:
				#print "note_off for note", message.note, "has ticks ", message.time
				#update running_tick_total
				running_tick_total = running_tick_total + message.time
				#print "and then I updated running tick total to ", running_tick_total				#calculate difference between two time stamps (running_tick_total)
				try:
					#print "Note", message.note, "had tick duration", (running_tick_total - timestamps[message.note])
					print >>g, "Note", message.note, "had tick duration", (running_tick_total - timestamps[message.note])
					print >>j, (running_tick_total - timestamps[message.note])
					del timestamps[message.note]
				except:
					#print "Double note off occurred"
					pass				
				#print "and then I removed the timestamp entry for note", message.note
				#test if the dictionary is now empty.
				#if it is then make a timestamp because this is the start of a rest. 
				if len(timestamps) == 0:
					rest_length_start = running_tick_total
			elif "set_tempo" in message.type:
				#print "I GOT A SET TEMPO of ", message.tempo, "at time ", message.time
				tempo = message.tempo

			#print "#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"
			#print "timestamps from this message are:", timestamps
			#print "#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"
		n.close()
		h.close()
		g.close()
		f.close()
		
		
#The event time is measured in ticks. In the header of the midi file, you find the resolution, which tells you how many ticks are in one quarter note. The resolution is usually a multiple of 24, to allow using integral tick values for normal, dotted and triplet notes.
#
#This information is sufficient to calculate the note duration independent from tempo.
#
#If you need the duration in milliseconds, you need the initial tempo from the header, plus all tempo change meta events within the midi file. Using all tempo changes, you can build a tempo map. Then you can calculate the time of every tempo change. Since the tempo is unchanged between two tempo changes, you can calculate the exact begin, end and duration of every note.

# ticks = number of ticks until the following event

#Tempo is in microseconds per beat (quarter note). 
#The default tempo is 500000 microseconds per beat (quarter note), 
#which is half a second per beat or 120 beats per minute. 
		
		
		
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
	# Make transition tables from a midi file
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

	#go through all the text files we created
	#if the track is non-empty, then process it
	#into a markov chain
	#j is the track we're on
	#r, R = pykov.maximum_likelihood_probabilities(v,lag_time=1, separator='rest')

	
	#now make a set of notes that are based on the transition tables, and save to a file. 
	for j in range(0, i+1):

			
		file_name = mypath+"/{}_track_contents.txt".format(j)
		if not is_non_zero_file(file_name):
			print "{}_track_contents.txt is empty".format(j)
			#skip_empty_track is set whenever we have an empty track
			phrase_lengths.append(None)
			skip_empty_track = 1
		else:
			print "{}_track_contents.txt will become a markov object and a new music object".format(j)
			t = pykov.readtrj(mypath+"/{}_track_contents.txt".format(j))
			p, P = pykov.maximum_likelihood_probabilities(t,lag_time=1)
			tt_file_name = mypath+"/{}_track_transition_table.txt".format(j)
			k = open(tt_file_name, 'w+')
			#p is a pykov vector. It's the probability distribution of all the notes in the track.
			#P is a pykov chain. It's a transition table. Probability of one note followed by another. 
			#Save our transition table to a file.
			print >>k, P
			print "The Kemeny constant of the track contents transition table is", P.kemeny_constant()
			#The presence or absence of the rests makes a differences in the Kemeny constant
			#results for the contents track vs. the notes track. 
			#This is an area of investigation that might make a difference. Maybe chart the % rest per track too?
			#also, from here, use the Kemeny constant to set the initial phrase length
			phrase_lengths.append(P.kemeny_constant())
			#Generate a phrase of length equal to the Kemeny constant of the track
			print "A phrase of kemeny length from this transition table is:", P.walk(int(P.kemeny_constant()))


		file_name = mypath+"/{}_track_notes.txt".format(j)
		if not is_non_zero_file(file_name):
			print "{}_track_notes.txt is empty".format(j)
			skip_empty_track = 1
		else:
			print "{}_track_notes.txt will become a markov object and a new music object".format(j)
			t = pykov.readtrj(mypath+"/{}_track_notes.txt".format(j))
			m, M = pykov.maximum_likelihood_probabilities(t,lag_time=1)
			tt_file_name = mypath+"/{}_track_notes_transition_table.txt".format(j)
			k = open(tt_file_name, 'w+')
			#p is a pykov vector. It's the probability distribution of all the notes in the track.
			#P is a pykov chain. It's a transition table. Probability of one note followed by another. 
			#Save our transition table to a file.
			print >>k, M		
			#print "The Kemeny constant of the notes durations transition table"
			#print "doesn't seem to always exist. AI to find out why."
			#print "When it does, it is", M.kemeny_constant()

		
		
		file_name = mypath+"/{}_rest_durations.txt".format(j)
		if not is_non_zero_file(file_name):
			print "{}_rest_durations.txt is empty".format(j)
			skip_empty_track = 1
		else:
			#process the track into a markov chain thing
			print "{}_rest_durations.txt will become a markov object and a new music object".format(j)
			u = pykov.readtrj(mypath+"/{}_rest_durations.txt".format(j))
			q, Q = pykov.maximum_likelihood_probabilities(u,lag_time=1)
			print "if there aren't any rests to give a transition table, don't try to write one."
			#print "sorted q is currently ", q.sort(reverse = True)
			#print "Q is currently ", Q
			if len(q) > 0:
				rest_delta = (q.sort(reverse = True)[0])[0]
				tt_file_name = mypath+"/{}_rest_durations_transition_table.txt".format(j)
				k = open(tt_file_name, 'w+')
				#p is a pykov vector. It's the probability distribution of all the notes in the track.
				#P is a pykov chain. It's a transition table. Probability of one note followed by another. 
				#Save our transition table to a file.
				print >>k, Q
				#print "The Kemeny constant of the rest durations transition table"
				#print "doesn't seem to always exist. AI to find out why."
				#print "When it does, it is", Q.kemeny_constant()
			
			
		file_name = mypath+"/{}_note_durations.txt".format(j)
		if not is_non_zero_file(file_name):
			print "{}_note_durations.txt is empty".format(j)
			skip_empty_track = 1
		else:
			#process the track into a markov chain thing
			print "{}_note_durations.txt will become a markov object and a new music object".format(j)
			v = pykov.readtrj(mypath+"/{}_note_durations.txt".format(j))
			r, R = pykov.maximum_likelihood_probabilities(v,lag_time=1)
			note_delta = (r.sort(reverse = True)[0])[0]
			
			tt_file_name = mypath+"/{}_note_durations_transition_table.txt".format(j)
			k = open(tt_file_name, 'w+')
			#p is a pykov vector. It's the probability distribution of all the notes in the track.
			#P is a pykov chain. It's a transition table. Probability of one note followed by another. 
			#Save our transition table to a file.
			print >>k, R
			print "The Kemeny constant of the note durations transition table is", R.kemeny_constant()


		
		#P.walk(n) gives a random walk of n notes based on the contents transition table. Returns an array.
		#P.move(state) gives the next state based on the transition table. Returns a string here.
		if skip_empty_track == 0:
			nmo_file_name = mypath+"/nmo_track_{}.txt".format(j)
			l = open(nmo_file_name, 'w+')
			print >>l, P.walk(100)
			
	
			
			#Determine chain entropy
			#entropy(p=None, norm=False)
			#Return the Chain entropy, defined as $H = \sum_i \pi_i H_i$, where $H_i=\sum_j T_{ij}\ln T_{ij}$. 
			#If p is not None, then the entropy is calculated with the indicated probability pykov.Vector().
			#>>> T = pykov.Chain({('A','B'): .3, ('A','A'): .7, ('B','A'): 1.})
			#>>> T.entropy()
			#0.46989561696530169
			#With norm=True entropy belongs to [0,1].
			#In this respect, entropy can be normalized by dividing it by information length. 
			#This ratio is called metric entropy and is a measure of the randomness of the information.
			
			print "The normalized chain entropy of {}_track_contents.txt is ".format(j), P.entropy(p, norm=True)
			
			#Determine vector entropy
			#Return the Shannon entropy, defined as $H(p) = \sum_i p_i \ln p_i$.
			print "The vector entropy of {}_track_contents.txt is ".format(j), p.entropy()
			#print "The vector sums to ", p.sum()
			#print "The vector sorted is: ", p.sort(reverse = True)

			#print "The first element of the sorted vector is a tuple: ", p.sort(reverse = True)[0]
			#print "The first element of this tuple is the most common note, namely: ", (p.sort(reverse = True)[0])[0]
			#http://en.wikipedia.org/wiki/First-hitting-time_model
			#print "The Mean First Passage Times of every note in the chain to the most common note is: ", P.mfpt_to((p.sort(reverse = True)[0])[0])

			#print "The second element of the sorted vector is a tuple: ", p.sort(reverse = True)[1]
			#print "The first element of this tuple is the second most common note, namely: ", (p.sort(reverse = True)[1])[0]
			#http://en.wikipedia.org/wiki/First-hitting-time_model
			#print "The Mean First Passage Times of every note in the chain to the second most common note is: ", P.mfpt_to((p.sort(reverse = True)[1])[0])
			#print "The type of the most common element in the table is ", type(p.sort(reverse = True)[0][0])
			
			
			
			if type(p.sort(reverse = True)[0][0]) is str:
				previous_note = p.sort(reverse = True)[1][0]
				#print "most common note was a rest, so pick up the second result as previous_note, which was ", previous_note, "and is type", type(previous_note)
			else:
				previous_note = p.sort(reverse = True)[0][0]
				#print "most common note was a note, which was ", previous_note, "and is type", type(previous_note)
			
			
			#print "The Mean First Passage Times of every note in the chain to the most common note is: ", P.mfpt_to(previous_note)
					
					

			with MidiFile() as outfile:
				track = MidiTrack()
				outfile.tracks.append(track)
				track.append(Message('program_change', program=12))
				
				for i in P.walk(100):
					#print "the message from P.walk(100) is", i, "and is type", type(i)
					if i == 'rest':
						#print "the message is a rest"
						#then extend previous note_off to make a rest? a longer rest?
						track.append(Message('note_off', note=int(previous_note), velocity=100, time=int(rest_delta)))
						#P.move(state) gives the next state based on the transition table. Returns a string here.
						#print "rest_delta is ", rest_delta
						rest_delta = Q.move(rest_delta)
					else:
						#print "the message is a note"
						#previous_note begins life from the transition table as an integer
						#M.move() expects a string, though, so we have to convert the type from int to str
						#to get the next note. When the note is written to the track, it has to be an int.
						note = M.move(previous_note)
						#note = int(i)
						#check this carefully
						track.append(Message('note_on', note=int(note), velocity=100, time=int(note_delta)))
						track.append(Message('note_off', note=int(note), velocity=100, time=int(rest_delta)))
						note_delta = R.move(note_delta)
						previous_note = note

				
				
				outfile.save('/Users/w5nyv/Dropbox/Pipe_Organ/MIDI/nmo_track_{}.mid'.format(j))
				#create and play a midi object from the midi file we just made
				nmo_file = MidiFile('/Users/w5nyv/Dropbox/Pipe_Organ/MIDI/nmo_track_{}.mid'.format(j))

				
				#now attempt to play the new music object
				#if no port is set up, then skip over trying to output to the midi port
				for message in nmo_file.play():
					if midi_write_pass_flag == 0:
						try:
							print "Trying to send out the midi out port"
							out.send(message)
						except:
							print "I can't find a midi out port so setting a pass flag"
							midi_write_pass_flag = 1
							print "midi_write_pass_flag is ", midi_write_pass_flag
							pass
	
		else:
			print "track empty, so no transition table created"
			skip_empty_track = 0
		


		
		print "phrase lengths are", phrase_lengths
		

		



#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#   test that user input only numbers
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
valid = set('0123456789 ')
def test(s):
	return set(s).issubset(valid)



#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#   play n random midi files
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
def jukebox(n):
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
	# !!! initialize this variable? In each function
	# that relies on this method? Check this. 
	midi_write_pass_flag = 0
	#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

	print "picking %d random files for you." % (n - 1)
	mypath = os.getcwd()
	print "Home directory for all this work is ", mypath
	songspath = (mypath+"/songs")
	print "The songs directory is", songspath
	onlyfiles = [ f for f in listdir(songspath) if isfile(join(songspath,f)) ]
	#print "here's all %d files in the song directory" % len(onlyfiles)
	#print onlyfiles
	os.chdir(songspath)
	for x in xrange(1, n):
		mysong = onlyfiles[random.randint(0, len(onlyfiles)-1)]
		print "%s is the current random file from the songs directory" % mysong
		#create a midi object from the midi file
		mid = MidiFile(mysong)
		#print "The current mido object is %s " % mid
		#You can get the total playback time in seconds by accessing the length property:
		print "Total playback time of %s is %f seconds." % (mysong, mid.length)
		print "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
		print "Song number %d is beginning." % x
		print "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
		for message in mid.play():
			#print message
			if midi_write_pass_flag == 0:
				try:
					print "Trying to send out the midi out port in the jukebox function"
					out.send(message)
				except:
					print "I can't find a midi out port so setting a pass flag"
					midi_write_pass_flag = 1
					print "midi_write_pass_flag is ", midi_write_pass_flag
					pass
		print "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
		print "Song number %d has ended." % x
		print "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
		x = x - 1
	os.chdir(mypath)







#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#   Simple User Menu
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

ans=True
while ans:
	print("""
	1.Play a random song
	2.Play lots of random songs!
	3.Generate new tracks from random MIDI file
	4.Just play keyboard
	5.Exit/Quit
	6.Entropy Toy
	7.Play Theremin
	8.Play Memory Game
	""")
	ans=raw_input("What would you like to do? ")
	if ans=="1":
		print("\nPlaying random song")
		jukebox(2)
	elif ans=="2":
		ans=raw_input("How many random songs? ")
		if test(ans) == True:
			print("\nPlaying %d random songs." % int(ans))
			jukebox((int(ans))+1)
		else:
			print("\n Not Valid Choice Try again")
	elif ans=="3":
		composer()
	elif ans=="4":
		try:
			out.reset()
			print "All notes reset. You have the conn."
		except:
			print "No output port found. You have the conn."
		
	elif ans=="5":
		print("\n Goodbye")
		ans = None
	elif ans=="6":
		print("\nEntropy Toy Engaged")
		entropy_toy()
	elif ans=="7":
		print("\nTheremin Activated!")
		erase_old_files()
	elif ans=="8":
		print("\nMemory Game starting soon. Copy the pattern of notes. Hope you have perfect pitch! (Just kidding. Get close enough to the note and it will count.)")
	else:
		print("\n Not Valid Choice Try again")

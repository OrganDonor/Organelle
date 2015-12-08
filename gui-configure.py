#!/usr/bin/env python
#
# GUI Configuration Utility for Organ Donor Organelle
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
import pickle

import os
from os import listdir
from os.path import isfile, join

import mido
from mido import MidiFile, MetaMessage
import rtmidi

save_path = "saved_configs/"
icon_path = "icons/"
bg_happy = "#ddd"
bg_sad = "#000"


def initialize_MIDI_inout():
    """Initialize a MIDI input and output port using RTMIDI through mido
    """

    # select rtmidi as our backend
    mido.set_backend('mido.backends.rtmidi')
    # print "Backend selected is %s " % mido.backend

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


inport, outport = initialize_MIDI_inout()


root = Tk()
root.config(bg=bg_happy)


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
    global pitch
    global autorepeat

    for message in inport.iter_pending():
        if "note_on" in message.type:
            if 0 == message.channel:
                handle_note((4, message.note-35))
            elif 1 == message.channel:
                handle_note((8, message.note-35))
            else:
                print "Unknown channel", message.channel
        elif "pitchwheel" in message.type:
            if pitch == 0:
                if message.pitch < 0:
                    do_left()
                    if autorepeat is None:
                        autorepeat = root.after(autorepeat_interval, autorepeat_pitchwheel)
                elif message.pitch > 0:
                    do_right()
                    if autorepeat is None:
                        autorepeat = root.after(autorepeat_interval, autorepeat_pitchwheel)
            pitch = message.pitch
        elif "control_change" in message.type:
            set_active_entry(min(122, 128 - message.value))

    root.after(50, poll_midi)


def autorepeat_pitchwheel():
    """If the pitchwheel is held away from 0 for a time, treat that as multiple
    commands equivalent to the left or right buttons.
    """
    global pitch
    global autorepeat

    if pitch < 0:
        do_left()
        autorepeat = root.after(autorepeat_interval, autorepeat_pitchwheel)
    elif pitch > 0:
        do_right()
        autorepeat = root.after(autorepeat_interval, autorepeat_pitchwheel)
    else:
        autorepeat = None


def set_active_entry(num):
    """Move around the array of data entry fields, highlighting the current field
    and disabling buttons that would go beyond the boundaries.
    """
    global active_entry

    if active_entry != 0:
        entries[active_entry].config(state=NORMAL)

    active_entry = num

    if num != 0:
        entries[active_entry].config(state=ACTIVE)

        if active_entry == 1:
            button_left.config(state=DISABLED)
            button_right.config(state=NORMAL)
        elif active_entry == 122:
            button_left.config(state=NORMAL)
            button_right.config(state=DISABLED)
        else:
            button_left.config(state=NORMAL)
            button_right.config(state=NORMAL)

        if active_entry < 11:
            button_up.config(state=DISABLED)
            button_down.config(state=NORMAL)
        elif active_entry > 120:
            button_up.config(state=NORMAL)
            button_down.config(state=DISABLED)
        else:
            button_up.config(state=NORMAL)
            button_down.config(state=NORMAL)


def do_up():
    """Move up in the array of entry fields, if possible.
    """
    if active_entry > 10:
        set_active_entry(active_entry-10)


def do_down():
    """Move down in the array of entry fields, if possible.
    When moving to the bottom row (which has only two entries), special case.
    """
    if active_entry <= 112:
        set_active_entry(active_entry+10)
    elif active_entry <= 122:
        set_active_entry(122)


def do_left():
    """Move left in the array of entry fields, wrapping around toward the first
    entry in the upper left corner.
    """
    if active_entry > 1:
        set_active_entry(active_entry-1)


def do_right():
    """Move right in the array of entry fields, wrapping around toward the last
    entry.
    """
    if active_entry < 122:
        set_active_entry(active_entry+1)


which_buttons = None


def display_buttons(which):
    """Grid the specified set of buttons so they appear nicely on the screen
    below the fixed array of entry fields.
    """
    global which_buttons

    root.grid_rowconfigure(14, minsize=200)

    if which_buttons == "edit" and which != "edit":
        button_down.grid_forget()
        button_up.grid_forget()
        button_left.grid_forget()
        button_right.grid_forget()
        button_go.grid_forget()
        button_clear.grid_forget()
        button_save.grid_forget()
        button_restore.grid_forget()
        button_quit.grid_forget()
    elif which_buttons == "config" and which != "config":
        button_MTP1.grid_forget()
        button_MTP2.grid_forget()
        button_edit.grid_forget()
        button_quit.grid_forget()

    if which == "edit":
        button_up.grid(row=14, column=1, columnspan=3)
        button_down.grid(row=14, column=5, columnspan=3)
        button_left.grid(row=14, column=9, columnspan=3)
        button_right.grid(row=14, column=13, columnspan=3)
        button_go.grid(row=14, column=17, columnspan=3)
        button_clear.grid(row=15, column=0, columnspan=3)
        button_save.grid(row=15, column=3, columnspan=2)
        button_restore.grid(row=15, column=5, columnspan=5)
        button_quit.grid(row=15, column=17, columnspan=3)
        which_buttons = "edit"
    elif which == "config":
        button_MTP1.grid(row=14, column=7, columnspan=4)
        button_MTP2.grid(row=14, column=11, columnspan=4)
        button_edit.grid(row=14, column=16, columnspan=4)
        button_quit.grid(row=15, column=17, columnspan=3)
        which_buttons = "config"
    else:
        print "Unknown button configuration."
        sys.exit(1)


def do_clear():
    """Clear all data entered so far, and start over.
    """
    for entry in entries[1:]:
        entry.config(text="", bg="#eee")
    for note in range(1, 123):
        notes[note] = None
    set_active_entry(1)
    find_dupes()


def do_save():
    """Save the current results in a timestamped file for reference and possible
    future re-use.
    """
    filename = save_path + time.strftime("%Y%m%d-%H%M%S")
    with open(filename, "wb") as f:
        pickle.dump(notes, f)
    label_restore_button()


def label_restore_button():
    """Puts an informative label in the Restore button, with the filename to be restored.
    """
    onlyfiles = [f for f in listdir(save_path) if isfile(join(save_path, f))]

    if len(onlyfiles) == 0:
        button_restore.config(text="Restore not available", state=DISABLED)
        return

    filename = sorted(onlyfiles, reverse=True)[0]
    button_restore.config(text="Restore "+filename, state=NORMAL)


def do_restore():
    """Restores data from the most recent timestamped save file.
    """
    global notes
    do_clear()

    onlyfiles = [f for f in listdir(save_path) if isfile(join(save_path, f))]

    if len(onlyfiles) == 0:
        button_restore.config(state=DISABLED)
        return

    filename = save_path + sorted(onlyfiles, reverse=True)[0]
    with open(filename, "rb") as f:
        notes = pickle.load(f)

    for note_num in range(1, 123):
        if notes[note_num] != None:
            entries[note_num].config(text="%d'-%d" % notes[note_num], bg="#fff")
    if None not in notes[1:123]:
        button_go.config(state=NORMAL)
    else:
        button_go.config(state=DISABLED)


def do_quit():
    """Exit the program.
    """
    root.quit()


def do_go():
    """Proceed from the data entry screen to the MTP configuration screen.
    """
    set_active_entry(0)
    display_buttons("config")


def do_edit():
    """Go back from the MTP configuration screen to edit some more.
    """
    set_active_entry(1)
    display_buttons("edit")


def do_MTP1():
    """Send the MIDI commands to program MTP1 according to the configuration entered.
    """
    holes = range(1, 11) + range(21, 31) + range(41, 51) + range(61, 71) + range(81, 91) + range(101, 111) + range(121, 123)
    program_MTP(holes)


def do_MTP2():
    """Send the MIDI commands to program MTP2 according to the configuration entered.
    """
    holes = range(11, 21) + range(31, 41) + range(51, 61) + range(71, 81) + range(91, 101) + range(111, 121)
    program_MTP(holes)


def program_MTP(holes):
    """Send the MIDI commands to program a MTP.
    The list of holes gives the windchest hole numbers associated with this MTP.
    """
    configure_console(flagMidi=2, flagGhostBuster=0)

    for hole in holes:
        play_note(notes[hole], 0.1)

    # The MTP-8 board supports 64 notes and requires all to be programmed.
    # In our configuration, we have some unused notes on each MTP.
    # Send impossible notes to fill up those positions on the MTP.
    extras = 64 - len(holes)
    for i in range(0, extras):
        play_note((4, 62), 0.1)

    configure_console(flagMidi=1, flagGhostBuster=1)
    flash_console()


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
//    5    0 or 1     flagGhostBuster
//    etc. for more flags
//    N       F7      End of SysEx command, defined by MIDI standard
    """
    outport.send(mido.Message('sysex', data=[0x7d, 0x55, flagMidi, flagKBecho, flagGhostBuster]))


def flash_console():
    """Send a SysEx to the console to make the buttons all flash once.
    """
    outport.send(mido.Message('sysex', data=[0x7d, 0x50]))
    time.sleep(0.20)        # wait for the flash to be done; console is while flashing


def play_note(note, duration):
    """Play a given note (rank,number) for a given duration in seconds. (Blocking!)
    """
    rank, note_number = note
    if rank == 4:
        channel = 0
    elif rank == 8:
        channel = 1
    else:
        print "Unknown rank!"
        sys.exit(1)

    outport.send(mido.Message('note_on', note=note_number+35, channel=channel, velocity=100))
    time.sleep(duration)
    outport.send(mido.Message('note_off', note=note_number+35, channel=channel, velocity=100))


def play_rest(duration):
    """Play nothing for duration seconds. (Blocking!)
    """
    time.sleep(duration)


def clear_dupes():
    """Go through the entry widgets and clear any red backgrounds.
    """
    for num in range(1, 123):
        if notes[num] != None:
            entries[num].config(bg="#fff")


def flag_dupes(note):
    """Go through the results so far and look for a particular note, and flag
    all the matching entries as dupes by setting their background to red.
    """
    for num in range(1, 123):
        if notes[num] == note:
            entries[num].config(bg="#f00")


def find_dupes():
    """Go through the results so far and see if there are any duplicate (non-empty)
    values. For any duplicated value, call flag_dupes().
    """
    clear_dupes()

    found = set()
    dupes_found = False
    for note in notes[1:123]:
        if note is not None:
            if note in found:
                flag_dupes(note)
                dupes_found = True
            else:
                found.add(note)
    if dupes_found:
        root.config(bg=bg_sad)
    else:
        root.config(bg=bg_happy)
    return dupes_found


def handle_note(note_heard):
    """Handle a note received over the MIDI interface. This is taken to be the
    answer to the implicit question, "what note corresponds to the windchest hole
    with the number active_entry?"
    """
    if active_entry == 0:
        return

    entries[active_entry].config(text="%d'-%d" % note_heard, bg="#fff")
    notes[active_entry] = note_heard
    if not find_dupes():
        do_right()
        if None not in notes[1:123]:
            button_go.config(state=NORMAL)

# Load up some icon images
upImage = PhotoImage(file=icon_path + "previous.gif")
downImage = PhotoImage(file=icon_path + "next.gif")
leftImage = PhotoImage(file=icon_path + "redblue-left.gif")
rightImage = PhotoImage(file=icon_path + "redblue-right.gif")
goImage = PhotoImage(file=icon_path + "random.gif")

entries = [None]        # dummy entry for [0] to keep indexing simple and 1-based
notes = [None]*123

row = 0
col = 0
for hole in range(1, 123):
    label = Label(root, text="%3d:" % hole)
    label.grid(row=row, column=col)
    entry = Label(root, text="", width=5, bg="#eee", activebackground="#66f")
    entry.grid(row=row, column=col+1)
    entries.append(entry)
    col += 2
    if col >= 20:
        row += 1
        col = 0

button_up = Button(root, image=upImage, command=do_up)
button_down = Button(root, image=downImage, command=do_down)
button_left = Button(root, image=leftImage, command=do_left)
button_right = Button(root, image=rightImage, command=do_right)
button_go = Button(root, image=goImage, command=do_go, state=DISABLED)
button_clear = Button(root, text="Clear", command=do_clear)
button_save = Button(root, text="Save", command=do_save)
button_restore = Button(root, command=do_restore)
label_restore_button()
button_MTP1 = Button(root, text="Program Left MTP", command=do_MTP1)
button_MTP2 = Button(root, text="Program Right MTP", command=do_MTP2)
button_edit = Button(root, text="Edit", command=do_edit)
button_quit = Button(root, text="Quit", command=do_quit)

display_buttons("edit")

active_entry = 1
set_active_entry(1)
poll_midi()                 # kick off a frequent poll of the MIDI input port

# for debug, use the same screen size as the real screen, in a handy screen position.
# root.geometry("800x480+50+50")
# for real hardware, go full screen
root.attributes("-fullscreen", True)

root.mainloop()
print("Here we are cleaning up.")

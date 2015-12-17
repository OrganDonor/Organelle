#!/usr/bin/env python
#
# GUI Step Sequencer for Organ Donor Organelle
#
# Inspired by the Adafruit UNTZtrument, formerly called OONTZ, an array of
# lighted pushbuttons with USB MIDI output. Its typical demonstration software is
# a simple step sequencer, something like this one.
#
# 2015-12 ptw

from Tkinter import *
import tkFont

import sys
import signal
import time
from os.path import isfile
import pickle

import mido
from mido import MidiFile, MetaMessage
import rtmidi

deployed_mode = isfile("deployed.txt")      # Create this file to go full-screen, etc.
save_filename = "oontz/saved_config.pickle"
bg_color = 'green'

midi_channel = 1
notes = [48, 50, 52, 53, 55, 57, 59, 60, 62, 64, 65, 67, 69, 71, 72, 74]
notes.reverse()


def initialize_MIDI_output():
    """Initialize a MIDI output port using RTMIDI through mido
    """

    # select rtmidi as our backend
    mido.set_backend('mido.backends.rtmidi')

    # Enumerate the available port names
    outports = mido.get_output_names()

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

    return outport


outport = initialize_MIDI_output()

root = Tk()
root.config(bg=bg_color)


# This program ends normally when we receive a SIGUSR1 signal from the supervisor.
def handle_sigusr1(signum, frame):
    root.quit()
signal.signal(signal.SIGUSR1, handle_sigusr1)


class ButtonArray:
    """Packed 2D array of button-like rectangular areas drawn on a Tk canvas.
    """
    def __init__(self, parent, rows=10, columns=10, width=20, height=20, false_color='white', true_color='red', column_action=None):
        self.height = height * rows + 1
        self.width = width * columns + 1
        self.canvas = Canvas(parent, width=self.width, height=self.height, bd=0, highlightthickness=0, bg=bg_color)
        self.canvas.pack(anchor=CENTER, side=RIGHT, expand=1)
        self.rows = rows
        self.columns = columns
        self.false_color = false_color
        self.true_color = true_color
        self.button_width = width
        self.button_height = height
        self.column_action = column_action
        self.rects = [[self._rect(x, y) for y in range(0, self.height, self.button_height)] for x in range(0, self.width, self.button_width)]
        self.truth = [[False            for y in range(0, self.height, self.button_height)] for x in range(0, self.width, self.button_width)]
        self.cursor = self.canvas.create_line(0, 0, 0, self.height, fill='blue', width=3)
        self.cursor_position = -1
        self._scan_cursor()
        self.canvas.bind("<Button-1>", self._tapped)

    def _rect(self, x, y):
        """Create a rectangle on the canvas with upper left corner at given coordinates."""
        return self.canvas.create_rectangle(x, y, x + self.button_width, y + self.button_height, fill=self.false_color)

    def _tapped(self, event):
        """Called when a tap is detected on the Canvas."""
        # For coding convenience we define the button's tappable area to include the
        # upper and left borders but not the lower or right borders.
        col_index = event.x // self.button_width
        row_index = event.y // self.button_height
        if col_index > self.columns or row_index > self.rows:
            return
        self._toggle(row=row_index, col=col_index)

    def _toggle(self, row, col):
        """Called when a tap is detected within a particular button area."""
        self.truth[col][row] = not self.truth[col][row]
        self._redraw(row=row, col=col)

    def _redraw(self, row, col):
        """Repaint the surface of a particular button area."""
        if self.truth[col][row]:
            self.canvas.itemconfig(self.rects[col][row], fill=self.true_color)
        else:
            self.canvas.itemconfig(self.rects[col][row], fill=self.false_color)

    def clear(self):
        """Clear all the buttons"""
        for col in range(0, self.columns):
            for row in range(0, self.rows):
                if self.truth[col][row]:
                    self._toggle(row, col)

    def _scan_cursor(self):
        """Move the cursor line horizontally across the array."""
        self.canvas.move(self.cursor, 1, 0)
        position,_,_,_ = self.canvas.coords(self.cursor)
        if position >= self.width - 1:
            position = 0
            self.canvas.coords(self.cursor, 0, 0, 0, self.height)
        if self.column_action is not None and (position % self.button_width) == 0:
            self.column_action(int(position) // self.button_width)
        self.canvas.after(10, self._scan_cursor)

    def get_column(self, col):
        """Return a list of booleans representing a column in the array."""
        # make a copy to return, just in case it gets messed with
        return list(self.truth[col])

    def empty_column(self):
        """Return a list of False representing a silent column."""
        return [False] * self.rows

    def save(self):
        """Save the current truth in a file for future re-use.
        """
        with open(save_filename, "wb") as f:
            pickle.dump(self.truth, f)

    def restore(self):
        """Restore the truth from a file.
        """
        if isfile(save_filename):
            with open(save_filename, "rb") as f:
                self.truth = pickle.load(f)
            for col in range(0, self.columns):
                for row in range(0, self.rows):
                    self._redraw(row, col)


def note_on(row):
    """Send a note_on message for the note corresponding to a given row."""
    outport.send(mido.Message('note_on', note=notes[row], channel=midi_channel, velocity=100))


def note_off(row):
    """Send a note_off message for the note corresponding to a given row."""
    outport.send(mido.Message('note_off', note=notes[row], channel=midi_channel, velocity=100))


# def play_column_differences(col):
#     """Column action: send MIDI commands to start notes that just came on
#     in this column and stop notes that were on before and aren't anymore.
#     """
#     oontz.compare_columns(col, on_action=note_on, off_action=note_off)


def play_column_differences(col):
    """Column action: send MIDI commands to start notes that just came on
    in this column and stop notes that were on before and aren't anymore.
    """
    global current_column

    new_column = oontz.get_column(col)
    for row, (before, after) in enumerate(zip(current_column, new_column)):
            if before and not after:
                note_off(row)
            elif after and not before:
                note_on(row)
    current_column = new_column


def do_clear():
    oontz.clear()


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


if deployed_mode:
    root.attributes("-fullscreen", True)
else:
    # for debug, use the same screen size as the real screen, in a handy screen position.
    root.geometry("800x480+50+50")

controls = Frame(root, width=96, height=480, bg=bg_color, bd=0, highlightthickness=0)
controls.pack(side=RIGHT, expand=1)

clear_button = Button(controls, text='Clear', command=do_clear, bg=bg_color, highlightbackground=bg_color)
clear_button.pack()

oontz = ButtonArray(root, rows=16, columns=24, height=28, width=28, column_action=play_column_differences)
oontz.restore()
current_column = oontz.empty_column()

root.mainloop()
print("Here we are cleaning up.")
oontz.save()
for row in range(0, oontz.rows):
    note_off(row)

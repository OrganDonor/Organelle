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

# MIDI Channel numbers according to the console for each rank of pipes
RANK_4FT = 0
RANK_8FT = 1

root_bg = "#bbb"

deployed_mode = isfile("deployed.txt")      # Create this file to go full-screen, etc.


def initialize_MIDI_inout():
    """Initialize MIDI input and output ports using RTMIDI through mido

    We will go ahead and initialize all four of the input ports from the MIDIPLUS
    interface, plus the output port to the console.
    """

    # select rtmidi as our backend
    mido.set_backend('mido.backends.rtmidi')
    # print "Backend selected is %s " % mido.backend

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


inports, outport = initialize_MIDI_inout()

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
    for mynote in range(1, 128):
        outport.send(mido.Message('note_off', note=mynote, velocity=100, channel=RANK_4FT))
        outport.send(mido.Message('note_off', note=mynote, velocity=100, channel=RANK_8FT))


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


MODE_PASSTHRU, MODE_4FT, MODE_8FT, MODE_BOTH, MODE_MAX = range(5)
ModeButtons = [
    ("Thru", MODE_PASSTHRU),
    ("4' Rank", MODE_4FT),
    ("8' Rank", MODE_8FT),
    ("Both Ranks", MODE_BOTH),
    ("Max", MODE_MAX)
]
ModeButtonColor = '#ccc'
enabledColor = 'green'

MIN_SUBOCTAVE_NOTE = 13
MAX_OCTAVE_NOTE = 115
OCTAVE = 12


class MidiPortPassthru():
    """Object to handle configuration and passthrough of MIDI notes from an input port.

    The object knows its port, and creates a GUI to set how messages from that port
    are to be passed through to the console. It then handles messages according to
    the user settings.

    A MIDI port can be translated to console notes in a few different ways:
    * Thru mode -- all messages are passed thru on the channel they're received on
    * 4' Rank mode -- Note On and Note Off messages on any channel go to the 4' rank
    * 8' Rank mode -- Note On and Note Off messages on any channel go to the 8' rank
    * Both Ranks mode -- Note On and Note Off messages on any channel go to both ranks
    * Max mode -- Note On and Note Off messages on any channel go to both ranks, AND
        are tripled with octave and suboctave couplers.

    The controls could be more general, but it would be too complex on screen.
    """
    def __init__(self, port):
        self.port = port
        self.enabled = IntVar()
        self.enabled.set(1)             # defaults to enabled
        self.gui = Frame(root, height=110, width=800, bg=root_bg, bd=2, relief=SUNKEN)
        port_name = "MIDI In " + chr(ord(port.name[-1])+1)
        self.portlabel = Label(self.gui, text=port_name+':', font=("Helvetica", 24), fg='black', bg=root_bg)
        self.portlabel.pack(side=LEFT, padx=10)
        self.enabledButton = Checkbutton(self.gui, text="Enabled ", font=("Helvetica", 18), padx=0, pady=0, bg=enabledColor, activebackground=enabledColor, highlightbackground=enabledColor, variable=self.enabled, command=self._enabledCallback)
        self.enabledButton.pack(side=LEFT, padx=10)
        self.mode = IntVar()
        self.mode.set(MODE_PASSTHRU)
        self.modeButtons = []
        for text, value in ModeButtons:
            self.modeButtons.append(Radiobutton(self.gui, text=text, value=value, variable=self.mode, command=self._modeCallback, bg=ModeButtonColor, highlightcolor=ModeButtonColor, indicatoron=0, font=("Helvetica", 14), padx=5, pady=5))
        self.showing_buttons = False
        self._showButtons(True)

    def _showButtons(self, show):
        """Show or hide the secondary buttons on this widget.
        """
        if show and not self.showing_buttons:
            for button in self.modeButtons:
                button.pack(side=LEFT, padx=10)
            self.showing_buttons = True
        elif self.showing_buttons and not show:
            for button in self.modeButtons:
                button.pack_forget()
            self.showing_buttons = False

    def _enabledCallback(self):
        """Called when the enabled status of this MIDI port is changed.
        """
        if self.enabled.get() == 1:
            self.portlabel.config(fg='black')
            self.enabledButton.config(text="Enabled ", bg=enabledColor, activebackground=enabledColor, highlightbackground=enabledColor)
            self._showButtons(True)
        else:
            self.portlabel.config(fg='gray')
            self.enabledButton.config(text="Enable   ", bg=root_bg, activebackground=root_bg, highlightbackground=root_bg)
            self._showButtons(False)
            everything_off()        # just in case there are notes left playing
            # This disrupts the other channels, but to avoid that
            # we'd need to keep track of all the notes played. Ugh.

    def _modeCallback(self):
        """Called when the message handling mode of this MIDI port is changed.
        """
        everything_off()        # Just to make sure there are no orphaned notes being played

    def handle_message(self, msg):
        if self.enabled.get() == 1:
            mode = self.mode.get()
            if mode == MODE_PASSTHRU:
                outport.send(msg)       # Send the message on without thinking about it
            else:
                if 'note_on' in msg.type or 'note_off' in msg.type:     # discard other message types
                    if mode == MODE_4FT:
                        msg.channel = RANK_4FT
                        outport.send(msg)
                    elif mode == MODE_8FT:
                        msg.channel = RANK_8FT
                        outport.send(msg)
                    elif mode == MODE_BOTH:
                        msg.channel = RANK_4FT
                        outport.send(msg)
                        msg.channel = RANK_8FT
                        outport.send(msg)
                    elif mode == MODE_MAX:  # Send to both ranks with octave couplers
                        msg.channel = RANK_4FT
                        note = msg.note
                        outport.send(msg)
                        if note >= MIN_SUBOCTAVE_NOTE:
                            msg.note = note - OCTAVE
                            outport.send(msg)
                        if note <= MAX_OCTAVE_NOTE:
                            msg.note = note + OCTAVE
                            outport.send(msg)
                        msg.channel = RANK_8FT
                        if note >= MIN_SUBOCTAVE_NOTE:
                            msg.note = note - OCTAVE
                            outport.send(msg)
                        if note <= MAX_OCTAVE_NOTE:
                            msg.note = note + OCTAVE
                            outport.send(msg)
                    else:
                        print "Impossible mode."


configure_console(flagMidi=2)           # Make sure console allows access to both ranks

Label(root, text="Play From MIDI Devices", font=("Helvetica", 36), fg='red', bg=root_bg, padx=4, pady=2).pack()


# Associate each input port with a MidiPortPassthru and put their GUIs on the screen.
passthrus = []
for port in inports:
    passthru = MidiPortPassthru(port)
    passthrus.append(passthru)
    passthru.gui.pack(fill=BOTH, expand=1)

poll_midi()                 # kick off a frequent poll of the MIDI input port

if deployed_mode:
    root.attributes("-fullscreen", True)
else:
    # for debug, use the same screen size as the real screen, in a handy screen position.
    root.geometry("800x480+50+50")

root.mainloop()
print("Here we are cleaning up.")
everything_off()

#!/usr/bin/env python

"""Master program for the Organ Donor "Organelle"
This program is mainly responsible for monitoring the physical rotary switch
that allows users to select a major mode of operation for the Organelle.
When it detects that the switch has been moved, it asks the current program
to clean up and exit (by sending it a SIGUSR1 signal), waits for this to
complete, and launches the newly selected program.

Because Python GUI programs on the Raspberry Pi take a while to launch in
the best case, there is no way the rotary switch can be super responsive.
We'll have to settle for predictable but slow behavior. When the switch
position starts to change, we'll go ahead and signal the running program,
and continue to monitor the switch position. Once the switch reading has
been steady for a while, we will launch the new program (which might be
the same as the old program).

2015-05-25 Paul Williamson
2015-08-24 ptw  Reconstructing lost work: actually launch programs and signal them,
				and don't use the screen.
				Added syslog logging.
2015-08-25 ptw  Adjusted pin number to match as-built configuration.

"""

# Unfortunately, must run as root to use the built-in GPIO package.
import RPi.GPIO as GPIO
import sys, time
import subprocess
import syslog
import signal

syslog.openlog("organelle")
syslog.syslog(syslog.LOG_INFO, "Organelle supervisor started")

switch_steady_delay = 1.0  # seconds before the switch is considered stable
proc_exit_delay = 1.0		# seconds to allow the process to exit

# Pin numbers will follow the Broadcom SoC pin numbering
GPIO.setmode(GPIO.BCM)

# Mapping of pins onto programs and their command-line arguments
programs = {  4: ("./organelle.py", "p MIDI4x4_20:0 MIDIPLUS_1"),
             17: ("./organelle.py", "p MIDI4x4_20:1 MIDIPLUS_2"),
             27: ("./organelle.py", "p MIDI4x4_20:2 MIDIPLUS_3"),
             22: ("./organelle.py", "p MIDI4x4_20:3 MIDIPLUS_4"),
              5: ("./organelle.py", "4"),		# keyboards only
              6: ("./organelle.py", "4"),
             13: ("./organelle.py", "4"),
             19: ("./organelle.py", "2 8"),		# auto-play
             26: ("./organelle.py", "t"),		# theremin
             23: ("./organelle.py", "g")		# pitch game
              }

# Extract the list of GPIO pins from the program mapping.
pins = programs.keys()

# Function that reads all the pins into a dictionary.
def rotary_switch():
    return {x : GPIO.input(x) for x in pins}

# Given a dictionary levels containing the pin levels,
# and hoping that exactly one of them is 0 (because it's a rotary switch),
# return the pin number of the first one that's 0.
# If somehow none of the pins are grounded, return None.
def selected(levels):
    for pin,val in levels.iteritems():
        if val == 0:
            return pin
    return None

# Display a prompt in case the screen is unclaimed long enough to matter.
#def prompt():
#    sys.stderr.write("\x1b[2J\x1b[10;1H")    # row 10, column 1
#    print "Select mode using rotary switch"
def prompt():
	# we need not do anything to prompt; the wallpaper is the prompt.
	pass

# Set all pins as inputs with pullup, so we just ground a pin to activate.
for p in pins:
    GPIO.setup(p, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# The rotary switch monitoring goes on forever ...
while True:

    prompt()

    # Here we are in between programs. Wait for a constant switch reading.
    levels = rotary_switch()
    waitfor = time.time() + switch_steady_delay
    while time.time() < waitfor:
        newlevels = rotary_switch()
        if newlevels != levels:
            levels.update(newlevels)
            waitfor = time.time() + switch_steady_delay

    # OK, the switch has been steady for long enough. Launch that program!
    choice = selected(levels)
    if choice is None:
        continue
    (prog,arg) = programs[choice]

    # dummy launch for testing
    #print "Here we launch %s %s" % (prog,arg)
    proc = subprocess.Popen([prog]+arg.split())
    if not proc:
        syslog.syslog(syslog.LOG_ERROR, "Failed to launch " + prog + " " + arg)
        continue
    syslog.syslog(syslog.LOG_INFO, "Launched " + prog + " " + arg)
    
    # Program is running. Continue watching the rotary switch for changes.
    while levels == rotary_switch():
        time.sleep(0.100)

    # Switch touched! Ask the program to exit and wait for it to do so.
    proc.send_signal(signal.SIGUSR1)
    proc.wait()
#    waitfor = time.time() + proc_exit_delay
#    while time.time() < waitfor:
#        if proc.poll():
#	    syslog.syslog(syslog.LOG_INFO, "Normal exit")
#            break
#        time.sleep(0.100)
#    if not proc.poll():
#        # uh oh, program didn't exit as requested. Terminate with prejudice.
#        syslog.syslog(syslog.LOG_ERR, "Program failed to exit on request!")
#        proc.kill()
#        proc.wait()		# if kill() doesn't work, we're hung too.



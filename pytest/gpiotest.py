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

"""

# Unfortunately, must run as root to use the built-in GPIO package.
import RPi.GPIO as GPIO
import sys, time, signal, subprocess

switch_steady_delay = 1.0  # seconds before the switch is considered stable

# Pin numbers will follow the Broadcom SoC pin numbering
GPIO.setmode(GPIO.BCM)

# Mapping of pins onto programs and their command-line arguments
programs = {  4: ("/home/pi/organ/pytest/tkdemo.py", "4"),
             17: ("/home/pi/organ/pytest/tkdemo.py", "17"),
             27: ("/home/pi/organ/pytest/tkdemo.py", "27"),
             22: ("/home/pi/organ/pytest/tkdemo.py", "22"),
             18: ("/home/pi/organ/pytest/tkdemo.py", "18"),
             23: ("/home/pi/organ/pytest/tkdemo.py", "23"),
             24: ("/home/pi/organ/pytest/tkdemo.py", "24"),
             25: ("/home/pi/organ/pytest/tkdemo.py", "25"),
              8: ("/home/pi/organ/pytest/tkdemo.py", "8"),
              7: ("/home/pi/organ/pytest/tkdemo.py", "7")
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
def prompt():
    sys.stderr.write("\x1b[2J\x1b[10;1H")    # row 10, column 1
    print "Select mode using rotary switch"

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
    print "Here we launch %s %s" % (prog,arg)
    process = subprocess.Popen([prog, arg], cwd='/home/pi/organ/pytest')
    
    # Program is running. Continue watching the rotary switch for changes.
    while levels == rotary_switch():
        time.sleep(0.100)

    # Switch touched! Ask the program to exit and wait for it to do so.
    # dummy exit
    print "Here we exit the program."
    process.send_signal(signal.SIGUSR1)
    process.wait()


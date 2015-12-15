#!/usr/bin/env python

"""Rotary knob tester for Organ Donor Organelle
"""

# If we're running on Raspbian Jessie, we can use GPIO without being root!
# Otherwise, must run as root to use the built-in GPIO package.
import RPi.GPIO as GPIO
import sys
import time
import subprocess
import syslog
import signal

switch_steady_delay = 1.0  # seconds before the switch is considered stable

# Pin numbers will follow the Broadcom SoC pin numbering
GPIO.setmode(GPIO.BCM)

# Mapping of pins onto switch positions.
# 1 is at the bottom and positions go clockwise.
programs = {
         4: 1,
        17: 2,
        27: 3,
        22: 4,
         5: 5,
         6: 6,
        13: 7,
        19: 8,
        26: 9,
        23: 10
        }

# Extract the list of GPIO pins from the program mapping.
pins = programs.keys()

# Function that reads all the pins into a dictionary.
def rotary_switch():
    return {x: GPIO.input(x) for x in pins}


# Given a dictionary levels containing the pin levels,
# and hoping that exactly one of them is 0 (because it's a rotary switch),
# return the pin number of the first one that's 0.
# If somehow none of the pins are grounded, return None.
def selected(levels):
    for pin, val in levels.iteritems():
        if val == 0:
            return pin
    return None

# Set all pins as inputs with pullup, so we just ground a pin to activate.
for p in pins:
    GPIO.setup(p, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# The rotary switch monitoring goes on forever ...
while True:
    # Wait for a constant switch reading.
    levels = rotary_switch()
    waitfor = time.time() + switch_steady_delay
    while time.time() < waitfor:
        newlevels = rotary_switch()
        if newlevels != levels:
            levels.update(newlevels)
            waitfor = time.time() + switch_steady_delay

    # OK, the switch has been steady for long enough.
    choice = selected(levels)
    if choice is None:
        continue
    prog = programs[choice]

    print "Detected switch position", prog

    # Continue watching the rotary switch for changes.
    while levels == rotary_switch():
        time.sleep(0.100)
    
    print "Switch turning ..."

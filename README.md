# Organelle
Organ Donor Organelle Code. This is the user interface that the operator sees. It allows the operator to choose Organ Donor functions. 

* run-organelle.sh is a shell script intended to be run automatically at startup. Put it in the home directory for the auto-login user (pi).

* supervisor.py is a Python program that manages the major modes of the Organelle, as controlled by the rotary switch. It contains a table that maps each position of the rotary switch onto a program and its command line arguments. When the rotary switch is moved, it sends a SIGUSR1 signal to the currently running process, waits for it to exit cleanly, and then launches the program for the new switch position with the specified arguments.

* organelle.py is a Python program that implements certain Organelle behaviors. It can be run interactively for development, in which case it provides a simple pick-a-number text menu. Or, it can be run under the supervisor, by providing command line arguments. At present, this single program implements ALL the Organelle modes.

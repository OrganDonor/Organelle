# Organelle pytest
These files are test/demo code showing how to set up a framework (gpiotest.py) that
continuously scans the rotary switch connected to GPIO pins and launches one of
several full-screen GUI programs.

autostart goes in /etc/xdg/lxsession/LXDE-pi and is responsible for starting the framework

gamedemo.py is a sample GUI application that uses PyGame for the GUI.

tkdemo.py is a sample GUI application that uses TkInter for the GUI, which is somewhat
faster to launch than PyGame.

dummy.py is a sample non-GUI application that complies with the signaling convention
used by the framework to ask the application to exit.

Organelle Prompt Screen.jpg is an image to be used as desktop wallpaper, so that the
user sees a prompt when none of the GUI applications are visible (during transitions,
and when the rotary switch has no contacts grounded).
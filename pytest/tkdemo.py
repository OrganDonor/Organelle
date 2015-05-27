#! /usr/bin/env python

import sys, signal
from Tkinter import Tk, BOTH, Label
from ttk import Frame, Button, Style


class Example(Frame):
	def __init__(self, parent):
		Frame.__init__(self, parent)
		self.parent = parent
		self.initUI()

	def initUI(self):
		self.parent.title("Demo Program")
		self.style = Style()
		self.style.theme_use("default")

		self.pack(fill=BOTH, expand=1)

		# A real Organelle app would not have a Quit button
		# This is just for debug purposes.
		quitButton = Button(self, text="Quit", command=self.quit)
		quitButton.place(x=50,y=50)

		# A real Organelle app wouldn't use the command line
		# arguments, either. This just gives us a way to use
		# a single demo app to stand in for many apps.
		messageLabel = Label(self, text=sys.argv[1], fg="red", font=("Helvetica", 144))
		messageLabel.place(x=100, y=100)

def main():

	root = Tk()
	def kludge():
		root.after(100, kludge)
	root.after(100, kludge)

	def handle_sigusr1(signum, frame):
		root.quit()
	signal.signal(signal.SIGUSR1, handle_sigusr1)

	root.geometry("250x150+300+300")
	root.attributes("-fullscreen", True)
	app = Example(root)
	root.mainloop()
	print("Here we are cleaning up.")

if __name__ == '__main__':
	main()


#!/usr/bin/env python
#
# Sequence Recognizer for Organ Donor Organelle

import operator


class SequenceRecognizer():
    """Object that detects a specified magic sequence of events.

    Send events by calling step(). The call to step() that includes the final event
    of a successful sequence will include the call to the specified success_command().

    Call reset() to start over.

    Constructor args:
        parent          -- a Tkinter widget (any kind) that we can hang a timer on
        timeout         -- seconds allowed from first event to successful completion
        deadtime        -- seconds from first bad event until we start accepting events again
        success_command -- function to call on successful recognition of the entire sequence
        timeout_command -- functino to call when the timeout expires without success
        badevent_command-- function to call when an out-of-sequence event is passed.
        sequence        -- list of events (can be any object) to recognize
        match           -- function to compare an incoming event to an event from the sequence
                            (defaults to a standard equality test)

    """
    def __init__(self, *args, **kwargs):
        self.parent = kwargs.pop('parent')          # Tkinter widget we can hang timers on
        self.timeout = kwargs.pop('timeout', 5.0)   # seconds allowed for whole sequence
        self.sequence = kwargs.pop('sequence')      # list of events to receive in order
        self.success_command = kwargs.pop('success_command')        # function to call on completion
        self.timeout_command = kwargs.pop('timeout_command', lambda: None)
        self.badevent_command = kwargs.pop('badevent_command', lambda: None)
        self.match = kwargs.pop('match', operator.eq)   # function to test event matches
        self.deadtime = kwargs.pop('deadtime', 2.0)     # time after failure to reject events
        self.timer = None
        self.progress = 0
        self.rejecting = False

    def step(self, event):
        if self.rejecting:              # event during dead time: reset the deadtime timer
            if self.timer is not None:
                self.parent.after_cancel(self.timer)
            self.timer = self.parent.after(int(1000*self.deadtime), self.reset)
        elif self.match(event, self.sequence[self.progress]):   # test for a good event
            if self.progress == 0:      # meaning that we are starting a new attempt
                self.timer = self.parent.after(int(1000*self.timeout), self._expire)
            self.progress += 1
            if self.progress == len(self.sequence):     # meaning that we've completed the sequence
                self.success_command()
                self.reset()
        else:                           # out-of-sequence event
            if self.timer is not None:
                self.parent.after_cancel(self.timer)
            self.timer = self.parent.after(int(1000*self.deadtime), self.reset)
            self.rejecting = True
            self.badevent_command()

    def _expire(self):
        if self.timer is not None:
            self.parent.after_cancel(self.timer)
        self.parent.after(int(1000*self.deadtime), self.reset)
        self.rejecting = True
        self.timeout_command()

    def reset(self):
        if self.timer is not None:
            self.parent.after_cancel(self.timer)
            self.timer = None
        self.progress = 0
        self.rejecting = False


if __name__ == "__main__":
    from Tkinter import *

    def test_cmd():
        print "Success!"

    def to_cmd():
        print "Too slow!"

    def bad_cmd():
        print "Ugh."

    def test_entry1():
        magic.step(1)

    def test_entry2():
        magic.step(2)

    def test_entry3():
        magic.step(3)

    root = Tk()

    magic = SequenceRecognizer(parent=root, sequence=(1, 2, 3), timeout=5.0, success_command=test_cmd, timeout_command=to_cmd, badevent_command=bad_cmd)

    Button(root, text="1", command=test_entry1).pack()
    Button(root, text="2", command=test_entry2).pack()
    Button(root, text="3", command=test_entry3).pack()
    root.mainloop()

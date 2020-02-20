#!/usr/bin/env python3 
import time
import threading
import sounds

class WT(threading.Thread):
    """
    A worker thread that polls the vlc api for current position and calls options as necessary

    Ask the thread to stop by calling its join() method.
    """

    def __init__(self, song):
        super(WT, self).__init__()
        self.song = song
        self.stoprequest = threading.Event()
        self.last = 0

        self.current = 0
        self.difference = 0.0025
        # self.difference = 0.005

    def run(self):
        # As long as we weren't asked to stop, try to take new tasks from the
        # queue. The tasks are taken with a blocking 'get', so no CPU
        # cycles are wasted while waiting.
        # Also, 'get' is given a timeout, so stoprequest is always checked,
        # even if there's nothing in the queue.
        # difference - this is a 'magic' number to give leaway to testing to each
        # mark relative to the current time. because there could be variation 
        # between the polled time from vlc and the current mark, it needs a 
        # cushion to test against. This needs to be converted to a algorith 
        # relative to the length of the file.

        while not self.stoprequest.isSet():
            self.current = self.song.song.get_position()
            if abs(self.current - self.last) > 0:
                try:
                    for itr,each in enumerate(self.song.state.marks):
                        if abs(self.current - self.last) < self.difference: 
                            if self.song.is_editing:
                                # self.song.log("{}:{}".format(self.last <= each.end, each.end <= self.current))
                                res = self.last - self.difference <= each.end <= self.current + self.difference
                                if res:
                                    self.song.log(res)
                                try:
                                    if self.last <= each.start <= self.current:
                                        self.song.print_to_screen('Block {} start'.format(itr + 1))
                                        if each.start != 0:
                                            self.song.startSound()
                                    if self.last <= each.end <= self.current:
                                        self.song.print_to_screen('Block {} end'.format(itr + 1))
                                        self.song.endSound()
                                except Exception as ex:
                                    self.song.log(ex)
                            else:
                                if self.last <= each.start <= self.current:
                                    # keep the marks iterator up to date on the location in the file
                                    self.song.markItr = itr
                                    self.song.updateIters()
                                    self.song.song.set_position(each.end)
                                    self.song.print_to_screen('Block {}'.format(itr + 1))
                                    self.song.song.pause()
                                    time.sleep(1)
                                    self.song.song.play()

                    
                    
                except Exception as e:
                    self.song.log(e)
                self.last = self.current

    # used to shut down the worker thread
    def join(self, timeout=None):
        self.stoprequest.set()
        super(WT, self).join(timeout)
#!/usr/bin/env python3 
import datetime
import time
import threading
import sounds

class WorkerThread(threading.Thread):
    """
    A worker thread that polls the vlc api for current position and calls options as necessary

    Ask the thread to stop by calling its join() method.
    """

    def __init__(self, song):
        super(WorkerThread, self).__init__()
        self.song = song
        self.stoprequest = threading.Event()
        self.last = 0

        self.current = 0
        self.difference = 0.0025

    def log(self, input):
        input = str(input)
        with open("log.txt", "a") as myfile:
            string = datetime.datetime.fromtimestamp(
                time.time()).strftime('%Y-%m-%d %H:%M:%S')
            string = string + ' - ' + input + '\n'
            myfile.write(string)

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
                        if abs(self.current- self.last) < self.difference : 
                            if self.last <= each.start <= self.current:
                                self.song.song.pause()
                                self.song.print_to_screen("Block {} start".format(itr+1))
                                time.sleep(1)
                                # sounds.mark_start_sound(self.song.volume)
                                self.song.song.play()
                            elif self.last <= each.end <= self.current:
                                self.song.print_to_screen("Block {} end".format(itr+1))
                                # sounds.mark_end_sound(self.song.volume)
                                self.song.song.pause()
                                time.sleep(1)
                                self.song.song.play()

                    
                    self.last = self.current
                    # self.song.window.refresh()
                except Exception as e:
                    self.log(e)

    def timeStamp(self,duration,current):
        out = duration * current
        try:
            millis = int(out)
            seconds = round((millis/1000) % 60, 3)
            minutes = (millis/(1000*60)) % 60
            minutes = int(minutes)
            hours = int((millis/(1000*60*60)) % 24)
            time = ""
            if hours >= 1:
                time = "{} hours ".format(hours)
            if minutes >= 1:
                time += "{} minutes ".format(minutes)
            if seconds >= 1:
                time  += "{} seconds".format(seconds)
            return time
        except Exception as ex:
            self.log(ex)

    # used to shut down the worker thread
    def join(self, timeout=None):
        self.stoprequest.set()
        super(WorkerThread, self).join(timeout)
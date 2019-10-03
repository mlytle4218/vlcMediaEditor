#!/usr/bin/env python3 
import datetime
import time
import threading

class WorkerThread(threading.Thread):
    """ A worker thread that takes directory names from a queue, finds all
        files in them recursively and reports the result.

        Input is done by placing directory names (as strings) into the
        Queue passed in dir_q.

        Output is done by placing tuples into the Queue passed in result_q.
        Each tuple is (thread name, dirname, [list of files]).

        Ask the thread to stop by calling its join() method.
    """

    def __init__(self, song):
        super(WorkerThread, self).__init__()
        self.song = song
        self.stoprequest = threading.Event()
        self.last = 0

        self.current = 0
        self.difference = 0

    def log(self, input):
        input = str(input)
        with open("test.txt", "a") as myfile:
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
        while not self.stoprequest.isSet():
            self.current = self.song.song.get_position()
            if abs(self.current - self.last) > 0:
                try:
                    cnt = 0
                    for each in self.song.marks:
                        if self.song.now_okay and each.start > (self.current - (self.difference)) and each.start < (self.current + (self.difference)):
                            # self.song.load_and_play(self.song.asc)
                            self.song.mark_start_sound()
                        if self.song.now_okay and each.end > (self.current - (self.difference)) and each.end < (self.current + (self.difference)):
                            # self.song.load_and_play(self.song.des)
                            self.song.mark_end_sound()
                    self.song.window.clear()
                    self.song.window.addstr(cnt, 0, str(self.current))
                    cnt += 1
                    out = self.song.duration * self.current

                    millis = int(out)
                    seconds = (millis/1000) % 60
                    minutes = (millis/(1000*60)) % 60
                    minutes = int(minutes)
                    hours = (millis/(1000*60*60)) % 24
                    time = ""
                    if hours >= 1:
                        time = "{}:{:02d}:{:02d}".format(
                            hours, minutes, seconds)
                    else:
                        time = "{}:{:02.3f}".format(minutes, seconds)

                    self.song.window.addstr(cnt, 0, str(time))
                    cnt += 1
                    for each in self.song.marks:
                        self.song.window.addstr(cnt, 0, str(each.start))
                        cnt += 1
                        self.song.window.addstr(cnt, 0, str(each.end))
                        cnt += 1
                    self.difference = (
                        125 / self.song.duration) * self.song.rate

                    self.last = self.current
                    self.song.window.refresh()
                except Exception as e:
                    # pass
                    self.log(e)

    def join(self, timeout=None):
        self.stoprequest.set()
        super(WorkerThread, self).join(timeout)
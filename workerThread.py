#!/usr/bin/env python3 
import datetime
import time
import threading
import sounds

class WorkerThread(threading.Thread):
    """ A worker thread that polls the vlc api for current position 
        and calls options as necessary

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

    def print_out_time(self):
        self.song.window.clear()
        time = self.timeStamp(self.song.duration, self.current)
        self.song.window.addstr(0,0,time)

    def run(self):
        # As long as we weren't asked to stop, try to take new tasks from the
        # queue. The tasks are taken with a blocking 'get', so no CPU
        # cycles are wasted while waiting.
        # Also, 'get' is given a timeout, so stoprequest is always checked,
        # even if there's nothing in the queue.
        while not self.stoprequest.isSet():
            self.current = self.song.song.get_position()
            if abs(self.current - self.last) > 0:
                # self.log('bob')
                try:
                    # cnt = 0
                    for each in self.song.marks:
                        if each.start > (self.current - (self.difference)) and each.start < (self.current + (self.difference)):
                        # if self.song.now_okay and each.start > (self.current - (self.difference)) and each.start < (self.current + (self.difference)):
                            sounds.mark_start_sound(self.song.volume)

                        if each.end > (self.current - (self.difference)) and each.end < (self.current + (self.difference)):
                        # if self.song.now_okay and each.end > (self.current - (self.difference)) and each.end < (self.current + (self.difference)):
                            sounds.mark_end_sound(self.song.volume)

                    # self.song.window.clear()
                    #print out the current vlc decimal position
                    # self.song.window.addstr(cnt, 0, str(self.current))

                    # print out the current timeStamp of position
                    # cnt += 1
                    # time = self.timeStamp(self.song.duration, self.current)
                    # self.song.window.addstr(cnt, 0, str(time))






                    #print out each of the marks start and stop
                    # cnt += 1
                    # for each in self.song.marks:
                    #     self.song.window.addstr(cnt, 0, str(each.start))
                    #     cnt += 1
                    #     self.song.window.addstr(cnt, 0, str(each.end))
                    #     cnt += 1








                    # update the difference - this is a 'magic' number to give leaway to testing to each
                    # mark relative to the current time. because there could be variation between the polled
                    # time from vlc and the current mark, it needs a cushion to test against. This needs to be converted
                    # to a algorith relative to the length of the file.
                    self.difference = (
                        125 / self.song.duration) * self.song.rate

                    self.last = self.current
                    self.song.window.refresh()
                except Exception as e:
                    self.log(e)

    def timeStamp(self,duration,current):
        out = duration * current

        millis = int(out)
        seconds = int((millis/1000) % 60)
        minutes = (millis/(1000*60)) % 60
        minutes = int(minutes)
        hours = int((millis/(1000*60*60)) % 24)
        time = ""
        # if hours >= 1:
        #     time = "{} hours {} minutes {}  seconds".format(hours, minutes, seconds)
        # else:
        #     time = "{} minutes {} seconds".format(minutes, seconds)
        if hours >= 1:
            time = "{} hours ".format(hours)
        if minutes >= 1:
            time += "{} minutes ".format(minutes)
        if seconds >= 1:
            time  += "{} seconds".format(seconds)
        return time

    # used to shut down the worker thread
    def join(self, timeout=None):
        self.stoprequest.set()
        super(WorkerThread, self).join(timeout)
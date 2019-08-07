#!/usr/bin/env python3
import vlc
import sys
import curses
from curses import panel
import datetime, time
import threading
import math
from operator import itemgetter 
from playsound import playsound

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


        


    def run(self):
        # As long as we weren't asked to stop, try to take new tasks from the
        # queue. The tasks are taken with a blocking 'get', so no CPU
        # cycles are wasted while waiting.
        # Also, 'get' is given a timeout, so stoprequest is always checked,
        # even if there's nothing in the queue.
        while not self.stoprequest.isSet():
            self.current = self.song.song.get_position()
            if abs(self.current - self.last) > 0:
                cnt = 0 
                for each in self.song.marks:
                    if self.song.now_okay and each.start > ( self.current - ( self.difference ) ) and each.start < ( self.current + ( self.difference ) ):
                        self.song.load_and_play(self.song.asc)
                    if self.song.now_okay and each.end > ( self.current - ( self.difference ) ) and each.end < ( self.current + ( self.difference ) ):
                        self.song.load_and_play(self.song.des)
                self.song.window.clear()
                self.song.window.addstr(cnt, 0, str( self.current ))
                cnt+=1
                out = self.song.duration * self.current

                millis = int(out)
                seconds=(millis/1000)%60
                minutes=(millis/(1000*60))%60
                minutes = int(minutes)
                hours=(millis/(1000*60*60))%24
                time = ""
                if hours >= 1:
                    time = "{}:{:02d}:{:02d}".format(hours, minutes, seconds)
                else:
                    time = "{}:{:02.3f}".format(minutes, seconds)

                self.song.window.addstr(cnt, 0, str( time ))
                cnt+=1
                for each in self.song.marks:
                    self.song.window.addstr(cnt, 0, str( each.start ))
                    cnt +=1 
                    self.song.window.addstr(cnt, 0, str( each.end ))
                    cnt+=1
                self.difference = (125 / self.song.duration) * self.song.rate

                self.last = self.current
                self.song.window.refresh()

    def join(self, timeout=None):
        self.stoprequest.set()
        super(WorkerThread, self).join(timeout)


class Mark():
    def __init__(self):
        self.start = -1
        self.end = -1

    def __str__(self):
        return str( self.start ) + ":" + str( self.end )
    
    def __getitem__(self, item):
         return self.start

    def reset(self):
        if self.start > self.end:
            temp = self.start
            self.start = self.end
            self.end = temp



class MyApp(object):   
    def update_rate(self, amount):
        self.rate += amount
        self.song.set_rate( self.rate )

    def log(self, input):
        input = str( input )
        with open("test.txt", "a") as myfile:
            string=datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            string=string+ ' - ' +input + '\n'
            myfile.write(string)


    def load_and_play(self, input_file):
        playsound(input_file)

    def milliseconds_to_hms(self, milliseconds):
        millis = int(milliseconds * self.duration)
        seconds=(millis/1000)%60
        part_of_seconds = int((seconds - math.floor(seconds)) * 1000)
        seconds = int(seconds)
        minutes=(millis/(1000*60))%60
        minutes = int(minutes)
        hours=(millis/(1000*60*60))%24
        hours = int(hours)
        time = ""
        if hours >= 1:
            time = "{}:{:02d}:{:02d}.{}".format(hours, minutes, seconds, part_of_seconds)
        else:
            time = "{}:{:02d}.{}".format(minutes, seconds, part_of_seconds)

        return time

         


    def __init__(self, stdscreen): 
        self.rate = 1 
        self.position = 0
        self.is_marking = False   
        self.marks = []
        self.markItr = 0
        self.errorSound = 'error.wav'
        self.asc = "assending.wav"
        self.des = "desending.wav"
        self.current_mark = None
        self.now_okay = True

        


        self.screen = stdscreen 
                                          
        curses.curs_set(0)

        self.height,self.width = stdscreen.getmaxyx()                   
        self.window = stdscreen.subwin(0,0)                                  
        self.window.keypad(1)                                                
        self.panel = panel.new_panel(self.window)                            
        self.panel.hide()                                                  
        panel.update_panels()                                                

        self.position = 0
        self.panel.top()                                                     
        self.panel.show()                                                    
        self.window.clear()     
        n = Mark()
        n.start = 0.015
        n.end = 0.035
        self.marks.append(n)

        sys.argv.pop(0)
        if sys.argv:
            self.instance = vlc.Instance(('--no-video'))
            self.song = self.instance.media_player_new()
            self.media = self.instance.media_new(sys.argv[0])
            self.song.set_media(self.media)
            self.song.play()
            self.media.parse()
            self.poll_thread = WorkerThread(self)
            self.poll_thread.start()

            

            self.duration = self.media.get_duration()                             

        while True:
            self.position = self.song.get_position()                                            
            self.window.refresh()                                            
            curses.doupdate()                                                                 

            key = self.window.getch()                            
                          
            # Speeds up the playback
            if key == curses.KEY_UP:
                self.update_rate(0.25)
                
            # Slows down the playback
            elif key == curses.KEY_DOWN:
                self.update_rate(-0.25)

            elif key == curses.KEY_LEFT:
                cur_pos = self.song.get_position()
                cur_sec = round( cur_pos * self.duration ) - 5000
                new_pos = cur_sec / self.duration
                self.now_okay = False
                self.song.set_position(new_pos)
                self.song.play()
                self.now_okay = True

            elif key == curses.KEY_RIGHT:
                cur_pos = self.song.get_position()
                cur_sec = round( cur_pos * self.duration ) + 5000
                new_pos = cur_sec / self.duration
                self.now_okay = False
                self.song.set_position(new_pos)
                self.song.play()
                self.now_okay = True
            
            # pauses and plays the media
            elif key == ord(' '):
                if self.song.is_playing:
                    self.song.pause()
                else:
                    self.song.play()

            # Testing sound overlay
            elif key == ord('w'):
                self.load_and_play(self.asc)

            # Create a new mark
            elif key == ord('n'):
                # if there is not an active mark, make one
                if self.current_mark:
                    self.load_and_play(self.errorSound)
                else: 
                    self.current_mark = Mark()

            # Saves a current mark
            elif key == ord('s'):
                # check to make sure there is an active mark and that both the beginning and end have 
                # been entered
                if self.current_mark and self.current_mark.start != -1 and self.current_mark.end != -1:
                        self.current_mark.reset()
                        self.marks.append(self.current_mark)
                        self.markItr = len( self.marks ) - 1
                        self.current_mark = None
                        self.marks = sorted(self.marks, key=itemgetter('start'))
                else:
                    self.load_and_play(self.errorSound)


            # Record the beginning of the mark
            elif key == ord('b'):
                #make sure there is and active mark
                if self.current_mark:
                    begin_position_check = self.song.get_position()
                    okay = True
                    # cycle through the saved marks and make sure the current position does 
                    # overlap with them
                    for each in self.marks:
                        if begin_position_check > each.start and begin_position_check < each.end:
                            okay =  False
                    if okay:
                        self.current_mark.start = begin_position_check
                    else:
                        self.log('overlap')
                        self.load_and_play(self.errorSound)
                else:
                    self.log('no current_mark')
                    self.load_and_play(self.errorSound)


            # Record the end of the mark
            elif key == ord('e'):
                # make sure there is an active mark
                if self.current_mark:
                    begin_position_check = self.song.get_position()
                    okay = True
                    # cycle through the saved marks and make sure the current position does 
                    # overlap with them
                    for each in self.marks:
                        if begin_position_check > each.start and begin_position_check < each.end:
                            okay =  False
                    if okay:
                        self.current_mark.end = begin_position_check
                    else:
                        self.load_and_play(self.errorSound)
                else:
                    self.load_and_play(self.errorSound)

            # Testing the markIter
            elif key == ord('p'):
                temp = self.marks[self.markItr]
                self.log( temp )

            elif key == ord('m'):
                for each in self.marks:
                    self.log( self.milliseconds_to_hms(each.start) )
                    self.log( self.milliseconds_to_hms(each.end) )
                
            # Quit the program
            elif key == ord('q'):
                self.poll_thread.join()
                break


        self.window.clear()                                                  
        self.panel.hide()                                                    
        panel.update_panels()                                                
        curses.doupdate()                                

if __name__ == '__main__':                                                       
    curses.wrapper(MyApp)
#!/usr/bin/env python3
import vlc
import sys
import curses
from curses import panel
import datetime, time
import threading
import math

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

    def run(self):
        # As long as we weren't asked to stop, try to take new tasks from the
        # queue. The tasks are taken with a blocking 'get', so no CPU
        # cycles are wasted while waiting.
        # Also, 'get' is given a timeout, so stoprequest is always checked,
        # even if there's nothing in the queue.
        while not self.stoprequest.isSet():
            self.current = self.song.song.get_position()
            if abs(self.current - self.last) > 0:
                self.song.window.addstr(0, 0, str( self.song.song.get_position() ))
                # with open("test.txt", "a") as myfile:
                #     string=datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                #     string=string+ ' - ' + str( self.song.song.get_position() ) + '\n'
                #     myfile.write(string)
                self.last = self.current
            # print('hi')
            # self.song.window.addstr(1, 1, str( self.song.media.get_duration() ))
            # self.song.window.addstr(1,1, str( self.out ))
            # self.out += 1
            # try:
            #     dirname = self.dir_q.get(True, 0.05)
            #     filenames = list(self._files_in_dir(dirname))
            #     self.result_q.put((self.name, dirname, filenames))
            # except Queue.Empty:
            #     continue

    def join(self, timeout=None):
        self.stoprequest.set()
        super(WorkerThread, self).join(timeout)


class Mark():
    def __init__(self):
        self.start = 0
        self.end = 0

    def __str__(self):
        return str( self.start ) + ":" + str( self.end )

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
        asc_instance = vlc.Instance(('--no-video'))
        asc = asc_instance.media_player_new()
        asc_media = asc_instance.media_new(input_file)
        asc.set_media(asc_media)
        asc.play()

         


    def __init__(self, stdscreen): 
        self.rate = 1 
        self.position = 0
        self.is_marking = False   
        self.marks = []
        self.markItr = 0
        self.errorSound = 'error.wav'
        self.asc = "assending.wav"
        self.des = "desending.wav"

        


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
            # self.window.addstr(1, 1, str( self.song.get_position() ))     
            # self.log(self.song.get_position())                                              
            self.window.refresh()                                            
            curses.doupdate()                                                                 

            key = self.window.getch()
            # self.log('now')                             
                          
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
                self.song.set_position(new_pos)
                self.song.play()

            elif key == curses.KEY_RIGHT:
                cur_pos = self.song.get_position()
                cur_sec = round( cur_pos * self.duration ) + 5000
                new_pos = cur_sec / self.duration
                self.log( new_pos )
                self.song.set_position(new_pos)
                self.song.play()

            # Starts the media
            elif key == ord('s'):
                if self.song.is_playing:
                    self.song.pause()
                    self.song.set_position(0)
            
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
                try: 
                    self.marks[self.markItr].reset()
                except IndexError:
                    pass
                self.marks.append(Mark())
                self.markItr = len( self.marks ) - 1

            # Record the beginning of the mark
            elif key == ord('b'):
                try:
                    self.marks[self.markItr].start = self.song.get_position()
                except IndexError:
                    self.load_and_play(self.errorSound)

            # Record the end of the mark
            elif key == ord('e'):
                try: 
                    self.marks[self.markItr].end = self.song.get_position()
                except IndexError:
                    self.load_and_play(self.errorSound)

            # Testing the markIter
            elif key == ord('p'):
                temp = self.marks[self.markItr]
                self.log( temp )
                
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
#!/usr/bin/env python3
import vlc
import sys
import curses
from curses import panel
from playsound import playsound
import datetime, time

class Mark():
    def __init__(self):
        self.start = 0
        self.end = 0

    def __str__(self):
        return str( self.start ) + ":" + str( self.end )
    
    def start(self, start):
        self.start = start
    
    def end(self, end):
        self.end = end

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
         


    def __init__(self, stdscreen): 
        self.rate = 1 
        self.position = 0
        self.is_marking = False   
        self.marks = []
        self.markItr = 0
        self.errorSound = 'lower.wav'



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
            self.instance = vlc.Instance()
            self.song = self.instance.media_player_new()
            self.media = self.instance.media_new(sys.argv[0])
            self.song.set_media(self.media)
            self.song.play()
            self.media.parse()

            self.duration = self.media.get_duration()                             

        while True:
            self.position = self.song.get_position()                                                       
            self.window.refresh()                                            
            curses.doupdate()                                                                 

            key = self.window.getch()                                        
                          

            if key == curses.KEY_UP:
                self.update_rate(-0.25)
                
            elif key == curses.KEY_DOWN:
                self.update_rate(0.25)

            elif key == ord('s'):
                if self.song.is_playing:
                    self.song.pause()
                    self.song.set_position(0)
            
            elif key == ord(' '):
                if self.song.is_playing:
                    self.song.pause()
                else:
                    self.song.play()

            elif key == ord('w'):
                playsound('lower.wav')

            elif key == ord('n'):
                try: 
                    self.marks[self.markItr].reset()
                except IndexError:
                    pass
                self.marks.append(Mark())
                self.markItr = len( self.marks ) - 1

            elif key == ord('b'):
                try:
                    self.marks[self.markItr].start = self.song.get_position()
                except IndexError:
                    playsound(self.errorSound)

            elif key == ord('e'):
                try: 
                    self.marks[self.markItr].end = self.song.get_position()
                except IndexError:
                    playsound(self.errorSound)

            elif key == ord('p'):
                temp = self.marks[self.markItr]
                self.log( temp )
                
            elif key == ord('q'):
                break


        self.window.clear()                                                  
        self.panel.hide()                                                    
        panel.update_panels()                                                
        curses.doupdate()                                

if __name__ == '__main__':                                                       
    curses.wrapper(MyApp)
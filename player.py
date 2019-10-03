#!/usr/bin/env python3
import vlc
import sys
import curses
from curses import panel
import datetime
import time
import threading
import math
from operator import itemgetter
from ctypes import *

import subprocess
import os

import pyaudio
import struct

from workerThread import WorkerThread
from mark import Mark

def py_error_handler(filename, line, function, err, fmt):
    pass
    with open("test.txt", "a") as myfile:
        string = datetime.datetime.fromtimestamp(
            time.time()).strftime('%Y-%m-%d %H:%M:%S')
        string = string + ' - ' + str(filename) + '\n'
        myfile.write(string)


class MyApp(object):
    ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)
    
        
    c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)
    asound = cdll.LoadLibrary('libasound.so')
    asound.snd_lib_error_set_handler(c_error_handler)

    def data_for_freq(self, frequency: float, time: float = None):
        """get frames for a fixed frequency for a specified time or
        number of frames, if frame_count is specified, the specified
        time is ignored"""
        frame_count = int(self.RATE * time)

        remainder_frames = frame_count % self.RATE
        wavedata = []

        for i in range(frame_count):
            a = self.RATE / frequency  # number of frames per wave
            b = i / a
            # explanation for b
            # considering one wave, what part of the wave should this be
            # if we graph the sine wave in a
            # displacement vs i graph for the particle
            # where 0 is the beginning of the sine wave and
            # 1 the end of the sine wave
            # which part is "i" is denoted by b
            # for clarity you might use
            # though this is redundant since math.sin is a looping function
            # b = b - int(b)

            c = b * (2 * math.pi)
            # explanation for c
            # now we map b to between 0 and 2*math.PI
            # since 0 - 2*PI, 2*PI - 4*PI, ...
            # are the repeating domains of the sin wave (so the decimal values will
            # also be mapped accordingly,
            # and the integral values will be multiplied
            # by 2*PI and since sin(n*2*PI) is zero where n is an integer)
            d = math.sin(c) * 32767
            e = int(d)
            wavedata.append(e)

        for i in range(remainder_frames):
            wavedata.append(0)

        number_of_bytes = str(len(wavedata))
        wavedata = struct.pack(number_of_bytes + 'h', *wavedata)

        return wavedata

    # def mark_start_sound(self, frequency: float, time: float):
    def error_sound(self):
        frequency = 400.0
        time = 0.3
        """
        play an error tone
        """
        frames = self.data_for_freq(frequency, time)

        stream = pyaudio.PyAudio().open(format=self.FORMAT, channels=self.CHANNELS,
                                 rate=self.RATE, output=True)
        stream.write(frames)
        stream.stop_stream()
        stream.close()

    def mark_start_sound(self):
        frequency = 400.0
        time = 0.3
        """
        play a set of tones going up
        """
        number = 5
        frames_total = bytes()
        for itr in range(number):
            frames = self.data_for_freq(frequency*(1+(itr/10)), time/number)
            frames_total += frames
        # self.log(frames_total)

        stream = pyaudio.PyAudio().open(format=self.FORMAT, channels=self.CHANNELS,
                                 rate=self.RATE, output=True)
        stream.write(frames_total)
        stream.stop_stream()
        stream.close()

    def mark_end_sound(self):
        frequency = 400.0
        time = 0.3
        """
        play a set of quick tones going down
        """
        number = 5
        frames_total = bytes()
        for itr in range(number):
            freq = frequency*( 1 - (itr/10) )
            split = time/number

            frames = self.data_for_freq(freq, split)
            frames_total += frames
        stream = pyaudio.PyAudio().open(format=self.FORMAT, channels=self.CHANNELS,
                                 rate=self.RATE, output=True)
        stream.write(frames_total)
        stream.stop_stream()
        stream.close()

    def update_rate(self, amount):
        self.rate += amount
        self.song.set_rate(self.rate )

    def log(self, input):
        input = str(input )
        with open("test.txt", "a") as myfile:
            string = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            string = string + ' - ' + input + '\n'
            myfile.write(string)

    def mark_to_milliseconds(self, mark):
        milliseconds = int(self.duration * mark)
        return milliseconds

    def milliseconds_to_hms(self, millis):
        millis = int(millis)
        seconds = (millis/1000)%60
        part_of_seconds = int((seconds - math.floor(seconds)) * 1000)
        seconds = int(seconds)
        minutes = (millis/(1000*60))%60
        minutes = int(minutes)
        hours = (millis/(1000*60*60))%24
        time = ''
        if hours >= 1 and minutes >= 1:
            time = ("{}:{:02d}:{:02d}.{}".format(
                hours, minutes, seconds, part_of_seconds))
        elif minutes >= 1:
            time = ("{:02d}:{:02d}.{}".format(
                minutes, seconds, part_of_seconds))
        else:
            time = ("{:02d}.{}".format(seconds, part_of_seconds))

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
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 2
        self.RATE = 44100




        self.screen = stdscreen

        curses.curs_set(0)

        self.height, self.width = stdscreen.getmaxyx()                   
        self.window = stdscreen.subwin(0, 0)                                  
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
        n = Mark()
        n.start = 0.125
        n.end = 0.268
        self.marks.append(n)

        sys.argv.pop(0)
        if sys.argv:
            self.original_file = sys.argv[0]
            self.instance = vlc.Instance(('--no-video'))
            self.song = self.instance.media_player_new()
            self.media = self.instance.media_new(self.original_file)
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
                cur_sec = round(cur_pos * self.duration ) - 5000
                new_pos = cur_sec / self.duration
                self.now_okay = False
                if new_pos < 0:
                    new_pos = 0
                self.song.set_position(new_pos)
                self.song.play()
                self.now_okay = True

            elif key == curses.KEY_RIGHT:
                cur_pos = self.song.get_position()
                cur_sec = round(cur_pos * self.duration ) + 5000
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
                    
            # Create a new mark
            elif key == ord('n'):
                # if there is not an active mark, make one
                if self.current_mark:
                    self.error_sound()
                else:
                    self.current_mark = Mark()

            # Saves a current mark
            elif key == ord('s'):
                # check to make sure there is an active mark and that both the beginning and end have
                # been entered
                if self.current_mark and self.current_mark.start != -1 and self.current_mark.end != -1:
                    self.current_mark.reset()
                    self.marks.append(self.current_mark)
                    self.markItr = len(self.marks ) - 1
                    self.current_mark = None
                    self.marks = sorted(self.marks, key=itemgetter('start'))
                else:
                    self.error_sound()

            # Record the beginning of the mark
            elif key == ord('b'):
                # make sure there is and active mark
                if self.current_mark:
                    begin_position_check = self.song.get_position()
                    okay = True
                    # cycle through the saved marks and make sure the current position does
                    # overlap with them
                    for each in self.marks:
                        if begin_position_check > each.start and begin_position_check < each.end:
                            okay = False
                    if okay:
                        self.current_mark.start = begin_position_check
                    else:
                        self.log('overlap')
                        self.error_sound()
                else:
                    self.log('no current_mark')
                    self.error_sound()

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
                            okay = False
                    if okay:
                        self.current_mark.end = begin_position_check
                    else:
                        self.error_sound()
                else:
                    self.error_sound()

            # Testing the markIter
            elif key == ord('p'):
                temp = self.marks[self.markItr]
                self.log(temp )

            # elif key == ord('m'):
            #     for each in self.marks:
            #         self.log( self.milliseconds_to_hms(each.start) )
            #         self.log( self.milliseconds_to_hms(each.end) )

            # Quit the program
            elif key == ord('q'):
                self.poll_thread.join()
                break

            elif key == ord('o'):
                self.poll_thread.join()
                self.song.stop()

                filename, file_extension = os.path.splitext(self.original_file)
                self.temp_file = filename + "-old" + file_extension
                os.rename(self.original_file, self.temp_file)
                command = ['ffmpeg', "-loglevel","error",'-i',self.temp_file]

                select = """ffmpeg -i {} -vf "select='""".format(
                    self.temp_file)
                select = "select='"
                aselect = "aselect='"
                last = 0
                for each in self.marks:
                    temp = each.end
                    each.end = each.start
                    each.start = last
                    last = temp
                n = Mark()
                n.start = last
                self.log( str( int( self.duration / 1000 ) ) )
                n.end = 1
                self.marks.append(n)
                for i, each in enumerate(self.marks):
                    if i == 0:
                        select += """between(t,{},{})""".format(
                            int(  self.mark_to_milliseconds( each.start ) / 1000) ,
                            int(  self.mark_to_milliseconds( each.end ) / 1000) ,
                        )
                        aselect += """between(t,{},{})""".format(
                            int(  self.mark_to_milliseconds( each.start ) / 1000) ,
                            int(  self.mark_to_milliseconds( each.end ) / 1000) ,
                        )
                    else:
                        select += """+between(t,{},{})""".format(
                            int(  self.mark_to_milliseconds( each.start ) / 1000) ,
                            int(  self.mark_to_milliseconds( each.end ) / 1000) ,
                        )
                        aselect += """+between(t,{},{})""".format(
                            int(  self.mark_to_milliseconds( each.start ) / 1000) ,
                            int(  self.mark_to_milliseconds( each.end ) / 1000) ,
                        )

                select += """',setpts=N/FRAME_RATE/TB """
                aselect += """',asetpts=N/SR/TB"""
                command.append('-vf')
                command.append(select)
                command.append('-af')
                command.append(aselect)
                command.append(self.original_file)
                self.command = command
                self.log(command )
                subprocess.call(command)
                os.remove(self.temp_file)
                break



        self.window.clear()
        self.panel.hide()
        panel.update_panels()
        curses.doupdate()


if __name__ == '__main__':
    curses.wrapper(MyApp)

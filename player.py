#!/usr/bin/env python3
import vlc
import sys
import curses
from curses import panel
import datetime
import time
from operator import itemgetter
from ctypes import (CFUNCTYPE, c_char_p, c_int, cdll)
# from ctypes import *
import ctypes
import subprocess
import os


from workerThread import WorkerThread
from mark import Mark
import sounds
import config


def py_error_handler(filename, line, function, err, fmt):
    pass
    with open("test.txt", "a") as myfile:
        timestamp = datetime.datetime.fromtimestamp(
            time.time()).strftime('%Y-%m-%d %H:%M:%S')
        # string = string + ' - ' + str(fmt) + '\n'
        string = "{}:{}:{}:{}:{}:{}".format(
            timestamp, filename, line, function, err, fmt)
        myfile.write(string)


class MyApp(object):
    ERROR_HANDLER_FUNC = CFUNCTYPE(
        None, c_char_p, c_int, c_char_p, c_int, c_char_p)

    c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)
    asound = cdll.LoadLibrary('libasound.so')
    asound.snd_lib_error_set_handler(c_error_handler)

    def update_rate(self, amount):
        self.rate += amount
        self.song.set_rate(self.rate)

    def log(self, input):
        input = str(input)
        with open("test.txt", "a") as myfile:
            string = datetime.datetime.fromtimestamp(
                time.time()).strftime('%Y-%m-%d %H:%M:%S')
            string = string + ' - ' + input + '\n'
            myfile.write(string)

    def mark_to_milliseconds(self, mark):
        milliseconds = int(self.duration * mark)
        return milliseconds

    def __init__(self, stdscreen):
        self.rate = 1
        self.position = 0
        self.is_marking = False
        self.marks = []
        self.markItr = 0
        self.current_mark = None
        self.now_okay = True

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
            if key == config.play_speed_up:
                self.update_rate(config.play_speed_rate)

            # Slows down the playback
            elif key == config.play_speed_down:
                self.update_rate(-config.play_speed_rate)

            # Jumps back 5 seconds
            elif key == config.jump_back:
                self.changePositionBySecondOffset(-config.jump_time, self.song.get_position())

            # Jump ahead five seconds
            elif key == config.jump_forward:
                self.changePositionBySecondOffset(config.jump_time, self.song.get_position())

            # pauses and plays the media
            elif key == config.play_pause:
                if self.song.is_playing:
                    self.song.pause()
                else:
                    self.song.play()

            # Create a new mark
            elif key == config.mark_create_new:
                # if there is not an active mark, make one
                if self.current_mark:
                    sounds.error_sound()
                else:
                    self.current_mark = Mark()

            # Saves a current mark
            elif key == config.mark_save_current:
                # check to make sure there is an active mark and that both the beginning and end have
                # been entered
                if self.current_mark and self.current_mark.start != -1 and self.current_mark.end != -1:
                    self.current_mark.reset()
                    self.marks.append(self.current_mark)
                    self.markItr = len(self.marks) - 1
                    self.current_mark = None
                    self.marks = sorted(self.marks, key=itemgetter('start'))
                else:
                    sounds.error_sound()

            # Record the beginning of the mark
            elif key == config.mark_record_start_posistion:
                # make sure there is and active mark
                if self.current_mark:
                    begin_position_check = self.song.get_position()
                    okay = True
                    # cycle through the saved marks and make sure the current position does
                    # overlap with them
                    for each in self.marks:
                        if each.start <= begin_position_check <= each.end:
                            okay = False
                    if okay:
                        self.current_mark.start = begin_position_check
                    else:
                        self.log('overlap')
                        sounds.error_sound()
                else:
                    self.log('no current_mark')
                    sounds.error_sound()

            # Record the end of the mark
            elif key == config.mark_record_end_posistion:
                # make sure there is an active mark
                if self.current_mark:
                    begin_position_check = self.song.get_position()
                    okay = True
                    # cycle through the saved marks and make sure the current position does
                    # overlap with them
                    for each in self.marks:
                        if each.start <= begin_position_check <= each.end:
                            okay = False
                    if okay:
                        self.current_mark.end = begin_position_check
                    else:
                        sounds.error_sound()
                else:
                    sounds.error_sound()

            elif key == config.cycle_through_marks:
                self.markItr = 0
                self.current_mark = self.marks[self.markItr]

            # Quit the program
            elif key == config.quit_program:
                self.poll_thread.join()
                break

            # Do the actual edits taking the marks and applying them to
            # to the original file
            elif key == config.begin_edits:
                self.poll_thread.join()
                self.song.stop()

                filename, file_extension = os.path.splitext(self.original_file)
                self.temp_file = filename + "-old" + file_extension
                os.rename(self.original_file, self.temp_file)
                command = ['ffmpeg', "-loglevel",
                           "error", '-i', self.temp_file]

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
                self.log(str(int(self.duration / 1000)))
                n.end = 1
                self.marks.append(n)
                for i, each in enumerate(self.marks):
                    if i == 0:
                        select += """between(t,{},{})""".format(
                            int(self.mark_to_milliseconds(each.start) / 1000),
                            int(self.mark_to_milliseconds(each.end) / 1000),
                        )
                        aselect += """between(t,{},{})""".format(
                            int(self.mark_to_milliseconds(each.start) / 1000),
                            int(self.mark_to_milliseconds(each.end) / 1000),
                        )
                    else:
                        select += """+between(t,{},{})""".format(
                            int(self.mark_to_milliseconds(each.start) / 1000),
                            int(self.mark_to_milliseconds(each.end) / 1000),
                        )
                        aselect += """+between(t,{},{})""".format(
                            int(self.mark_to_milliseconds(each.start) / 1000),
                            int(self.mark_to_milliseconds(each.end) / 1000),
                        )

                select += """',setpts=N/FRAME_RATE/TB """
                aselect += """',asetpts=N/SR/TB"""
                command.append('-vf')
                command.append(select)
                command.append('-af')
                command.append(aselect)
                command.append(self.original_file)
                self.command = command
                self.log(command)
                subprocess.call(command)
                os.remove(self.temp_file)
                break

        self.window.clear()
        self.panel.hide()
        panel.update_panels()
        curses.doupdate()

    def changePositionBySecondOffset(self, sec_offset, cur_pos):
        cur_sec = round(cur_pos * self.duration) + (sec_offset * 1000)
        new_pos = cur_sec / self.duration
        if sec_offset < 0:
            if new_pos < 0:
                new_pos = 0
        else:
            if new_pos > 1:
                new_pos = 1
        self.song.set_position(new_pos)
        self.song.play()



if __name__ == '__main__':
    curses.wrapper(MyApp)

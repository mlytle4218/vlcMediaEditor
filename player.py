#!/usr/bin/env python3
import curses
import datetime
import os
import subprocess
import sys
import time
from ctypes import CFUNCTYPE, c_char_p, c_int, cdll
from curses import panel
from operator import itemgetter

import config
import sounds
import vlc
from mark import Mark
from workerThread import WorkerThread



class MyApp(object):

    def update_rate(self, amount):
        self.rate += amount
        self.song.set_rate(self.rate)

    def normalize_rate(self):
        self.rate = 1
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

        # self.height, self.width = stdscreen.getmaxyx()
        self.window = stdscreen.subwin(0, 0)
        self.window.keypad(1)
        self.panel = panel.new_panel(self.window)
        self.panel.hide()
        panel.update_panels()

        self.position = 0
        self.panel.top()
        self.panel.show()
        self.window.clear()
        # n = Mark()
        # n.start = 0.015
        # n.end = 0.035
        # self.marks.append(n)
        # n = Mark()
        # n.start = 0.125
        # n.end = 0.268
        # self.marks.append(n)

        self.original_file = sys.argv[1]
        self.instance = vlc.Instance(('--no-video'))
        self.song = self.instance.media_player_new()
        self.media = self.instance.media_new(self.original_file)
        self.song.set_media(self.media)
        self.song.play()
        self.media.parse()
        self.poll_thread = WorkerThread(self)
        self.poll_thread.start()

        self.duration = self.media.get_duration()
        try:
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
                    if (self.song.get_state() != 6):
                        self.changePositionBySecondOffset(
                            -config.jump_time,
                            self.song.get_position()
                            )
                    else:
                        self.song = self.instance.media_player_new()
                        self.media = self.instance.media_new(self.original_file)
                        self.song.set_media(self.media)
                        self.song.play()
                        self.media.parse()
                        self.changePositionBySecondOffset(
                            -config.jump_time, 1)


                # Jump ahead five seconds
                elif key == config.jump_forward:
                    self.changePositionBySecondOffset(
                        config.jump_time, self.song.get_position())

                # pauses and plays the media
                elif key == config.play_pause:
                    if self.song.is_playing:
                        self.song.pause()
                    else:
                        self.song.play()

                # Create a new mark
                elif key == config.mark_create_new:
                    try:
                        if self.current_mark:
                            sounds.error_sound()
                        else:
                            self.current_mark = Mark()
                    except Exception as ex:
                        self.log(ex)

                # Saves a current mark
                elif key == config.mark_save_current:
                    try:
                        self.saveCurrentMark()
                    except Exception as ex:
                        self.log(ex)

                # Record the beginning of the mark
                elif key == config.mark_record_start_position:
                    try:
                        self.startMarkPosition()
                    except Exception as ex:
                        self.log(ex)

                # Record the end of the mark
                elif key == config.mark_record_end_position:
                    try:
                        self.endMarkPosition()
                    except Exception as ex:
                        self.log(ex)

                # Starting the current markItr cycle through the saved marks
                # when in a Mark it is editable
                elif key == config.cycle_through_marks:
                    try:
                        self.cycleThroughMarks()
                    except Exception as ex:
                        self.log(ex)

                # Stop cycling through marks
                elif key == config.cycle_through_marks_stop:
                    try:
                        self.current_mark = None
                    except Exception as ex:
                        self.log(ex)

                # Quit the program
                elif key == config.quit_program:
                    self.poll_thread.join()
                    break

                elif key == ord('w'):
                    # self.log(self.current_mark)
                    # self.log(self.markItr)
                    self.log(self.position)
                    self.log(self.song.get_position())

                # Do the actual edits taking the marks and applying them to
                # to the original file
                elif key == config.begin_edits:
                    self.applyEdits()
                    break

                # Go back to normal speed
                elif key == config.normal_speed:
                    self.normalize_rate()

                elif key == config.current_time:
                    self.poll_thread.print_out_time()

                elif key == config.jump_specific:
                    self.jumpSpecificTime()
        except KeyboardInterrupt:
            pass

        self.window.clear()
        self.panel.hide()
        panel.update_panels()
        curses.doupdate()

    def getInput(self, prompt, input_length):
        curses.echo()
        self.window.addstr(0,0,prompt)
        self.window.refresh()
        input = self.window.getstr(1, 0, input_length)
        self.window.clear()
        return input

    def jumpSpecificTime(self):
        self.song.pause()
        self.window.clear()
        forward_input = self.getInput('forward? ',1)
        reverse = False
        if forward_input.decode() == "-":
            reverse = True
        hours = 0
        while True:
            hours_input = self.getInput('hours? ',2)
            if hours_input.decode() == '':
                break
            try:
                hours_input = int(hours_input.decode())
                if (hours_input >= hours):
                    hours = hours_input
                    break
            except ValueError as e:
                self.log('error hours')
                self.log(e)
        minutes = 0
        while True:
            minutes_input = self.getInput('minutes? ', 2)
            if minutes_input.decode() == '':
                break
            try:
                minutes_input = int(minutes_input.decode())
                if (minutes_input >= minutes):
                    minutes = minutes_input
                    break
            except ValueError as e:
                self.log('error minutes')
                self.log(e)
        seconds = 0
        while True:
            seconds_input = self.getInput('seconds? ', 2)
            if seconds_input.decode() == '':
                break
            try:
                seconds_input = int(seconds_input.decode())
                if (seconds_input >= seconds):
                    seconds = seconds_input
                    break
            except ValueError as e:
                self.log('error seconds')
                self.log(e)
        seconds = seconds + minutes * 60 + hours * 60 *60
        if reverse:
            seconds *= -1

        self.changePositionBySecondOffset(
            seconds,
            self.song.get_position()
            )
        self.song.play()
        
        


    def saveCurrentMark(self):
        # check to make sure there is an active mark and that both the beginning and end have
        # been entered
        if self.current_mark and self.current_mark.start != -1 and self.current_mark.end != -1:
            self.current_mark.reset()
            self.marks.append(self.current_mark)
            self.current_mark = None
            # TODO Not thinking I need to do this. investgate later
            self.marks = sorted(self.marks, key=itemgetter('start'))
        else:
            sounds.error_sound()

    def startMarkPosition(self):
        if self.current_mark:
            begin_position_check = self.song.get_position()
            okay = True
            # cycle through the saved marks and make sure the current position does
            # overlap with them
            for each in self.marks:
                if each != self.current_mark:
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

    def endMarkPosition(self):
        if self.current_mark:
            begin_position_check = self.song.get_position()
            okay = True
            # cycle through the saved marks and make sure the current position does
            # overlap with them
            for each in self.marks:
                if each != self.current_mark:
                    if each.start <= begin_position_check <= each.end:
                        okay = False
            if okay:
                self.current_mark.end = begin_position_check
            else:
                sounds.error_sound()
        else:
            sounds.error_sound()

    def applyEdits(self):
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
        # self.log(str(int(self.duration / 1000)))
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

    def cycleThroughMarks(self):
        self.current_mark = self.marks[self.markItr]
        self.changePositionBySecondOffset(-2, self.current_mark.start)
        if len(self.marks) > self.markItr+1:
            self.markItr += 1
        else:
            self.markItr = 0

    def changePositionBySecondOffset(self, sec_offset, cur_pos):
        cur_sec = round(cur_pos * self.duration) + (sec_offset * 1000)
        new_pos = cur_sec / self.duration
        if sec_offset < 0:
            if new_pos < 0:
                new_pos = 0
                # print out remaining time instead of jumping to end
                left = self.poll_thread.timeStamp(self.duration, self.song.get_position())
                self.window.addstr(0,0,"the most you can jump backwards is " + left)
                return None
        else:
            if new_pos > 1:
                new_pos = 1
                # print out remaining time instead of jumping to end
                left = self.poll_thread.timeStamp(self.duration, 1 - self.song.get_position())
                self.window.addstr(0,0,"the most you can jump forward is " + left)
                return None
        self.song.set_position(new_pos)
        self.song.play()


if __name__ == '__main__':
    if len(sys.argv) == 2:
        curses.wrapper(MyApp)
    else:
        print("requires a file to edit")

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
import pickle
import shutil

import config
import sounds
import vlc
from mark import Mark
from wt import WT

import json


class State():
    def __init__(self):
        marks = []
        duration = 0


class MyApp(object):

    def __init__(self, stdscreen):

        self.rate = 1
        self.position = 0
        self.is_editing = False
        self.state = State()
        self.markItr = 0
        self.blockItrPrev = -1
        self.current_mark = None
        self.volume = config.volume
        self.applyEditsBoolean = False
        self.cycle_start = True
        self.advance_time = config.jump_time_long

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

        self.original_file = sys.argv[1]

        self.file_path = os.path.dirname(os.path.realpath(sys.argv[1]))
        self.file_basename = os.path.basename(sys.argv[1])
        self.file_name = os.path.splitext(self.file_basename)[0]
        self.file_ext = os.path.splitext(self.file_basename)[1]

        # if opening a backup, look for a state file with the original name
        self.state_file_name = ""
        self.old_file_name = ""
        if self.file_name.endswith('-original'):
            self.state_file_name = os.path.join(
                self.file_path,
                self.file_name.replace('-original', '') + ".state"
            )
            self.old_file_name = os.path.join(
                self.file_path,
                self.file_name.replace('-original','') + self.file_ext
            )
        else:
            # check to see if its our data input
            if self.file_ext == '.data':
                self.file_ext = ".mp4"
            self.file_name_new = os.path.join(
                self.file_path,
                self.file_name + "-original" + self.file_ext
            )
            if self.checkRates(os.path.realpath(sys.argv[1])):
                shutil.move(
                    os.path.realpath(sys.argv[1]),
                    os.path.join(
                        self.file_path,
                        self.file_name_new
                    )
                )
            else:
                self.print_to_screen('converting file')
                cmd = ['ffmpeg','-y','-i',os.path.realpath(sys.argv[1]),'-ar','44100',os.path.join(self.file_path, self.file_name_new)]
                result = subprocess.run(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                lines = result.stdout.decode('utf-8').splitlines()
                for line in lines:
                    for word in line.split():
                        if word.startswith('time='):
                            time_temp = word.split("=")[1].split(":")
                            time = int(time_temp[0]) * 3600 + int(time_temp[1]
                                                                )*60 + round(float(time_temp[2]))
                
                quick_state = State()
                quick_state.marks = []
                quick_state.duration = time * 1000
                self.write_state_information()
                os.remove(os.path.realpath(sys.argv[1]))





            # self.file_path = self.file_name_new
            self.old_file_name = self.original_file
            self.original_file = self.file_name + "-original" + self.file_ext

            self.state_file_name = os.path.join(
                self.file_path, 
                self.file_name + ".state"
            )

        self.read_state_information()

        print('loading file')
        try:
            if not self.state.duration:
                self.state.duration = self.get_file_length(self.original_file)
                self.write_state_information()
            self.log("file duration: {}".format(self.state.duration))
        except Exception:
            quick_state = State()
            quick_state.marks = []
            quick_state.duration = self.get_file_length(self.original_file)
            self.state = quick_state

        
        # this extra step is to set the verbosity of the log errors so they
        # don't print to the screen
        # libvlc_set_log_verbosity tooltip says its defunct
        self.VLC = vlc
        self.VLC.libvlc_set_log_verbosity(None, 1)
        self.instance = self.VLC.Instance(('--no-video'))
        self.song = self.instance.media_player_new()
        self.media = self.instance.media_new(self.original_file)
        self.song.set_media(self.media)

        self.song.play()
        self.media.parse()
        self.poll_thread = WT(self)
        self.poll_thread.start()

        try:
            while True:
                self.position = self.song.get_position()
                self.window.refresh()
                curses.doupdate()

                key = self.window.getch()

                # Raises the volume
                if key == config.volume_up:
                    self.changeVolume(config.volume_increments)
                # Lowers the volume
                if key == config.volume_down:
                    if self.volume > 0:
                        self.changeVolume(-config.volume_increments)

                # Speeds up the playback
                if key == config.play_speed_up:
                    self.update_rate(config.play_speed_rate)

                # Slows down the playback
                elif key == config.play_speed_down:
                    self.update_rate(-config.play_speed_rate)

                # Jumps back 5 seconds
                elif key == config.jump_back:
                    self.changePositionBySecondOffset_new(
                        -self.advance_time,
                        message=False,
                        forward=False
                    )

                # Jump ahead five seconds
                elif key == config.jump_forward:
                    self.changePositionBySecondOffset_new(
                        self.advance_time,
                        message=False,
                        forward=True
                    )

                # pauses and plays the media
                elif key == config.play_pause:
                    if self.song.is_playing:
                        self.song.pause()
                    else:
                        self.song.play()

                # Create a new mark
                elif key == config.mark_create_new:
                    # self.createNewMark()
                    pass

                # Saves a current mark
                elif key == config.change_advance_speed:
                    try:
                        self.toggle_advance_speed()
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
                # This is only for listening
                elif key == config.cycle_through_marks:
                    try:
                        self.cycleThroughMarks()
                    except Exception as ex:
                        self.log(ex)

                elif key == config.cycle_through_marks_editing:
                    try:
                        self.is_editing = not self.is_editing
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

                elif key == ord('x'):
                    self.log(self.position)
                    self.log(self.song.get_position())

                # Do the actual edits taking the marks and applying them to
                # to the original file
                elif key == config.begin_edits:
                    global final_command
                    global edited_file
                    final_command, edited_file = self.applyEdits()
                    self.poll_thread.join()
                    break

                # Go back to normal speed
                elif key == config.normal_speed:
                    self.normalize_rate()

                # print the current time formatted to the screen
                elif key == config.current_time:
                    c_time = self.timeStamp(
                        self.state.duration, self.song.get_position())
                    self.print_to_screen(c_time)

                # print the lenght of the file to the screen
                elif key == config.file_length:
                    length = self.timeStamp(self.state.duration, 1)
                    self.print_to_screen(length)

                # causes the playback to stop and allows user to enter a spcific
                # amount of time to move forward or backward
                elif key == config.jump_specific:
                    self.jumpSpecificTime()

                # creates a mark that starts at the beginning of the file to the
                # current position
                elif key == config.block_from_begining:
                    self.begining_ending_block(True)

                # creates a mark that starts from the current position to the end
                # fo the file
                elif key == config.block_till_end:
                    self.begining_ending_block(False)

                elif key == config.jump_to_start:
                    self.log('jump_to_start')
                    self.song.set_position(0)
                
                elif key == config.jump_to_end:
                    self.song.set_position(0.9999999999)

                # deletes the current block
                elif key == config.delete_block:
                    self.delete_block()

                # elif key == config.nudge:
                #     self.nudgeBeginningOrEnding()

                elif key == config.list_marks:
                    self.log('current blocks')
                    for mark in self.state.marks:
                        self.log(mark.get_time(self.state.duration))
        except KeyboardInterrupt:
            pass

        self.window.clear()
        self.panel.hide()
        panel.update_panels()
        curses.doupdate()
        curses.endwin()


    def nudge(self,forward=True):
        if self.is_editing:
            amount = 0
            if forward:
                amount = config.nudge_increment
            else:
                amount = -config.nudge_increment
        else:
            sounds.error_sound()
            self.print_to_screen("Can not nudge unless in edit mode")

    def getBitRate(self,inputFile):
        cmd = ['ffprobe','-v','quiet','-print_format','json','-show_streams',inputFile]
        result = subprocess.check_output(cmd).decode('utf-8')
        result = json.loads(result)
        for stream in result['streams']:
            if stream['codec_type'] =="audio":
                return int(stream['bit_rate'])
        # return int(result['streams'][0]['bit_rate'])

    def getSampleRate(self,inputFile):
        cmd = ['ffprobe','-v','quiet','-print_format','json','-show_streams',inputFile]
        result = subprocess.check_output(cmd).decode('utf-8')
        result = json.loads(result)
        for stream in result['streams']:
            if stream['codec_type'] =="audio":
                return int(stream['sample_rate'])
        # return int(result['streams'][0]['sample_rate'])

    def checkRates(self,inputFile):
        return self.getBitRate(inputFile) == 128000 and self.getSampleRate ==  44100

    def startSound(self):
        sounds.mark_start_sound()

    def endSound(self):
        sounds.mark_end_sound()

    def write_state_information(self):
        """
        Method to write the state information to a file named like the original
        with a .state extension
        """
        try:
            state = open(self.state_file_name, 'wb')
            # for mark in self.state.marks:
            #     self.log(mark.get_time(self.state.duration))
            pickle.dump(self.state, state)
        except Exception as e:
            self.log(e)

    def read_state_information(self):
        """
        Method to read the saved information about a file from a file named like
        the original with a .state extension
        """
        try:
            state = open(self.state_file_name, 'rb')
            self.state = pickle.load(state)
        except IOError:
            self.log("No file found")

    def delete_block(self):
        """
        Method to remove block from self.state.marks
        """
        try:
            if self.is_editing:
                self.state.marks.pop(self.markItr)
                self.print_to_screen('Block deleted')
            else:
                self.print_to_screen('Not in edit mode')
            # if self.current_mark.is_editing:
            #     block_to_be_deleted = self.state.marks.index(self.current_mark)
            #     self.state.marks.pop(block_to_be_deleted)
            #     self.current_mark = None
            #     self.print_to_screen('block deleted')
            # else:
            #     self.print_to_screen('Not in edit mode')
        except Exception as ex:
            self.log(ex)

    def delete_block_old(self):
        """
        Method to remove block from self.state.marks
        """
        try:
            if self.is_editing and self.current_mark:
                self.state.marks.pop(self.blockItrPrev)
                if self.markItr > len(self.state.marks):
                    self.markItr = 0
                if self.markItr == 0:
                    self.blockItrPrev = len(self.state.marks)
                else:
                    self.blockItrPrev = self.markItr - 1
                self.print_to_screen('Block deleted')
                self.current_mark = None
                self.write_state_information()
        except Exception as ex:
            self.log(ex)

    def begining_ending_block(self, start):
        """
        Method to make a block starting from the begining of the file to the current position or from the current position to the end of the file

        Arguments:
        start: Boolean - if True, then the block is from the begining to the current position, if False -  from the current position to the end of the file
        """
        try:
            if self.current_mark:
                self.print_to_screen('There is unfinished block')
            else:
                mark = Mark(position=self.song.get_position())
                if start:
                    mark.start = 0
                else:
                    mark.end = 1
                self.overwriteOverlaps(mark)
                self.state.marks = sorted(
                    self.state.marks, key=itemgetter('start'))
                self.markItr += 1
                self.print_to_screen('saved')
                self.write_state_information()
        except Exception as ex:
            self.log(ex)

    def begining_ending_block_old(self, start):
        """
        Method to make a block starting from the begining of the file to the current position or from the current position to the end of the file

        Arguments:
        start: Boolean - if True, then the block is from the begining to the current position, if False -  from the current position to the end of the file
        """
        try:
            if self.current_mark:
                sounds.error_sound(self.volume)
                self.log(
                    'tried to use B or E while an existing block was current - beginning_ending_block()')
                self.print_to_screen('Overlap with an existing block')
            else:
                mark = Mark(position=self.song.get_position())
                if not self.check_for_overlap(self.song.get_position()):
                    if start:
                        mark.start = 0
                        mark.end = self.song.get_position()
                    else:
                        mark.start = self.song.get_position()
                        mark.end = 1
                    self.state.marks.append(mark)
                    self.state.marks = sorted(
                        self.state.marks, key=itemgetter('start'))
                    self.markItr += 1
                    self.print_to_screen('saved')
                    self.write_state_information()
                else:
                    self.log(
                        'Tried to use B or E and found an overlap with exisitng block')
                    self.print_to_screen('Overlap with an existing block')
        except Exception as ex:
            self.log(ex)

    def update_rate(self, amount):
        """
        Method to change the playback rate.

        Arguments - amount - float - The amount of change in the rate. A positive
        amount makes it faster. A negative amount makes it slower.
        """
        self.rate += amount
        self.song.set_rate(self.rate)

    def normalize_rate(self):
        """
        Method to return the playback rate to normal(1)
        """
        self.rate = 1
        self.song.set_rate(self.rate)

    def log(self, input):
        input = str(input)
        with open("log.txt", "a") as myfile:
            string = datetime.datetime.fromtimestamp(
                time.time()).strftime('%Y-%m-%d %H:%M:%S')
            string = string + ' - ' + input + '\n'
            myfile.write(string)

    def mark_to_milliseconds(self, mark):
        """
        Method to change vlc's position to milliseconds

        Argument - mark - float - vlc's position number.
        """
        return int(self.state.duration * mark)

    def print_to_screen(self, output):
        """
        Method that prints the time (formatted) of the current postion

        Arguments - output - string - what is supposed to printed to screen
        """
        # self.log('print_to_screen: {}'.format(output))
        self.window.clear()
        self.window.addstr(0, 0, output)
        self.window.refresh()

        curses.doupdate()

    def get_file_length(self, input_file):
        """
        Method to get the length of the original file

        Arguments - input_file - string - the path and file name of the file
        """
        time = 0
        command = ['ffmpeg', '-i', input_file, '-f', 'null', '-']
        result = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        lines = result.stdout.decode('utf-8').splitlines()
        for line in lines:
            for word in line.split():
                if word.startswith('time='):
                    time_temp = word.split("=")[1].split(":")
                    time = int(time_temp[0]) * 3600 + int(time_temp[1]
                                                          )*60 + round(float(time_temp[2]))
        return time * 1000

    def getInput(self, prompt, input_length):
        """
        Method to get input from the user, more than just one keystroke.
        """
        curses.echo()
        self.window.addstr(0, 0, prompt)
        self.window.refresh()
        input = self.window.getstr(1, 0, input_length)
        self.window.clear()
        return input

    def changeVolume(self, value):
        """
        Method to the change the current volume of the ancillary sounds.

        Arguments - value - float - positive value raises the volume, negative
        value lowers the volume.
        """
        self.volume += value

    def jumpSpecificTime(self):
        self.song.pause()
        self.window.clear()
        forward_input = self.getInput('forward? ', 1)
        if forward_input.decode() == "b":
            self.song.set_position(0)
        elif forward_input.decode() == "e":
            self.song.set_position(1)
        else:
            reverse = False
            if forward_input.decode() == "-":
                reverse = True
            hours = 0
            while True:
                hours_input = self.getInput('hours? ', 2)
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
            seconds = seconds + minutes * 60 + hours * 60 * 60
            if reverse:
                seconds *= -1

            self.changePositionBySecondOffset_new(
                seconds
            )
        self.song.play()

    def createNewMark(self):
        """
        Method to create a new block and set it to current.

        defunct
        """
        try:
            if self.current_mark:
                sounds.error_sound(self.volume)
                self.log(
                    'tried to create a new mark when one existed - createNewMark()')
            else:
                count = len(self.state.marks)
                self.current_mark = Mark(position=self.song.get_position())
                self.state.marks.append(self.current_mark)
                self.write_state_information()
                self.print_to_screen('block {}.'.format(count+1))
        except Exception as ex:
            self.log(ex)

    def toggle_advance_speed(self):
        """
        Method that changes the arrow forward/back advace mode.
        """
        if self.advance_time == config.jump_time_long:
            self.advance_time = config.jump_time_short
        else:
            self.advance_time = config.jump_time_long
        self.print_to_screen("{} second advance amount".format(self.advance_time))
        # if self.is_editing:
        #     self.current_mark.reset()
        #     self.current_mark = None
        #     self.print_to_screen('saved')
        #     self.write_state_information()
        #     self.is_editing = False
        # else:
        #     sounds.error_sound(self.volume)
        #     self.print_to_screen('not in edit mode f toggle_advance_speed()')

    def checkForOverlap(self, markToBeChecked):
        """
        Method to check if a proposed black will overlap and existing block

        Arguments:
        markToBeChecked - mark - the new mark that may overlap another.

        Returns an array of iterators of the marks that it overlaps 
        """
        results = []
        for itr,mark in enumerate(self.state.marks):
            if mark.over(markToBeChecked):
                results.append(itr)

        return results

    def check_for_overlap(self, position, index=None):
        """
        Method to check if the proposed position for a new block beginning or
        ending position overlaps with another block

        Arguments - position - float - the proposed position
                    index - int - the index of existing marks array that we want
                    to avoid.

        Returns True if there is overlap with any block in marks array and False
        if there is not - if an index is passed, it avoids that object as that is
        the current object getting edited.
        """
        if index is not None:
            for i, mark in enumerate(self.state.marks):
                if i != index:
                    if mark.overlap(position):
                        return True
                return False
        else:
            self.log('check for overlap no index')
            for mark in self.state.marks:
                if mark.overlap(position):
                    return True
            return False

    def startMarkPosition(self):
        """
        Method to mark the start position of a new block.

        Starts by seeing if it is in edit mode.

        If it is in edit mode, it gets the index of the current mark and compares
        the proposed new start against all the other marks to see if it overlaps
        with any of them. If not, it updates the start position of the block.

        If it is not in edit move, it checks to see if the proposed position
        overlaps with any of the other blocks. If it does not, it creates a new
        block and sets the start position at the current position
        """
        try:
            if self.is_editing:
                self.state.marks[self.markItr].start = self.song.get_position()
                self.print_to_screen('Block {} start edited'.format((self.markItr+1)))
                self.write_state_information()
            else:
                if self.current_mark:
                    self.current_mark = None
                self.current_mark = Mark()
                self.current_mark.start = self.song.get_position()
                self.print_to_screen('Starting block {}'.format(len(self.state.marks)+1))

        except Exception as ex:
            sounds.error_sound(self.volume)
            self.log(ex)

    def endMarkPosition(self):
        """
        Method to mark the end position of an existing block.

        Starts by seeing if it is in edit mode.

        If it is in edit mode, it gets the index of the current mark and compares
        the proposed new end against all the other marks to see if it overlaps
        with any of them. If not, it updates the end position of the block.

        If it is not in edit move, it checks to see if the proposed position
        overlaps with any of the other blocks. If it does not, it sets the start
        position at the current position
        """
        try:
            if self.is_editing:
                # markItr - 1 from a problem with cycling function
                # TODO fix this living with it for now.
                self.state.marks[self.markItr - 1].end = self.song.get_position()
                self.print_to_screen('Block {} end edited'.format(self.markItr))
                self.write_state_information()
            elif self.current_mark:
                self.current_mark.end = self.song.get_position()
                self.print_to_screen('Ending block {}'.format(len(self.state.marks)+1))
                self.overwriteOverlaps(self.current_mark)
                self.current_mark = None
                self.write_state_information()
            else:
                self.print_to_screen("Can't end block that hasn't been started")

        except Exception as ex:
            self.log(ex)

    def overwriteOverlaps(self, cur_mark):
        itrs = self.checkForOverlap(cur_mark)
        itrs.sort(reverse=True)
        for i in itrs:
            self.state.marks.pop(i)
        self.state.marks.append(cur_mark)
        self.state.marks = sorted(self.state.marks, key=itemgetter('start'))

    def check_for_null_blocks(self):
        """
        Method to check the blocks for any that did have the beginning or ending specified
        """
        self.state.marks = list(
            filter(lambda x: x.is_null() != True, self.state.marks))
        self.log('check_for_null_blocks')

    def applyEdits(self):
        """
        Method to create the final command for editing the original file.
        """
        self.song.stop()
        self.check_for_null_blocks()

        # filename, file_extension = os.path.splitext(self.original_file)
        # edited_file = filename + "-edited" + file_extension
        edited_file = self.old_file_name
        command = ['ffmpeg', '-i', self.original_file]
        select = "select='"
        aselect = "aselect='"
        last = 0
        for each in self.state.marks:
            temp = each.end
            each.end = each.start
            each.start = last
            last = temp
        n = Mark(position=self.song.get_position())
        n.start = last
        n.end = 1
        self.state.marks.append(n)
        for i, each in enumerate(self.state.marks):
            if i == 0:
                select += """between(t,{},{})""".format(
                    (self.mark_to_milliseconds(each.start) / 1000),
                    (self.mark_to_milliseconds(each.end) / 1000),
                )
                aselect += """between(t,{},{})""".format(
                    (self.mark_to_milliseconds(each.start) / 1000),
                    (self.mark_to_milliseconds(each.end) / 1000),
                )
            else:
                select += """+between(t,{},{})""".format(
                    (self.mark_to_milliseconds(each.start) / 1000),
                    (self.mark_to_milliseconds(each.end) / 1000),
                )
                aselect += """+between(t,{},{})""".format(
                    (self.mark_to_milliseconds(each.start) / 1000),
                    (self.mark_to_milliseconds(each.end) / 1000),
                )

        select += """',setpts=N/FRAME_RATE/TB """
        aselect += """',asetpts=N/SR/TB"""
        command.append('-vf')
        command.append(select)
        command.append('-af')
        command.append(aselect)
        command.append(edited_file)
        self.log(command)
        return command, edited_file

    def cycleThroughMarks(self, edit=False):
        """
        Method to move the playback through the existing blocks

        Arguments:
        edit - boolean - True if the intent is to edit the blocks and False if
        not. Default is False.
        """
        # self.is_editing = edit
        
        if self.is_editing:
            if self.cycle_start:
                self.changePositionBySecondOffset(
                    config.preview_time,
                    self.state.marks[self.markItr].start
                )
                self.print_to_screen('Block {} start'.format(self.markItr + 1))
            else:
                self.changePositionBySecondOffset(
                    config.preview_time,
                    self.state.marks[self.markItr].end
                )

                self.print_to_screen('Block {} end'.format(self.markItr + 1))
                self.updateIters()

            self.cycle_start = not self.cycle_start
            
        else:
            self.changePositionBySecondOffset_new(
                config.preview_time,
                cur_pos=self.state.marks[self.markItr].start
            )
            self.print_to_screen('Block {}'.format(self.markItr + 1))
            self.updateIters()

    def cycleThroughMarks_old(self, edit=False):
        """
        Method to move the playback through the existing blocks.

        Arguments:
        edit - boolean - True if the intent is to edit the blocks and False if
        not. Default is False
        """

        self.is_editing = edit
        if edit:
            self.current_mark = self.state.marks[self.markItr]
        if self.cycle_start:
            self.changePositionBySecondOffset(
                config.preview_time, self.state.marks[self.markItr].start)
            self.cycle_start = False
            self.print_to_screen('Block {} start'.format(self.markItr+1))
        else:
            self.changePositionBySecondOffset(
                config.preview_time, self.state.marks[self.markItr].end)
            self.cycle_start = True
            self.print_to_screen('Block {} end'.format(self.markItr+1))
            self.updateIters()

    def updateIters(self):
        if len(self.state.marks) > self.markItr+1:
            self.markItr += 1
        else:
            self.markItr = 0

    def changePositionBySecondOffset_new(self, sec_offset, cur_pos=None, message=True, forward=True):
        """
        Method to change the current position of the playing audio

        Arguments:
        sec_offset - float - how many seconds to change from the current position,
        a negative value will go back while a posititve value will move formard
        message - boolean - designates that the quick 5 second jump is calling this
        function and will keep it from printing out the message
        forward - boolean - designates the jump direction
        """
        try:
            pos_offset = (sec_offset * 1000) / self.state.duration
            new_pos = 1
            if (self.song.get_state() == 6):
                if cur_pos is not None:
                    # self.log('stopped not None')
                    new_pos = cur_pos + pos_offset
                else:
                    # self.log('stopped none')
                    new_pos += pos_offset
                # get_state() 
                # {0: 'NothingSpecial',
                # 1: 'Opening',
                # 2: 'Buffering',
                # 3: 'Playing',
                # 4: 'Paused',
                # 5: 'Stopped',
                # 6: 'Ended',
                # 7: 'Error'}
                # Song is in a stopped position
                self.song = self.instance.media_player_new()
                self.media = self.instance.media_new(self.original_file)
                self.song.set_media(self.media)
                self.song.set_position(new_pos)
                self.song.play()
            else:
                # Song is in a play position
                if cur_pos is not None:
                    # self.log('playing not none')
                    new_pos = cur_pos + pos_offset
                else:
                    # self.log('playing none')
                    new_pos = self.song.get_position() + pos_offset

            for itr,mark in enumerate(self.state.marks):
                if not self.is_editing:
                    if mark.overlap(new_pos):
                        if forward:
                            new_pos = mark.end + (new_pos - mark.start)
                        else:
                            new_pos = mark.start - (mark.end - new_pos)
                        self.print_to_screen('Block {}'.format(itr + 1))
            warn_message = ""


            if new_pos < 0:
                new_pos = 0
                left = self.timeStamp(
                    self.state.duration,
                    self.song.get_position()
                )
                warn_message = 'the most you can jump backwards is {}'.format(left)

            if new_pos > 1:
                new_pos = 1
                left = self.timeStamp(
                    self.state.duration,
                    1 - self.song.get_position()
                    )
                warn_message = 'the most you can jump forwards is {}'.format(left)

            if message:
                self.print_to_screen(warn_message)
            self.song.play()
            self.song.set_position(new_pos)
        except Exception as ex:
            self.log('changePositionBySecondOffset_new')
            self.log(ex)

    def changePositionBySecondOffset(self, sec_offset, cur_pos, message=True, forward=True):
        """
        Method to change the current position of the playing audio

        Arguments:
        sec_offset - float - how many seconds to change from the current position,
        a negative value will go back while a posititve value will move formard
        curr_postion - float - the vlc position marker - this is a value between
        0 and 1.
        message - boolean - designates that the quick 5 second jump is calling this
        function and will keep it from printing out the message
        forward - boolean - designates the jump direction
        """
        try:
            pos_offset = (sec_offset * 1000) / self.state.duration
            new_pos = cur_pos + pos_offset
            # self.log(new_pos)

            for itr,mark in enumerate(self.state.marks):
                if not self.is_editing:
                    if mark.overlap(new_pos):
                        if forward:
                            new_pos = mark.end + (new_pos - mark.start)
                        else:
                            new_pos = mark.start - (mark.end - new_pos)
                        self.print_to_screen('Block {}'.format(itr + 1))
            warn_message = ""


            if new_pos < 0:
                new_pos = 0
                left = self.timeStamp(
                    self.state.duration,
                    self.song.get_position()
                )
                warn_message = 'the most you can jump backwards is {}'.format(left)

            if new_pos > 1:
                self.log('past one')
                new_pos = 1
                self.log(new_pos)
                left = self.timeStamp(
                    self.state.duration, 1 - self.song.get_position())
                warn_message = 'the most you can jump forwards is {}'.format(left)

            # check to see it is has stopped playing - have to start her again if it has
            if (self.song.get_state() == 6):
                self.song = self.instance.media_player_new()
                self.media = self.instance.media_new(
                    self.original_file)
                self.song.set_media(self.media)
                self.song.set_position(new_pos)

            if message:
                self.print_to_screen(warn_message)
            self.song.play()
            self.song.set_position(new_pos)
        except Exception as ex:
            self.log(ex)

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
            self.song.log(ex)

def printHelp():
    print('Usage: vlc-edit [FILE]')
    print('')
    print('CREATING, SETTING AND SAVING BLOCKS')
    print('To remove a section from a file, the user must create and save a block. When created, the block is in')
    print('edit mode. The user can change the beginning and ending of each block. Once saved, the user can create')
    print('new blocks. To edit an existing block, the user has to cycle through the existing blocks. It will place')
    print('the user 2 seconds before the block unless the block starts at the beginning of the file')
    print('To begin a new block press {}.'.format(chr(config.mark_create_new)))
    print('To set the starting point of a block press {}.'.format(
        chr(config.mark_record_start_position)))
    print('To set the ending point of a block press {}.'.format(
        chr(config.mark_record_end_position)))
    print('To save the current block press {}.'.format(
        chr(config.mark_save_current)))
    print('To set a block from the beginning of the file to the current position press {}.'.format(
        chr(config.block_from_begining)))
    print('To set a block from the current location till the end of the file press {}.'.format(
        chr(config.block_till_end)))
    print('To delete the current block press {}.'.format(chr(config.delete_block)))
    print('To edit existing blocks, press {} to cycle through blocks in edit mode.'.format(
        chr(config.cycle_through_marks)))
    print('To nudge a block beginning or ending, activate the block and press {}. It will ask beginning? If you want to '.format(chr(config.nudge)))
    print('edit the beginning of the block press the Return key. If you want to edit the ending of the block enter e.')
    print('Then it will ask to be continued')
    print('')
    print('MOVING THROUGH THE FILE')
    print('To play or pause existing file press {}.'.format(config.play_pause_desc))
    print('To jump ahead {} seconds press {}.'.format(
        config.jump_time, (config.jump_forward_desc)))
    print('To jump back {} seconds press {}.'.format(
        config.jump_time, config.jump_back_desc))
    print('To speed up play speed press {}.'.format((config.play_speed_up_desc)))
    print('To slow down play speed press {}.'.format(
        (config.play_speed_down_desc)))
    print('To go back to normal play speed press {}.'.format(
        chr(config.normal_speed)))
    print('To jump to a specific time forward or backward press {}. This will stop the playing of the file and '.format(
        chr(config.jump_specific)))
    print('ask a few questions. First it will ask forward? No response will result in a forward jump, where as')
    print('a - will result in a backward jump. Then it will ask for hours. Enter the number of hours or press')
    print('return to accept as zero. Then it will ask for minutes and then seconds. After the amounts are entered')
    print('it will jump that far ahead')
    print('To quit the program press {}'.format(chr(config.quit_program)))
    print('To apply the edits to the file, press {}'.format(
        chr(config.begin_edits)))
    print('')
    print('OTHER COMMANDS')
    print('To print out the current time, press {}'.format(
        chr(config.current_time)))
    print('To raise the volume of the sound effects, press {}'.format(
        chr(config.volume_up)))
    print('To lower the volume of the sound effects, press {}'.format(
        chr(config.volume_down)))


if __name__ == '__main__':
    if len(sys.argv) == 2:
        if sys.argv[1] == '--help' or sys.argv[1] == '-h':
            printHelp()
        else:
            final_command = None
            edited_file = None
            curses.wrapper(MyApp)
            curses.endwin()
            if final_command:
                process = subprocess.Popen(
                    final_command, stdout=subprocess.PIPE, universal_newlines=True)
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        print(output.strip())
    else:
        print("requires a file to edit")

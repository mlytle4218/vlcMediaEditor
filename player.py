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

import config
import sounds
import vlc
from mark import Mark
from workerThread import WorkerThread



class MyApp(object):

    def __init__(self, stdscreen):
        
        self.rate = 1
        self.position = 0
        self.is_marking = False
        self.marks = []
        self.markItr = 0
        self.current_mark = None
        # self.now_okay = True
        self.volume = config.volume
        self.applyEditsBoolean = False

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
        # this extra step is to set the verbosity of the log errors so they
        # don't print to the screen
        self.VLC = vlc
        self.VLC.libvlc_set_log_verbosity(None, 1)
        self.instance = self.VLC.Instance(('--no-video'))
        self.song = self.instance.media_player_new()
        self.media = self.instance.media_new(self.original_file)
        self.song.set_media(self.media)
        self.song.play()
        self.media.parse()
        self.poll_thread = WorkerThread(self)
        self.poll_thread.start()
        
        # self.duration = self.media.get_duration()
        # self.log(self.duration)
        # if self.duration <= 0:
        #     self.duration = int(self.ffprobe_get_length(self.original_file) * 1000)
        self.duration = int(self.ffprobe_get_length(self.original_file) * 1000)


        self.file_path = os.path.dirname(os.path.realpath(sys.argv[1]))

        self.file_basename=os.path.basename(sys.argv[1])

        self.file_name = os.path.splitext(self.file_basename)[0]

        self.state_file_name = os.path.join(self.file_path, self.file_name + ".state")

        self.read_state_information()


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
                    self.createNewMark()

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
                    global final_command
                    global edited_file
                    final_command, edited_file = self.applyEdits()
                    self.log(final_command)
                    break

                # Go back to normal speed
                elif key == config.normal_speed:
                    self.normalize_rate()

                elif key == config.current_time:
                    c_time = self.poll_thread.timeStamp(self.duration, self.song.get_position())
                    self.print_to_screen(c_time)

                elif key == config.jump_specific:
                    self.jumpSpecificTime()

                elif key == config.block_from_begining:
                    self.begining_ending_block(True)

                elif key == config.block_till_end:
                    self.begining_ending_block(False)

                elif key == config.delete_block:
                    self.delete_block()

                elif key == config.nudge:
                    self.nudgeBeginningOrEnding()

                elif key == config.list_marks:
                    self.log('bob')
                    for mark in self.marks:
                        self.log(mark)
        except KeyboardInterrupt:
            pass

        self.window.clear()
        self.panel.hide()
        panel.update_panels()
        curses.doupdate()

    def nudgeBeginningOrEnding(self):
        self.song.pause()
        beginning_input = self.getInput('Beginning? ',1)
        if beginning_input.lower() == 'b':
            self.nudgeForwardOrBackward(self.marks[self.markItr].start)
        elif beginning_input.lower() == 'e':
            self.nudgeForwardOrBackward(self.marks[self.markItr].end)
        else:
            self.print_to_screen('Invalid Choice')
            self.song.play()
            return None

    def nudgeForwardOrBackward(self, mark):
        forward_input = self.getInput('Forward? ',1)
        if forward_input == '':
            self.nudgeBlock(mark, True)
        elif forward_input == '-':
            self.nudgeBlock(mark, False)
        else:
            self.print_to_screen('Invalid Choice')
            self.song.play()
            return None

    def nudgeAmount(self, mark, forward):
        pass

    def nudgeBlock(self, mark, nudgeForward, nudgeIncrement=config.nudge_increment):
        """
        Method to return a value to assign to the nudged value of a block beginning or end.

        Arguments:
        mark: float - The current position to be nudged.
        nudgeIncrement: float - The amount to nudge the current position. If not passed, uses the default from the config.
        nudgeForward: boolean - used to decide if the nudge is a positive or negative value. 
        """
        if nudgeForward:
            mark += nudgeIncrement
        else:
            mark -= nudgeIncrement
        # mark += nudgeIncrement if nudgeForward else mark -= nudgeIncrement

    def write_state_information(self):
        try:
            state = open(self.state_file_name, 'wb')
            pickle.dump(self.marks, state)
        except Exception as e:
            self.log(e)
        # try:
        #     marks =[]
            
        #     episode_ids = []
        #     for each in download_queue:
        #         episode_ids.append(each.episode_id)
        #     state = open(config.pickled_file_location, 'wb')
        #     pickle.dump(episode_ids, state)
        # except Exception as e:
        #     self.log(e)

    def read_state_information(self):
        try:
            state = open(self.state_file_name, 'rb')
            self.marks = pickle.load(state)
        except IOError:
            self.log("No file found")
        # download_queue_local = []
        # state = open(config.pickled_file_location, 'rb')
        # episode_ids = pickle.load(state)
        # for each in episode_ids:
        #     epi = sql.get_episode_by_id(each)
        #     if epi:
        #         download_queue_local.append(epi)
        #     else:
        #         sql.log("could not read episode with episode_id:{}".format(each))
        # return download_queue_local

    def delete_block(self):
        """
        Method to remove block from self.marks
        """
        if self.current_mark:
            self.log(self.markItr)
            self.marks.pop(self.markItr)
            if self.markItr > 0:
                self.markItr -= 1
            self.print_to_screen('Block deleted')
            self.write_state_information()

    def begining_ending_block(self, start):
        """
        Method to make a block starting from the begining of the file to the current position or from the current position to the end of the file

        Arguments:
        start: Boolean - if True, then the block is from the begining to the current position, if False -  from the current position to the end of the file
        """
        try:
            if self.current_mark:
                sounds.error_sound(self.volume)
            else:
                mark = Mark()
                if start:
                    mark.start = 0
                    mark.end = self.song.get_position()
                else:
                    mark.start = self.song.get_position()
                    mark.end = 1
                self.marks.append(mark)
                self.marks = sorted(self.marks, key=itemgetter('start'))
                self.markItr += 1
                self.print_to_screen('saved')
                self.write_state_information()
        except Exception as ex:
            self.log(ex)

    def update_rate(self, amount):
        self.rate += amount
        self.song.set_rate(self.rate)

    def normalize_rate(self):
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
        milliseconds = int(self.duration * mark)
        return milliseconds

    def print_to_screen(self, output):
        self.window.clear()
        self.window.addstr(0,0,output)

    def ffprobe_get_length(self, input_file):
        #ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1
        command = ['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1', input_file]
        result = subprocess.run(command, stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        return float(result.stdout)

    def getInput(self, prompt, input_length):
        curses.echo()
        self.window.addstr(0,0,prompt)
        self.window.refresh()
        input = self.window.getstr(1, 0, input_length)
        self.window.clear()
        return input

    def changeVolume(self, value):
        self.volume += value

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

    def createNewMark(self):
        """ 
        Method to create a new block and set it to current.
        """
        try:
            if self.current_mark:
                sounds.error_sound(self.volume)
            else:
                count = len(self.marks)
                self.current_mark = Mark()
                self.marks.append(self.current_mark)
                self.write_state_information()
                self.print_to_screen('block {}.'.format(count+1))
        except Exception as ex:
            self.log(ex)

    def saveCurrentMark(self):
        """
        Method checks that block is finished and if it is, save it and remove it from the current block.
        """
        # check to make sure there is an active mark and that both the beginning and end have
        # been entered
        if self.current_mark and self.current_mark.start != -1 and self.current_mark.end != -1:
            self.current_mark.reset()
            # self.marks.append(self.current_mark)
            self.current_mark = None
            # TODO Not thinking I need to do this. investgate later
            self.marks = sorted(self.marks, key=itemgetter('start'))
            self.markItr += 1
            self.print_to_screen('saved')
            self.write_state_information()
        else:
            sounds.error_sound(self.volume)

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
                sounds.mark_start_sound(self.volume)
                self.print_to_screen('begining')
                self.log(self.poll_thread.timeStamp(self.duration, begin_position_check))
                self.write_state_information()
            else:
                self.log('overlap')
                sounds.error_sound(self.volume)
        else:
            self.log('no current_mark')
            sounds.error_sound(self.volume)

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
                sounds.mark_end_sound(self.volume)
                self.print_to_screen('end')
                self.log(self.poll_thread.timeStamp(self.duration, begin_position_check))
                self.write_state_information()
            else:
                sounds.error_sound(self.volume)
        else:
            sounds.error_sound(self.volume)

    def applyEdits(self):
        self.song.stop()

        filename, file_extension = os.path.splitext(self.original_file)
        edited_file = filename + "-edited" + file_extension
        command = ['ffmpeg', '-i', self.original_file]
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
        n.end = 1
        self.marks.append(n)
        for i, each in enumerate(self.marks):
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
        return command,edited_file

    def cycleThroughMarks(self):
        if len(self.marks) > self.markItr+1:
            self.markItr += 1
        else:
            self.markItr = 0
        self.current_mark = self.marks[self.markItr]
        self.changePositionBySecondOffset(config.preview_time, self.current_mark.start)
        self.print_to_screen('Block {}'.format(self.markItr + 1))
        time.sleep(0.25)

    def changePositionBySecondOffset(self, sec_offset, cur_pos):
        cur_sec = round(cur_pos * self.duration) + (sec_offset * 1000)
        new_pos = cur_sec / self.duration
        if sec_offset < 0:
            if new_pos < 0:
                new_pos = 0
                # print out remaining time instead of jumping to end
                left = self.poll_thread.timeStamp(self.duration, self.song.get_position())
                # self.window.addstr(0,0,"the most you can jump backwards is " + left)
                self.print_to_screen('the most you can jump backwoards is {}'.format(left))
                # return None
        else:
            if new_pos > 1:
                new_pos = 1
                # print out remaining time instead of jumping to end
                left = self.poll_thread.timeStamp(self.duration, 1 - self.song.get_position())
                self.print_to_screen('the most you can jump forwards is {}'.format(left))
                # self.window.addstr(0,0,"the most you can jump forward is " + left)
                # return None
        self.song.set_position(new_pos)
        self.song.play()


def printHelp():
    print('Usage: vlc-edit [FILE]')
    print('')
    print('CREATING, SETTING AND SAVING BLOCKS')
    print('To remove a section from a file, the user must create and save a block. When created, the block is in')
    print('edit mode. The user can change the beginning and ending of each block. Once saved, the user can create')
    print('new blocks. To edit an existing block, the user has to cycle through the existing blocks. It will place')
    print('the user 2 seconds before the block unless the block starts at the beginning of the file')
    print('To begin a new block press {}.'.format(chr(config.mark_create_new)))
    print('To set the starting point of a block press {}.'.format(chr(config.mark_record_start_position)))
    print('To set the ending point of a block press {}.'.format(chr(config.mark_record_end_position)))
    print('To save the current block press {}.'.format(chr(config.mark_save_current)))
    print('To set a block from the beginning of the file to the current position press {}.'.format(chr(config.block_from_begining)))
    print('To set a block from the current location till the end of the file press {}.'.format(chr(config.block_till_end)))
    print('To delete the current block press {}.'.format(chr(config.delete_block)))
    print('To edit existing blocks, press {} to cycle through blocks in edit mode.'.format(chr(config.cycle_through_marks)))
    print('To nudge a block beginning or ending, activate the block and press {}. It will ask beginning? If you want to '.format(chr(config.nudge)))
    print('edit the beginning of the block press the Return key. If you want to edit the ending of the block enter e.')
    print('Then it will ask to be continued')
    print('')
    print('MOVING THROUGH THE FILE')
    print('To play or pause existing file press {}.'.format(config.play_pause_desc))
    print('To jump ahead {} seconds press {}.'.format(config.jump_time, (config.jump_forward_desc)))
    print('To jump back {} seconds press {}.'.format(config.jump_time, config.jump_back_desc))
    print('To speed up play speed press {}.'.format((config.play_speed_up_desc)))
    print('To slow down play speed press {}.'.format((config.play_speed_down_desc)))
    print('To go back to normal play speed press {}.'.format(chr(config.normal_speed)))
    print('To jump to a specific time forward or backward press {}. This will stop the playing of the file and '.format(chr(config.jump_specific)))
    print('ask a few questions. First it will ask forward? No response will result in a forward jump, where as')
    print('a - will result in a backward jump. Then it will ask for hours. Enter the number of hours or press')
    print('return to accept as zero. Then it will ask for minutes and then seconds. After the amounts are entered')
    print('it will jump that far ahead')
    print('To quit the program press {}'.format(chr(config.quit_program)))
    print('To apply the edits to the file, press {}'.format(chr(config.begin_edits)))
    print('')
    print('OTHER COMMANDS')
    print('To print out the current time, press {}'.format(chr(config.current_time)))
    print('To raise the volume of the sound effects, press {}'.format(chr(config.volume_up)))
    print('To lower the volume of the sound effects, press {}'.format(chr(config.volume_down)))

if __name__ == '__main__':
    if len(sys.argv) == 2:
        if sys.argv[1] == '--help' or sys.argv[1] == '-h':
            printHelp()
        else:
            final_command = None
            edited_file = None
            curses.wrapper(MyApp)
            if final_command:
                process = subprocess.Popen(final_command, stdout=subprocess.PIPE,universal_newlines=True)
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        print(output.strip())
    else:
        print("requires a file to edit")

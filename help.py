#!/usr/bin/env python3
import textwrap, config

def printHelp():
    final_output = []
    final_output.append('Usage: vlc-edit [FILE]')
    final_output.append("")
    final_output.append('ON STARTING TO EDIT A FILE')
    final_output.append("When a file is opened with vlc-edit, it will test the "
        + "current format to see if it is compatible with vlc-edit. If it is "
        + "not, it will create new file with the original file name with a "
        +"'-original' before the file extension. If it is compatible, it will "
        + "rename the file with '-original' before the extension. In both "
        +"cases, a file with the orginal file name and extension '.state' will "
        +"be created that saves the edit information.")
    final_output.append("")
    final_output.append('MOVING THROUGH FILE')
    final_output.append(
        'To play or pause the file press {}.'.format(config.play_pause_desc))
    final_output.append("")
    final_output.append("Pressing {} will speed up the playback while {} will slow it down. ".format(
        config.play_speed_up_desc,
        config.play_speed_down_desc
    )
        + "Pressing {} will return the playback to normal speed. ".format(
            chr(config.normal_speed)
    )
    )
    final_output.append("")
    final_output.append("To jump forward press {}. To jump back press {}. {} ".format(
        config.jump_forward_desc,
        config.jump_back_desc,
        config.jump_time_long,
    )
        + "seconds is the default number of seconds the forward and back jumps. "
        + "traverse. The {} button will toggle between {} and {} second jumps ".format(
            chr(config.change_advance_speed),
            config.jump_time_long,
            config.jump_time_short,
    )
    )
    final_output.append("")
    final_output.append( ("To jump to a specific time forward or backward press {}. ".format(
        chr(config.jump_specific) ) )
        + "This will stop the playing of the file and ask a few questions. First "
        + "it will ask forward? No response will result in a forward jump, where "
        + "as a - will result in a backward jump. Then it will ask for hours. "
        + "Enter the number of hours or press return to accept as zero. Then it "
        + "will ask for minutes and then seconds. After the amounts are entered "
        + "it will jump that far.")
    final_output.append("")
    final_output.append("CREATING BLOCK FOR REMOVAL")
    final_output.append("To remove a section from a file, the user must start " 
        + "and end a block. The create a new block, press {}. To end and save a ".format(chr(config.mark_record_start_position))
        +"already started block press {}. In normal playback blocked section will ".format(chr(config.mark_record_end_position))
        +"no longer be heard")
    final_output.append("")
    final_output.append("To remove from the current position to the beginning of "
        +"the file press {}. This will overwrite any blocks made up to this point.".format(
            chr(config.block_till_begining)
        ))
    final_output.append("")
    final_output.append("To remove from the current position to the ending of "
        +"the file press {}. This will overwrite any blocks made after this point.".format(
            chr(config.block_till_end)
        ))
    final_output.append("")
    final_output.append("MOVING THROUGH BLOCKS")
    final_output.append("To preview the blocks made, the user can cycle through "
        +"the existing blocks by pressing {}. It will take the user to {} seconds ".format(chr(config.cycle_through_marks),-config.preview_time)
        +"before the first block and play. The edit should be evident. Pressing {} ".format(chr(config.cycle_through_marks))
        +"again will take the user to the next block. If the user is at the last "
        +"block, it will cycle back to the beginning.")
    final_output.append("")
    final_output.append("EDITING BLOCK")
    final_output.append("To edit a block, the user must enter edit mode by "
        +"pressing {}. Pressing {} again will toggle out of editing mode.".format(
            chr(config.cycle_through_marks_editing),
            chr(config.cycle_through_marks_editing)
        ))
    final_output.append("")
    final_output.append("To edit each specific block starting and ending position, "
        +"the user must cycle through the positions by pressing {} which selects ".format(chr(config.cycle_through_marks))
        +"that block position for editing. This will take the user to the first "
        +"block starting position and begin play. There will be an audio cue for "
        +"the block position location. Press {} again to move to the ending position.".format(chr(config.cycle_through_marks)))
    final_output.append("")
    final_output.append("If a starting block is chosen, the user can overwrite "
        +"the existing position with by pressing {}. If an ending postion is ".format(chr(config.mark_record_start_position))
        +"chosen, the exisitng position can be overwritten by pressing {}.".format(chr(config.mark_record_end_position)))
    final_output.append("")
    final_output.append("The user also has the option to nudge the position "
        +"forward or backward by {} seconds by pressing {} for backward and {} for ".format(
            config.nudge_increment,
            chr(config.nudge_back),
            chr(config.nudge_forward)
        )
        +"forward. When the nudge function is used, it will move to {} seconds ".format(-config.preview_time)
        +"before the new position and play it again.")
    final_output.append("")
    final_output.append("DELETING BLOCKS")
    final_output.append("To delete a block, the user must be in or enter edit "
        +"mode by pressing {} and then choose a block by cycling through the ".format(chr(config.cycle_through_marks_editing))
        +"block by pressing {}. The user can be either at the starting position ".format(chr(config.cycle_through_marks))
        +"or the ending position and by pressing {} can delete the curent block.".format(chr(config.delete_block)))
    final_output.append("")
    final_output.append("OTHER COMMANDS")
    final_output.append("To print out the current time, press {}.".format(chr(config.current_time)))
    final_output.append("")
    final_output.append("To print the file length, press {}".format(chr(config.file_length)))
    final_output.append("")
    final_output.append("To push the edits out to a file with the original file "
        +"name press {}.".format(chr(config.begin_edits)))
    final_output.append("")
    final_output.append("To quit the program press {}.".format(chr(config.quit_program)))
    final_output.append("")
    final_output.append("To export an existing block, the user must be in edit mode. "
        + "The user can cycle through the blocks till the block for export is "
        + "found and press {}. This will stop the playback and ask the user for ".format(chr(config.export_block_as_new_file))
        + "a path and filename. It will perform the export and then return to "
        + "regular playback.")
    
    for input in final_output:
        if input == "":
            print("")
        else:
            wrapper = textwrap.TextWrapper(width=80)
            word_list = wrapper.wrap(input)

            for each in word_list:
                print(each)
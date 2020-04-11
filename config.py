import curses

# Main control keys
play_speed_up = curses.KEY_UP
play_speed_up_desc = 'Arrow up'
play_speed_down = curses.KEY_DOWN
play_speed_down_desc = 'Arrow down'
normal_speed = ord('z')
jump_back = curses.KEY_LEFT
jump_back_desc = 'Left Arrow'
jump_forward = curses.KEY_RIGHT
jump_forward_desc = 'Right Arrow'
play_pause = ord(' ')
play_pause_desc = 'Space bar'
jump_specific = ord('j')
jump_to_start = curses.KEY_F4
jump_to_end = curses.KEY_F5

# Block creation and editing
# mark_create_new = ord('n')
cycle_through_marks_editing = ord('C')
change_advance_speed = ord('s')
mark_record_start_position = ord('b')
mark_record_end_position = ord('e')
cycle_through_marks = ord('c')
cycle_through_marks_stop = ord('v')
block_till_begining = ord('B')
block_till_end = ord('E')
delete_block = ord('d')
nudge_back = ord('n')
nudge_forward = ord('m')

export_block_as_new_file = ord('x')

# nudge = ord('l')
# nudge_beginning_left = curses.KEY_F0
# nudge_beginning_left_desc = 'Function 1'
# nudge_beginning_right =  curses.KEY_F1
# nudge_beginning_right = 'Function 2'
# nudge_ending_left = curses.KEY_F2
# nudge_ending_left = 'Function 3'
# nudge_ending_right = curses.KEY_F3
# nudge_ending_right = 'Function 4'


# Quitting and applying edits
quit_program = ord('q')
# quit_program = 'q'
begin_edits = ord('o')

# Interface keys
current_time = ord('w')
file_length = ord('l')

# volume controls
volume_up = ord('u')
volume_down = ord('d')



jump_time_long = 5
jump_time_short = 1
play_speed_rate = 0.5


volume = 1
volume_increments = 0.5
nudge_increment = 0.25
preview_time = -2


log_file = "log.txt"
key_stroke_file = "keys.txt"

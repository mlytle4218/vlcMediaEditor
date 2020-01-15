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

# Block creation and editing
mark_create_new = ord('n')
mark_save_current = ord('s')
mark_record_start_position = ord('b')
mark_record_end_position = ord('e')
cycle_through_marks = ord('c')
cycle_through_marks_stop = ord('v')
block_from_begining = ord('B')
block_till_end = ord('E')
delete_block = ord('d')

# Quitting and applying edits
quit_program = ord('q')
begin_edits = ord('o')

# Interface keys
current_time = ord('t')

# volume controls
volume_up = ord('u')
volume_down = ord('d')



jump_time = 5
play_speed_rate = 0.5


volume = 1
volume_increments = 0.5
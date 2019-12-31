import curses

play_speed_up = curses.KEY_UP
play_speed_down = curses.KEY_DOWN
jump_back = curses.KEY_LEFT
jump_forward = curses.KEY_RIGHT
play_pause = ord(' ')
mark_create_new = ord('n')
mark_save_current = ord('s')
mark_record_start_position = ord('b')
mark_record_end_position = ord('e')
quit_program = ord('q')
begin_edits = ord('o')
cycle_through_marks = ord('c')
cycle_through_marks_stop = ord('v')
normal_speed = ord('z')
current_time = ord('t')
jump_specific = ord('j')
volume_up = ord('u')
volume_down = ord('d')
block_from_begining = ord('B')
block_till_end = ord('E')



jump_time = 5
play_speed_rate = 0.25


volume = 1
volume_increments = 0.5
#!/usr/bin/python3
 
# adapted from https://github.com/recantha/EduKit3-RC-Keyboard/blob/master/rc_keyboard.py
 
import sys, termios, tty, os, time
 
 
def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
 
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch
 
def run():
    while True:
        char = getch()
    
        if (char == "q"):
            print("Stop!")
            exit(0)

        else:
            print(char)
    
        # if (char == "a"):
        #     print("Left pressed")
        #     time.sleep(button_delay)
    
        # elif (char == "d"):
        #     print("Right pressed")
        #     time.sleep(button_delay)
    
        # elif (char == "w"):
        #     print("Up pressed")
        #     time.sleep(button_delay)
    
        # elif (char == "s"):
        #     print("Down pressed")
        #     time.sleep(button_delay)
    
        # elif (char == "1"):
        #     print("Number 1 pressed")
        #     time.sleep(button_delay)


if __name__ == "__main__":
    button_delay = 0.1
    run()
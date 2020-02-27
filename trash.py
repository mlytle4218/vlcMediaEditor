#!/usr/bin/env python3

import math, sys, subprocess, syslog, pickle, json, shlex


class State():
    marks = []
    duration  = 0 

def milliseconds_to_hms(millis):
    millis = int(millis)
    seconds = (millis/1000)%60
    part_of_seconds = int((seconds - math.floor(seconds)) * 1000)
    seconds = int(seconds)
    minutes = (millis/(1000*60))%60
    minutes = int(minutes)
    hours = int(millis/(1000*60*60))%24
    time = ''
    if hours >= 1:# and minutes >= 1:
        time = ("{}:{:02d}:{:02d}.{}".format(
            hours, minutes, seconds, part_of_seconds))
    elif minutes >= 1:
        time = ("{:02d}:{:02d}.{}".format(
            minutes, seconds, part_of_seconds))
    else:
        time = ("{:02d}.{}".format(seconds, part_of_seconds))

    return time

def get_file_length(input_file):
    time = 0
    command  = [ 'ffmpeg','-i',input_file,'-f','null','-' ]
    result = subprocess.run(command, stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    lines = result.stdout.decode('utf-8').splitlines()
    for line in lines:
        for word in line.split():
            if word.startswith('time='):
                time_temp = word.split("=")[1].split(":")
                time = int(time_temp[0]) * 3600 + int(time_temp[1])*60 + round(float(time_temp[2]))
    return time


def read_state_information(state_file):
    """
    Method to read the saved information about a file from a file named like
    the original with a .state extension
    """
    try:
        state = open(state_file, 'rb')
        out = pickle.load(state)
        print('Duration {}'.format(out.duration))
        print(('Duration {}'.format(milliseconds_to_hms(out.duration))))
        for each in out.marks:
            print("{}  to {}".format(
                each.start,
                each.end
            ))
            print("{} to {}".format(
                milliseconds_to_hms(out.duration * each.start), 
                milliseconds_to_hms(out.duration * each.end)
                ))
        
    except IOError:
       print("No file found")


# function to find the resolution of the input video file
def findSampleRate(inputFile):
    cmd = ['ffprobe','-v','quiet','-print_format','json','-show_streams',inputFile]
    result = subprocess.check_output(cmd).decode('utf-8')
    result = json.loads(result)
    # return result['streams'][0]['sample_rate']
    return result['streams'][0]['bit_rate']


def main():
    print('hi')
    # result = get_file_length(sys.argv[1])
    # print(result)
    # syslog.syslog(syslog.LOG_INFO, "log_info")
    # read_state_information(sys.argv[1])
    print(findSampleRate(sys.argv[1]))



if __name__ == "__main__":
    main()
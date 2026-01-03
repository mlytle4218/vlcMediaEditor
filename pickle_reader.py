import sys
import pickle
# from player2 import State


class State():
    def __init__(self):
        marks = []
        duration = 0

def main(state_file):

    try:
        state = open(state_file, 'rb')
        results = pickle.load(state)
        print(results.duration)
        for mark in results.marks:
            print(mark)
    except IOError:
        self.log("No state file found")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print("duh")
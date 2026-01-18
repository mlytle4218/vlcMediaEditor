import pickletools
import sys
import pickle
from mark import Mark

class State():
    def __init__(self):
        marks = []
        duration = 0

    def __str__(self):
        result = "{}\n".format(self.duration)

        for m in self.marks:
            result += str(m.start) +":"+ str(m.end) + "\n"
        return result

def use(pickle_file):
    with open(pickle_file, 'rb') as f:
        pickletools.dis(f)


def load(pickle_file):
    state = open(pickle_file, 'rb')
    data = pickle.load(state)
    print(data)
    data.marks.clear()
    all = [(0,0.15),(0.2,0.3),(0.5,0.8)]
    for each in all:
        temp = Mark()
        temp.start = each[0]
        temp.end = each[1]
        data.marks.append(temp)
    # print(data)
    return data



def load_old(pickle_file) -> State:  
    state = open(pickle_file, 'rb')
    data = State()
    data = pickle.load(state)
    first = data.marks[0]
    second = data.marks[1]
    # print(first)
    # print(second)
    # print(data.duration)

    # print("0-start " + str(first).split(":")[0])
    # print("0-end "  + str(second).split(":")[0])

    # print("1-start " + str(first).split(":")[1])
    # print("1-end " + str(second).split(":")[1])


    first_mark = Mark()
    first_mark.start = float(str(first).split(":")[0])
    first_mark.end = float(str(second).split(":")[0])
    # print(first_mark)

    second_mark = Mark()
    second_mark.start = float(str(first).split(":")[1])
    second_mark.end = float(str(second).split(":")[1])
    # print(second_mark)

    # print("^^^^^^^^^^^^^^^^^^^^^")
    data.marks[0] = first_mark
    data.marks[1] = second_mark
 
    for m in data.marks:
        print(m.start)
        print(m.end)
    print(data.duration)
    return 
    
def print_out(pickle_file):
    state = open(pickle_file, 'rb')
    data = State()
    data = pickle.load(state)
    for m in data.marks:
        print(str(m.start) +":"+ str(m.end))
    print(data.duration)

def save_old(st, pickle_file):
    state = open(pickle_file, 'wb')
    pickle.dump(st, state)

def save(data, pickle_file):
    state = open(pickle_file+".new", 'wb')
    print(type(data))
    pickle.dump(data, state)



if __name__ == '__main__':
    if len(sys.argv) == 2:
        # print_out(sys.argv[1])
        # use(sys.argv[1])
        result = load(sys.argv[1])
        save(result, sys.argv[1])
    else:
        print("requires a file to edit")
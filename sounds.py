#!/usr/bin/env python3 
import generate_tone
import config

def error_sound(_volume=1):
    gt = generate_tone.Generator()
    notes=[]
    frequency = 400.0
    time = 0.3
    """
    play an error tone
    """
    notes.append(generate_tone.Note(
        frequency,
        time
    ))

    gt.generate_tone(notes, volume=_volume)


def mark_start_sound(_volume=1):
    gt = generate_tone.Generator()
    notes = []
    frequency = 400.0
    time = 0.3
    """
    play a set of tones going up
    """
    number = 5
    for itr in range(number):
        notes.append(generate_tone.Note(
            frequency*(1+(itr/10)),
            time/number
        ))

    gt.generate_tone(notes, volume=_volume)



def mark_end_sound(_volume=1):
    gt = generate_tone.Generator()
    notes= []
    frequency = 400.0
    time = 0.3
    """
    play a set of quick tones going down
    """
    number = 5
    for itr in range(number):
        notes.append(generate_tone.Note(
            frequency*( 1 - (itr/10) ),
            time/number
        ))
    gt.generate_tone(notes, volume=_volume)


if __name__ == "__main__":
    mark_start_sound()
    
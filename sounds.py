import generate_tone
import config

gt = generate_tone.Generator()

def error_sound(_volume=1):
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


def mark_start_sound():
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

    gt.generate_tone(notes)



def mark_end_sound():
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
    gt.generate_tone(notes)


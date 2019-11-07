import math, struct
import pyaudio
import generate_tone

gt = generate_tone.Generator()

FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100

def data_for_freq(frequency: float, time: float = None):
    """get frames for a fixed frequency for a specified time or
    number of frames, if frame_count is specified, the specified
    time is ignored"""
    frame_count = int(RATE * time)

    remainder_frames = frame_count % RATE
    wavedata = []

    for i in range(frame_count):
        a = RATE / frequency  # number of frames per wave
        b = i / a
        # explanation for b
        # considering one wave, what part of the wave should this be
        # if we graph the sine wave in a
        # displacement vs i graph for the particle
        # where 0 is the beginning of the sine wave and
        # 1 the end of the sine wave
        # which part is "i" is denoted by b
        # for clarity you might use
        # though this is redundant since math.sin is a looping function
        # b = b - int(b)

        c = b * (2 * math.pi)
        # explanation for c
        # now we map b to between 0 and 2*math.PI
        # since 0 - 2*PI, 2*PI - 4*PI, ...
        # are the repeating domains of the sin wave (so the decimal values will
        # also be mapped accordingly,
        # and the integral values will be multiplied
        # by 2*PI and since sin(n*2*PI) is zero where n is an integer)
        d = math.sin(c) * 32767
        e = int(d)
        wavedata.append(e)

    for i in range(remainder_frames):
        wavedata.append(0)

    number_of_bytes = str(len(wavedata))
    wavedata = struct.pack(number_of_bytes + 'h', *wavedata)

    return wavedata

def error_sound():
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

    gt.generate_tone(notes)

def error_sound_old():
    frequency = 400.0
    time = 0.3
    """
    play an error tone
    """
    frames = data_for_freq(frequency, time)

    stream = pyaudio.PyAudio().open(format=FORMAT, channels=CHANNELS,
                                rate=RATE, output=True)
    stream.write(frames)
    stream.stop_stream()
    stream.close()

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

def mark_start_sound_old():
    frequency = 400.0
    time = 0.3
    """
    play a set of tones going up
    """
    number = 5
    frames_total = bytes()
    for itr in range(number):
        frames = data_for_freq(frequency*(1+(itr/10)), time/number)
        frames_total += frames

    gt.generate_tone(notes)
    
    # log(frames_total)

    stream = pyaudio.PyAudio().open(format=FORMAT, channels=CHANNELS,
                                rate=RATE, output=True)
    stream.write(frames_total)
    stream.stop_stream()
    stream.close()

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

def mark_end_sound_old():
    frequency = 400.0
    time = 0.3
    """
    play a set of quick tones going down
    """
    number = 5
    frames_total = bytes()
    for itr in range(number):
        freq = frequency*( 1 - (itr/10) )
        split = time/number

        frames = data_for_freq(freq, split)
        frames_total += frames
    stream = pyaudio.PyAudio().open(format=FORMAT, channels=CHANNELS,
                                rate=RATE, output=True)
    stream.write(frames_total)
    stream.stop_stream()
    stream.close()
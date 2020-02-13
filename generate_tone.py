#!/usr/bin/env python3

import math
import numpy as np
import pyaudio
import ctypes
import datetime, time


# this incorporated from https://stackoverflow.com/questions/7088672/pyaudio-working-but-spits-out-error-messages-each-time
ERROR_HANDLER_FUNC = ctypes.CFUNCTYPE(
    None, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p)
# this incorporated from https://stackoverflow.com/questions/7088672/pyaudio-working-but-spits-out-error-messages-each-time


class Note:

    def __init__(self, frequency, duration):
        self.frequency = frequency
        self.duration = duration


class Generator:

    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate

    def log(self, input):
        input = str(input)
        with open("log.txt", "a") as myfile:
            string = datetime.datetime.fromtimestamp(
                time.time()).strftime('%Y-%m-%d %H:%M:%S')
            string = string + ' - ' + input + '\n'
            myfile.write(string)

    # this incorporated from https://stackoverflow.com/questions/7088672/pyaudio-working-but-spits-out-error-messages-each-time
    # def py_error_handler(self, filename, line, function, err, fmt):
    def py_error_handler(self, filename, line, function, err, fmt):
        self.log(fmt)

    def generate_tone(self, notes, volume=1.0):
        result = []
        for note in notes:
            samples = self.tone(note.frequency, note.duration)
            result.extend(samples)
        result = np.asarray(result) * volume
        self.play( np.array(result).tobytes())
        # return np.array(result).tobytes()

    def play(self, tones):
        # this incorporated from https://stackoverflow.com/questions/7088672/pyaudio-working-but-spits-out-error-messages-each-time
        c_error_handler = ERROR_HANDLER_FUNC(self.py_error_handler)
        asound = ctypes.cdll.LoadLibrary('libasound.so')
        asound.snd_lib_error_set_handler(c_error_handler)
        # this incorporated from https://stackoverflow.com/questions/7088672/pyaudio-working-but-spits-out-error-messages-each-time
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paFloat32,
                        channels=1,
                        rate=self.sample_rate,
                        output=True)
        stream.write(tones)
        stream.stop_stream()
        stream.close()
        p.terminate()

    def tone(self, frequency, duration):
        return (
            np.sin(
                2*np.pi*np.arange(
                    self.sample_rate*duration
                )*frequency/self.sample_rate
            )
        ).astype(np.float32)


if __name__ == "__main__":
    generater = Generator()

    notes = []
    notes.append(Note(440, 0.25))
    notes.append(Note(540, 0.25))

    generater.generate_tone(notes, 1.0)

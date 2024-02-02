from pygame import mixer, _sdl2 as devicer
import time
import pyaudio
import keyboard
from scipy.io import wavfile
import numpy as np
import whisper
import requests
import random
import os
mixer.init()  # Initialize the mixer, this will allow the next command to work

# Returns playback devices, Boolean value determines whether they are Input or Output devices.

inputs = devicer.audio.get_audio_device_names(True)
outputs = devicer.audio.get_audio_device_names(False)
print("Inputs:", inputs)
print("Outputs:", outputs)
mixer.quit()  # Quit the mixer as it's initialized on your main playback device

url = "https://kawaify.damaral.my.id"

vb = 'CABLE Input (VB-Audio Virtual Cable)'

if vb not in outputs:
    print("VB Microphone is not installed!")
    exit(1)

# Initialize it with the correct device
mixer.init(devicename=vb)


model = whisper.load_model("small", in_memory=True)


class Recorder():
    def __init__(self, filename):
        self.audio_format = pyaudio.paInt16
        self.channels = 1
        self.sample_rate = 44100
        self.chunk = int(0.03*self.sample_rate)
        self.filename = filename
        self.START_KEY = 'n'
        self.STOP_KEY = 'm'
        self.start_time = time.time()

    def record(self):
        print("Start Listening...")
        self.start_time = time.time()
        recorded_data = []
        p = pyaudio.PyAudio()

        stream = p.open(format=self.audio_format, channels=self.channels,
                        rate=self.sample_rate, input=True,
                        frames_per_buffer=self.chunk)
        while(True):
            data = stream.read(self.chunk)
            recorded_data.append(data)
            if keyboard.is_pressed(self.STOP_KEY):
                print("Stop Listening...")
                # stop and close the stream
                stream.stop_stream()
                stream.close()
                p.terminate()
                # convert recorded data to numpy array
                recorded_data = [np.frombuffer(
                    frame, dtype=np.int16) for frame in recorded_data]
                wav = np.concatenate(recorded_data, axis=0)
                wavfile.write(self.filename, self.sample_rate, wav)
                self.start_time = time.time()

                print(f"[{time.time() - self.start_time}s]Wav saved...")
                result = model.transcribe("buffer.wav", language="id")
                print(f"[{time.time() - self.start_time}s]Transcribing...")
                detected = result["text"]

                print("Detected : " + detected)

                req = requests.get(f"{url}/transcribe/" + detected)

                translate = req.text

                print(f"[{time.time() - self.start_time}s]Result : " + translate)

                print("Generating voice... ")

                req = requests.get(f"{url}/generate/" + translate)

                save = f'voices/{random.randint(0,9999)}.wav'

                with open(save, 'wb') as f:
                    f.write(req.content)

                mixer.music.load(save)  # Load the mp3
                mixer.music.play()  # Play it
                print(f"[{time.time() - self.start_time}s]Playing " + save)
                while mixer.music.get_busy():  # wait for music to finish playing
                    time.sleep(1)
                else:
                    mixer.music.unload()
                print(f"[{time.time() - self.start_time}s]Finished")

                os.remove(save)
                break

    def listen(self):

        while True:
            if keyboard.is_pressed('p'):
                print('quit !')
                exit(0)
            if keyboard.is_pressed(self.START_KEY):
                self.record()
                break


recorder = Recorder("buffer.wav")
print(
    f"Press `{recorder.START_KEY}` to start and `{recorder.STOP_KEY}` to stop!, p  to quit!")

print("press ctrl+c to quit")

while True:
    recorder.listen()
    print("Finish, start again!")

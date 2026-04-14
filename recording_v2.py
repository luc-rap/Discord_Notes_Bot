# Sources
# - https://stackoverflow.com/a/51554530
# - https://stackoverflow.com/questions/59665469/pyaudio-how-to-capture-microphone-and-system-sounds-in-a-single-stream
# Retrieved 2026-04-14, License - CC BY-SA 4.0

import pyaudiowpatch as pyaudio
import wave
import math
import threading
import numpy as np

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000
CHUNK = 2048
RECORD_SECONDS = 10
WAVE_OUTPUT_FILENAME = "recordedFile.wav"
MIC_INDEX = 1
SYS_INDEX = 13

audio = pyaudio.PyAudio()

mic_frames = []
sys_frames = []

#for i in range(p.get_device_count()):
#    d = p.get_device_info_by_index(i)
#    print(i, d["name"], "in:", d["maxInputChannels"], "out:", d["maxOutputChannels"], "rate:", d["defaultSampleRate"])

#print("----------------------record device list---------------------")
#info = audio.get_host_api_info_by_index(0)
#numdevices = info.get('deviceCount')
#for i in range(0, numdevices):
#        if (audio.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
#            print("Input Device id ", i, " - ", audio.get_device_info_by_host_api_device_index(0, i).get('name'))


#print("-------------------------------------------------------------")

#index = int(input())
#print("recording via index "+str(index))
def record_mic():
    mic_stream = audio.open(format=FORMAT, channels=1,
                    rate=RATE, input=True,input_device_index = MIC_INDEX, 
                    frames_per_buffer=CHUNK)
    for _ in range(int(RATE / CHUNK * RECORD_SECONDS)):
        mic_frames.append(mic_stream.read(CHUNK, exception_on_overflow=False))
    mic_stream.stop_stream()
    mic_stream.close()

def record_sys():
    sys_stream = audio.open(format=FORMAT, channels=2,
                    rate=RATE, input=True,input_device_index = SYS_INDEX,
                    frames_per_buffer=CHUNK)
    for _ in range(int(RATE / CHUNK * RECORD_SECONDS)):
        sys_frames.append(sys_stream.read(CHUNK, exception_on_overflow=False))
    sys_stream.stop_stream()
    sys_stream.close()

 
t1 = threading.Thread(target=record_mic)
t2 = threading.Thread(target=record_sys)

t1.start()
t2.start()
t1.join()
t2.join()

audio.terminate()
 
mic = np.frombuffer(b"".join(mic_frames), dtype=np.int16)
sysa = np.frombuffer(b"".join(sys_frames), dtype=np.int16)

if len(sysa) > len(mic):
    mic = np.pad(mic, (0, len(sysa) - len(mic)))
elif len(mic) > len(sysa):
    sysa = np.pad(sysa, (0, len(mic) - len(sysa)))

mic = mic.astype(np.float32) * 0.5
sysa = sysa.astype(np.float32) * 0.5

mixed = np.clip(mic + sysa, -32768, 32767).astype(np.int16)

wf = wave.open("mixed.wav", "wb")
wf.setnchannels(1)
wf.setsampwidth(2)
wf.setframerate(RATE)
wf.writeframes(mixed.tobytes())
wf.close()

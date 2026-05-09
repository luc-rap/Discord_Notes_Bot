# Sources
# - https://stackoverflow.com/a/51554530
# - https://stackoverflow.com/questions/59665469/pyaudio-how-to-capture-microphone-and-system-sounds-in-a-single-stream
# Retrieved 2026-04-14, License - CC BY-SA 4.0

import pyaudiowpatch as pyaudio
import wave
import math
import threading
import numpy as np
from datetime import datetime
import time

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000
CHUNK = 2048
MIC_INDEX = 1
SYS_INDEX = 13

def record_and_mix_audio(duration=10, mic_index=MIC_INDEX, sys_index=SYS_INDEX):
    audio = pyaudio.PyAudio()
    stop_event = threading.Event()

    mic_frames = []
    sys_frames = []

    def record_mic():
        mic_stream = audio.open(format=FORMAT, channels=1,
                        rate=RATE, input=True,input_device_index = mic_index, 
                        frames_per_buffer=CHUNK)
        while not stop_event.is_set():
            mic_frames.append(mic_stream.read(CHUNK, exception_on_overflow=False))
        mic_stream.stop_stream()
        mic_stream.close()

    def record_sys():
        sys_stream = audio.open(format=FORMAT, channels=2,
                        rate=RATE, input=True,input_device_index = sys_index,
                        frames_per_buffer=CHUNK)
        while not stop_event.is_set():
            sys_frames.append(sys_stream.read(CHUNK, exception_on_overflow=False))
        sys_stream.stop_stream()
        sys_stream.close()

    t1 = threading.Thread(target=record_mic)
    t2 = threading.Thread(target=record_sys)

    t1.start()
    t2.start()
    print("Recording started.")
    input("Type 'stop' and press Enter to end recording: ")
    stop_event.set()
    t1.join()
    t2.join()

    audio.terminate()
 
    mic = np.frombuffer(b"".join(mic_frames), dtype=np.int16)

    sysa = np.frombuffer(b"".join(sys_frames), dtype=np.int16)
    sysa = sysa[:len(sysa) - (len(sysa) % 2)]
    sysa = sysa.reshape(-1, 2).mean(axis=1).astype(np.int16)

    n = min(len(mic), len(sysa))
    mic = mic[:n]
    sysa = sysa[:n]

    mic = mic.astype(np.float32) * 0.5
    sysa = sysa.astype(np.float32) * 0.5
    mixed = np.clip(mic + sysa, -32768, 32767).astype(np.int16)

    current_date = datetime.now().strftime("%Y-%m-%d")
    filename = f"recordings/mixed_{current_date}.wav"
    wf = wave.open(filename, "wb")
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(RATE)
    wf.writeframes(mixed.tobytes())
    wf.close()
    
    return filename

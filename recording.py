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
import os

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000
CHUNK = 2048
MIC_INDEX = 1
SYS_INDEX = 13
FLUSH = 500

os.makedirs("recordings", exist_ok=True)

def record_and_mix_audio(mic_index=MIC_INDEX, sys_index=SYS_INDEX):
    audio = pyaudio.PyAudio()
    stop_event = threading.Event()

    current_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    mic_temp = f"recordings/mic_temp_{current_date}.raw"
    sys_temp = f"recordings/sys_temp_{current_date}.raw"
    output = f"recordings/mixed_{current_date}.wav"

    def record_mic():
        stream = audio.open(format=FORMAT, channels=1, rate=RATE,
                            input=True, input_device_index=mic_index,
                            frames_per_buffer=CHUNK)
        buffer = []
        count = 0
        with open(mic_temp, "wb") as f:
            while not stop_event.is_set():
                buffer.append(stream.read(CHUNK, exception_on_overflow=False))
                count += 1
                if count >= FLUSH:
                    f.write(b"".join(buffer))
                    buffer = []
                    count = 0
            if buffer:
                f.write(b"".join(buffer))
        stream.stop_stream()
        stream.close()

    def record_sys():
        stream = audio.open(format=FORMAT, channels=2, rate=RATE,
                            input=True, input_device_index=sys_index,
                            frames_per_buffer=CHUNK)
        buffer = []
        count = 0
        with open(sys_temp, "wb") as f:
            while not stop_event.is_set():
                buffer.append(stream.read(CHUNK, exception_on_overflow=False))
                count += 1
                if count >= FLUSH:
                    f.write(b"".join(buffer))
                    buffer = []
                    count = 0
            if buffer:
                f.write(b"".join(buffer))
        stream.stop_stream()
        stream.close()

    t1 = threading.Thread(target=record_mic)
    t2 = threading.Thread(target=record_sys)

    t1.start()
    t2.start()
    print("Recording starts in...")
    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)

    print("Recording started.")
    input("Type 'stop' and press Enter to end recording: ")
    stop_event.set()
    t1.join()
    t2.join()
    audio.terminate()
    
    print(f"Mic temp size: {os.path.getsize(mic_temp)} bytes = ~{os.path.getsize(mic_temp)/RATE/2:.1f}s")
    print(f"Sys temp size: {os.path.getsize(sys_temp)} bytes = ~{os.path.getsize(sys_temp)/RATE/4:.1f}s")
    
    print("Mixing audio...")
    output = mix_files(mic_temp, sys_temp, output)

    # clean up temp files
    #os.remove(mic_temp)
    #os.remove(sys_temp)
    
    return output
 
def mix_files(mic_path, sys_path, output_path):
    with open(mic_path, "rb") as f:
        mic = np.frombuffer(f.read(), dtype=np.int16).astype(np.float32)
    
    with open(sys_path, "rb") as f:
        sys_arr = np.frombuffer(f.read(), dtype=np.int16)
        sys_arr = sys_arr[:len(sys_arr) - (len(sys_arr) % 2)]
        sys_arr = sys_arr.reshape(-1, 2).mean(axis=1).astype(np.float32)

    n = min(len(mic), len(sys_arr))
    mic = mic[:n] * 0.5
    sys_arr = sys_arr[:n] * 0.5

    mixed = np.clip(mic + sys_arr, -32768, 32767).astype(np.int16)

    with wave.open(output_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(RATE)
        wf.writeframes(mixed.tobytes())

    print(f"Saved {output_path}")
    return output_path

# Sources
# - https://stackoverflow.com/a/51554530
# - https://stackoverflow.com/questions/59665469/pyaudio-how-to-capture-microphone-and-system-sounds-in-a-single-stream
# Retrieved 2026-04-14, License - CC BY-SA 4.0

import pyaudiowpatch as pyaudio
import wave
import math
import threading
import queue
import traceback
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
    error_event = threading.Event()
    exception_queue = queue.Queue()

    def validate_device(index, requested_channels, name):
        try:
            info = audio.get_device_info_by_index(index)
        except Exception as exc:
            raise ValueError(f"{name} device index {index} is invalid: {exc}") from exc

        max_channels = int(info.get("maxInputChannels", 0))
        if max_channels < 1:
            raise ValueError(f"{name} device index {index} has no input channels.")

        if max_channels < requested_channels:
            print(f"[{name}] device supports only {max_channels} channels, falling back to {max_channels}.")
            return max_channels

        return requested_channels

    def open_stream(device_index, channels, name):
        last_exc = None
        for attempt in range(1, 4):
            try:
                return audio.open(format=FORMAT, channels=channels, rate=RATE,
                                  input=True, input_device_index=device_index,
                                  frames_per_buffer=CHUNK)
            except Exception as exc:
                last_exc = exc
                print(f"[{name}] failed to open stream (attempt {attempt}/3): {exc}")
                time.sleep(0.5)
        raise RuntimeError(f"Unable to open {name} stream after 3 attempts: {last_exc}")

    def thread_exception(name, exc):
        error_event.set()
        stop_event.set()
        exception_queue.put((name, traceback.format_exc()))
        print(f"[{name}] thread error: {exc}")

    mic_channels = validate_device(mic_index, 1, "Mic")
    sys_channels = validate_device(sys_index, 2, "System")

    def record_mic():
        stream = None
        try:
            stream = open_stream(mic_index, mic_channels, "Mic")
            buffer = []
            count = 0
            with open(mic_temp, "wb") as f:
                while not stop_event.is_set() and not error_event.is_set():
                    try:
                        data = stream.read(CHUNK, exception_on_overflow=False)
                    except Exception as exc:
                        raise RuntimeError(f"Mic read failed: {exc}") from exc
                    buffer.append(data)
                    count += 1
                    if count >= FLUSH:
                        f.write(b"".join(buffer))
                        buffer = []
                        count = 0
                if buffer:
                    f.write(b"".join(buffer))
        except Exception as exc:
            thread_exception("Mic", exc)
        finally:
            if stream is not None:
                try:
                    stream.stop_stream()
                    stream.close()
                except Exception as cleanup_exc:
                    print(f"[Mic] cleanup failed: {cleanup_exc}")

    def record_sys():
        stream = None
        try:
            stream = open_stream(sys_index, sys_channels, "System")
            buffer = []
            count = 0
            with open(sys_temp, "wb") as f:
                while not stop_event.is_set() and not error_event.is_set():
                    try:
                        data = stream.read(CHUNK, exception_on_overflow=False)
                    except Exception as exc:
                        raise RuntimeError(f"System read failed: {exc}") from exc
                    buffer.append(data)
                    count += 1
                    if count >= FLUSH:
                        f.write(b"".join(buffer))
                        buffer = []
                        count = 0
                if buffer:
                    f.write(b"".join(buffer))
        except Exception as exc:
            thread_exception("System", exc)
        finally:
            if stream is not None:
                try:
                    stream.stop_stream()
                    stream.close()
                except Exception as cleanup_exc:
                    print(f"[System] cleanup failed: {cleanup_exc}")

    current_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    mic_temp = f"recordings/mic_temp_{current_date}.raw"
    sys_temp = f"recordings/sys_temp_{current_date}.raw"
    output = f"recordings/mixed_{current_date}.wav"

    def wait_for_stop():
        try:
            input("Type 'stop' and press Enter to end recording: ")
        except Exception:
            pass
        stop_event.set()

    prompt_thread = threading.Thread(target=wait_for_stop, daemon=True)
    t1 = threading.Thread(target=record_mic)
    t2 = threading.Thread(target=record_sys)

    t1.start()
    t2.start()
    print("Recording starts in...")
    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)

    print("Recording started.")
    prompt_thread.start()
    while not stop_event.is_set() and not error_event.is_set():
        time.sleep(0.1)

    stop_event.set()
    t1.join()
    t2.join()
    audio.terminate()

    if not exception_queue.empty():
        while not exception_queue.empty():
            name, tb = exception_queue.get()
            print(f"{name} thread exception:\n{tb}")
        raise RuntimeError("Recording failed because one or more threads encountered an error.")

    mic_size = os.path.getsize(mic_temp)
    sys_size = os.path.getsize(sys_temp)
    if mic_size == 0 or sys_size == 0:
        raise RuntimeError(
            f"Recording completed, but one of the raw files is empty: mic={mic_size}, sys={sys_size}."
        )

    print(f"Mic temp size: {mic_size} bytes = ~{mic_size/RATE/2:.1f}s")
    print(f"Sys temp size: {sys_size} bytes = ~{sys_size/RATE/4:.1f}s")

    print("Mixing audio...")
    output = mix_files(mic_temp, sys_temp, output, sys_channels)

    # clean up temp files
    #os.remove(mic_temp)
    #os.remove(sys_temp)
    
    return output
 
def mix_files(mic_path, sys_path, output_path, sys_channels=2):
    with open(mic_path, "rb") as f:
        mic = np.frombuffer(f.read(), dtype=np.int16).astype(np.float32)
    
    with open(sys_path, "rb") as f:
        sys_arr = np.frombuffer(f.read(), dtype=np.int16)

    if sys_channels > 1:
        pair_count = len(sys_arr) // sys_channels
        sys_arr = sys_arr[:pair_count * sys_channels]
        sys_arr = sys_arr.reshape(-1, sys_channels).mean(axis=1).astype(np.float32)
    else:
        sys_arr = sys_arr.astype(np.float32)

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

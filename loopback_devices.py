import pyaudiowpatch as pyaudio

p = pyaudio.PyAudio()

for i in range(p.get_device_count()):
    d = p.get_device_info_by_index(i)
    if d.get('isLoopbackDevice'):
        print(f"{i}: {d['name']} — hostApi: {d['hostApi']}")
p.terminate()

def get_default_loopback_index():
    """Always finds the loopback device for whatever the current default output is."""
    p = pyaudio.PyAudio()
    try:
        wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
        default_output = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
        print(f"Default output: {default_output['name']}")
        
        for loopback in p.get_loopback_device_info_generator():
            if default_output["name"] in loopback["name"]:
                print(f"Found loopback: {loopback['name']} at index {loopback['index']}")
                return int(loopback["index"]), int(loopback["maxInputChannels"])
        
        raise RuntimeError("No loopback device found for default output")
    finally:
        p.terminate()
        
sys_index, sys_channels_detected = get_default_loopback_index()
print(f"Detected loopback index: {sys_index}, channels: {sys_channels_detected}")
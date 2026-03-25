from faster_whisper import WhisperModel
import json
import os

USER_MAP = json.loads(os.getenv("USER_MAP", "{}"))

model = WhisperModel("medium", device="cpu", compute_type="int8")

segments, info = model.transcribe("recordings/452538681937625088.mp3")
print(list(segments))


#result = model.transcribe("recordings/452538681937625088.mp3")
#with open("transcription.txt", "w") as f:
#    f.write(result["text"])
#print(result["text"])
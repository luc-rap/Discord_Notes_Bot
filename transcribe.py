from faster_whisper import WhisperModel
from dotenv import load_dotenv

load_dotenv()

model = WhisperModel("medium", device="cpu", compute_type="int8")

print("Starting transcription...")
segments, info = model.transcribe(audio="mixed2.wav", language="en", initial_prompt="Dungeons and Dragons session.", log_progress=True)
print("Saving transcription to file...")
with open("transcript_2.txt", "w") as f:
    for segment in segments:
        f.write(segment.text + "\n")    
print("Transcription saved to transcript_2.txt")
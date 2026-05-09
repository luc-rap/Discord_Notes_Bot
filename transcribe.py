from faster_whisper import WhisperModel
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

model = WhisperModel("medium", device="cpu", compute_type="int8")

def start_transcription(filename):
    print("Starting transcription...")
    segments, info = model.transcribe(audio=filename, language="en", initial_prompt="Dungeons and Dragons session.", log_progress=True)
    print("Saving transcription to file...")
    # transcript name - transcript_current_date
    current_date = datetime.now().strftime("%Y-%m-%d")
    transcript_filename = f"transcripts/transcript_{current_date}.txt"
    with open(transcript_filename, "w") as f:
        for segment in segments:
            f.write(segment.text + "\n")    
    print(f"Transcription saved to {transcript_filename}.")
    return transcript_filename
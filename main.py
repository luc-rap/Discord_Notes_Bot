import recording
import transcribe
import summarize
from datetime import datetime

# 1. Start recording -> recording filename - mixed_current_date.wav
# 2. Transcribe the recording and save to file - transcript_current_date.txt
# 3. Summarize the transcript and save to file - summary_current_date.txt

if __name__ == "__main__":
    current_date = datetime.now().strftime("%Y-%m-%d")
    # Record audio
    print("Starting recording...")
    filename = recording.record_and_mix_audio()
    print(f"Recording saved to {filename}")
    
    #filename = f"recordings/mixed_2026-05-24_11-09-07.wav"

    # Transcribe
    transcript_filename = transcribe.start_transcription(filename)
    #transcript_filename = f"transcripts/transcript_2026-05-24.txt"

    with open(transcript_filename, "r") as f:
        transcript = f.read()
    print(f"Loaded transcript from {transcript_filename}")

    # Summarize
    print("Starting summarization...")
    #context = summarize.query_vector_db(transcript)
    summary_chunks = summarize.summarize_session(transcript)
    filename = f"notes/summary_{current_date}.txt"
    print("Process complete.")
    with open(filename, "w") as f:
        f.write("\n\n---\n\n".join(summary_chunks))
    print(f"Summary saved to {filename}")


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
    #transcript_filename = f"transcripts/transcription_diarized.txt"

    with open(transcript_filename, "r") as f:
        transcript = f.read()
    print(f"Loaded transcript from {transcript_filename}")

    # Summarize
    print("Starting summarization...")
    #context = summarize.query_vector_db(transcript)
    # In the transcript, replace: SPEAKER_00 with "DM", SPEAKER_01 with "Faelynn", SPEAKER_03 with "Keira" and SPEAKER_04 with "Dochanar"
    #transcript = transcript.replace("SPEAKER_00", "DM").replace("SPEAKER_02", "Faelynn").replace("SPEAKER_01", "Keira").replace("SPEAKER_03", "Erwan").replace("SPEAKER_04", "Dochanar")
    summary_chunks = summarize.summarize_session(transcript)
    filename = f"notes/summary_{current_date}.txt"
    print("Process complete.")
    with open(filename, "w") as f:
        f.write("\n\n---\n\n".join(summary_chunks))
    print(f"Summary saved to {filename}")


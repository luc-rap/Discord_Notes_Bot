from faster_whisper import WhisperModel
import json
import os
from dotenv import load_dotenv

load_dotenv()

USER_MAP = json.loads(os.getenv("USER_MAP", "{}"))


METADATA_PATH = os.path.join("recordings", "recording_metadata.json")
if os.path.exists(METADATA_PATH):
    with open(METADATA_PATH, "r", encoding="utf-8") as mf:
        RECORDING_METADATA = json.load(mf)
else:
    RECORDING_METADATA = {}

USER_OFFSETS = {}
if RECORDING_METADATA.get("users"):
    for uid, udata in RECORDING_METADATA["users"].items():
        # Prefer explicit per-user offset. Fallback to zero.
        USER_OFFSETS[str(uid)] = float(udata.get("offset", 0.0))

print("Loaded user offsets:", USER_OFFSETS)

model = WhisperModel("medium", device="cpu", compute_type="int8")

#segments, info = model.transcribe("recordings/<USER_ID>.mp3")
#print(list(segments))

def transcribe_one_user(audio_path, user_id):
    offset = USER_OFFSETS.get(str(user_id), 0.0)
    segments, info = model.transcribe(audio_path)
    #for seg in segments:
        #print(f"[{user_id}] {seg.start:.1f}s → {seg.end:.1f}s : {seg.text.strip()}")
    return [
        {
            "user_id": user_id,
            "start": offset + seg.start,
            "end": offset + seg.end,
            "text": seg.text.strip()
        }
        for seg in segments
        if seg.text.strip()  # skip empty segments
        
    ] 

def complete_transcription(): # merging the transcription of all players (by timestamp)
    all_segments = []
    for filename in os.listdir("recordings"):
        if filename.endswith(".mp3"):
            user_id = filename.split(".")[0]  # filename is "USERID.mp3"
            audio_path = os.path.join("recordings", filename)
            user_segments = transcribe_one_user(audio_path, user_id)
            all_segments.extend(user_segments)
            print("Transcribed", filename)
    all_segments = fix_merging_segments(all_segments)  # fix small gaps between segments of the same user       
    all_segments.sort(key=lambda x: x["start"])  # sort by start time
    # build the final transcript with user names
    final = []
    for seg in all_segments:
        user = seg["user_id"]
        name = USER_MAP.get(user, f"User {user}")
        final.append(f"{name}: {seg['text']}")
    return "\n".join(final)

def fix_merging_segments(segments):
    # to fix small issues when the gap between two segments is very small, if they are from the same user, they should be in the same segment/sentence
    if not segments:
        return []

    merged = [segments[0].copy()]
    for seg in segments[1:]:
        last = merged[-1]
        if seg["user_id"] == last["user_id"] and seg["start"] - last["end"] < 1.0:
            # small gap = assuming same speaker
            last["end"] = seg["end"]
            last["text"] += " " + seg["text"]
        else:
            merged.append(seg.copy())

    return merged


complete_text = complete_transcription()
#with open("final_transcription.txt", "w") as f:
#    f.write(complete_text)

print(complete_text)

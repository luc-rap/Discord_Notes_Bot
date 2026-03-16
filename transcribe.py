import whisper

model = whisper.load_model("base")
result = model.transcribe("recordings/510096145402298378.mp3")
with open("transcription.txt", "w") as f:
    f.write(result["text"])
print(result["text"])
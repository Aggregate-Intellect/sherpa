import whisper
model = whisper.load_model("base")
result = model.transcribe("lab10.mp3")

with open("10.txt", "w", encoding="utf-8") as f:
        f.write(result["text"])
# =========================================
# STEP 1: Install Whisper
# =========================================

!pip -q install openai-whisper
!sudo apt update -qq
!sudo apt install ffmpeg -qq


# =========================================
# STEP 2: Upload Audio File
# =========================================

from google.colab import files

uploaded = files.upload()


# =========================================
# STEP 3: Get Uploaded Filename
# =========================================

audio_file = list(uploaded.keys())[0]

print("Uploaded File:", audio_file)


# =========================================
# STEP 4: Load Whisper Model
# =========================================

import whisper

# Models:
# tiny, base, small, medium, large

model = whisper.load_model("base")


# =========================================
# STEP 5: Convert Speech to Text
# =========================================

result = model.transcribe(audio_file)

print("\n===== TRANSCRIBED TEXT =====\n")
print(result["text"])


# =========================================
# STEP 6: Save Transcript to File
# =========================================

with open("transcript.txt", "w", encoding="utf-8") as f:
    f.write(result["text"])


# =========================================
# STEP 7: Download Transcript
# =========================================

files.download("transcript.txt")

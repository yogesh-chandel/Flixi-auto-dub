# =========================================
# STEP 1: Install Demucs
# =========================================
!pip -q install demucs


# =========================================
# STEP 2: Upload Audio File
# =========================================
from google.colab import files

uploaded = files.upload()


# =========================================
# STEP 3: Get Uploaded File Name
# =========================================
import os

audio_file = list(uploaded.keys())[0]

print("Uploaded File:", audio_file)


# =========================================
# STEP 4: Run Demucs Source Separation
# =========================================
# This separates:
# - vocals
# - drums
# - bass
# - other instruments

!demucs "{audio_file}"


# =========================================
# STEP 5: Locate Output Folder
# =========================================
# Demucs saves output here:
# separated/htdemucs/<song_name>/

song_name = os.path.splitext(audio_file)[0]

output_path = f"/content/separated/htdemucs/{song_name}"

print("Output Folder:", output_path)


# =========================================
# STEP 6: List Generated Files
# =========================================
print("\nGenerated Files:")
print(os.listdir(output_path))


# =========================================
# STEP 7: Download Vocal Track
# =========================================
vocals_file = f"{output_path}/vocals.wav"

files.download(vocals_file)

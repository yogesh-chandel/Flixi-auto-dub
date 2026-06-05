# Install f5-tts for Audio cloning 
!pip install -q f5-tts soundfile

!pip install pydub

!apt-get install ffmpeg -y

# Upload files
from pydub import AudioSegment
from f5_tts.api import F5TTS
import f5_tts
import os
from google.colab import files

uploaded = files.upload()

# Input audio file
audio_file = "vocals.wav"  # change to your file

# Load audio
audio = AudioSegment.from_file(audio_file)

# Chunk length in milliseconds
chunk_length_ms = 12 * 1000  # 12 seconds

# Output folder
output_dir = "audio_chunks"
os.makedirs(output_dir, exist_ok=True)

# Split and save
for i in range(0, len(audio), chunk_length_ms):
    chunk = audio[i:i + chunk_length_ms]
    chunk_name = os.path.join(output_dir, f"chunk_{i//chunk_length_ms:03d}.wav")
    chunk.export(chunk_name, format="wav")

print(f"Created {len(os.listdir(output_dir))} clips")
print("Saved in:", output_dir)

# Print all chunks
clips = sorted(os.listdir("audio_chunks"))
for clip in clips:
    print(clip)

# Reference Audio
reference_audio = "audio_chunks/chunk_001.wav"   # uploaded file

text = """
Hello, welcome to our movie dubbing system.
This voice is generated using F5-TTS voice cloning.
"""

tts = F5TTS()

tts.infer(
    ref_file=reference_audio,
    ref_text="",
    gen_text=text,
    file_wave=output_file
)

print("Generated:", output_file)
output_file = "generated.wav"

# To play Audio
from IPython.display import Audio

Audio(output_file)

# Download audio
files.download(output_file)

#OR For Hindi audio

tts = F5TTS()

tts.infer(
    ref_file="speaker.wav",
    ref_text="",
    gen_text="नमस्ते, आप कैसे हैं? यह एक डबिंग परीक्षण है।",
    file_wave="hindi.wav"
)

Audio("hindi.wav")

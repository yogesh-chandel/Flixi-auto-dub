!pip install webrtcvad pydub

from google.colab import files

uploaded = files.upload()
audio_file = list(uploaded.keys())[0]

print("Uploaded:", audio_file)

from pydub import AudioSegment

audio = AudioSegment.from_file(audio_file)

audio = (
    audio
    .set_channels(1)
    .set_frame_rate(16000)
    .set_sample_width(2)
)

audio.export("vad_input.wav", format="wav")

print("Converted to vad_input.wav")

import wave
import webrtcvad

vad = webrtcvad.Vad(3)  # 0-3, 3 = most aggressive

wav = wave.open("vad_input.wav", "rb")

sample_rate = wav.getframerate()
frame_duration = 30  # ms

frame_size = int(sample_rate * frame_duration / 1000)

audio_bytes = wav.readframes(wav.getnframes())

speech_segments = []

offset = 0
timestamp = 0.0

frame_bytes = frame_size * 2  # 16-bit audio

speech_start = None

while offset + frame_bytes < len(audio_bytes):

    frame = audio_bytes[offset:offset + frame_bytes]

    is_speech = vad.is_speech(frame, sample_rate)

    if is_speech and speech_start is None:
        speech_start = timestamp

    if not is_speech and speech_start is not None:
        speech_segments.append(
            (speech_start, timestamp)
        )
        speech_start = None

    offset += frame_bytes
    timestamp += frame_duration / 1000.0

if speech_start is not None:
    speech_segments.append(
        (speech_start, timestamp)
    )

print("Detected speech segments:")
for seg in speech_segments:
    print(seg)

from pydub import AudioSegment
import os

audio = AudioSegment.from_wav("vad_input.wav")

os.makedirs("speech_chunks", exist_ok=True)

for i, (start, end) in enumerate(speech_segments):

    chunk = audio[
        int(start * 1000):
        int(end * 1000)
    ]

    if len(chunk) > 500:  # ignore tiny chunks

        filename = f"speech_chunks/chunk_{i:03d}.wav"

        chunk.export(
            filename,
            format="wav"
        )

print("Saved chunks.")

import os

chunks = sorted(os.listdir("speech_chunks"))

print("Number of chunks:", len(chunks))

for c in chunks[:20]:
    print(c)

import shutil
from google.colab import files

shutil.make_archive(
    "speech_chunks",
    "zip",
    "speech_chunks"
)

files.download("speech_chunks.zip")

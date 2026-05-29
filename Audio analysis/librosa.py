# Download librosa in google colab
!pip -q install librosa soundfile

# Upload file

from google.colab import files

uploaded = files.upload()

# Import Library

import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import json

# Sample Rate & Audio Length

audio_file = list(uploaded.keys())[0]

y, sr = librosa.load(audio_file, sr=None)

print("Sample Rate:", sr)
print("Audio Length:", len(y))

duration = librosa.get_duration(y=y, sr=sr)

# Tempo (BPM)
tempo, _ = librosa.beat.beat_track(y=y, sr=sr)

# RMS Energy
rms = librosa.feature.rms(y=y)[0].tolist()

# Zero Crossing Rate
zcr = librosa.feature.zero_crossing_rate(y)[0].tolist()

# Spectral Centroid
spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0].tolist()

# MFCCs
mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13).tolist()

# Chroma Features
chroma = librosa.feature.chroma_stft(y=y, sr=sr).tolist()

# Feaature Extraction

features = {
    "sample_rate": sr,
    "duration": duration,
    "tempo": float(tempo),
    "rms_energy": rms,
    "zero_crossing_rate": zcr,
    "spectral_centroid": spectral_centroid,
    "mfccs": mfccs,
    "chroma": chroma
}

with open("audio_features.json", "w") as f:
    json.dump(features, f)


print("\nFeatures Extracted Successfully!")

# Visualization

D = librosa.amplitude_to_db(
    np.abs(librosa.stft(y)),
    ref=np.max
)

plt.figure(figsize=(12, 5))

librosa.display.specshow(
    D,
    sr=sr,
    x_axis='time',
    y_axis='log'
)

plt.colorbar(format='%+2.0f dB')
plt.title('Spectrogram')

plt.show()

# Download

files.download("audio_features.json")

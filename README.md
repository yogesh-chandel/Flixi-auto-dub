# 🎙️ Flixi Auto-Dub

**An offline, zero-token AI pipeline that automatically translates and dubs audio while cloning each speaker's distinct voice.**

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/yogesh-chandel/Flixi-auto-dub/blob/main/Flixi_Auto_Dub.ipynb)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![PyTorch](https://img.shields.io/badge/PyTorch-2.6.0%20(CUDA%2012.4)-EE4C2C?logo=pytorch)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Cost](https://img.shields.io/badge/API%20Cost-$0%20(100%25%20Offline)-brightgreen)

---

## 📌 Overview

**Flixi Auto-Dub** is an end-to-end, fully open-source audio dubbing pipeline. Given an audio file containing multiple speakers, it outputs a synchronized `.wav` file where dialogue is translated into your target language, spoken in each original speaker's cloned voice, and mixed over the original background music and sound effects.

* **Zero Cloud APIs:** No OpenAI keys, no ElevenLabs subscriptions, and no rate limits.
* **Runs on Free Hardware:** Developed and benchmarked on **Google Colab's free T4 GPU tier**.
* **Preserves Acoustic Context:** Separates vocals and instrumentals so background ambience and music remain intact.

---

## ⚡ The Open-Source Stack vs. Paid APIs

| Step | Industry Standard (Paid Cloud) | Flixi Auto-Dub Stack (Self-Hosted) |
|---|---|---|
| **Vocal Separation** | Cloud Audio Splitting APIs | **Demucs (`htdemucs` 2-stem)** |
| **Speech-to-Text** | Whisper Cloud API / Google STT | **faster-whisper (`large-v3`)** |
| **Speaker Diarization** | Pyannote Cloud API | **Resemblyzer + Agglomerative Clustering** |
| **Translation** | Google Translate / DeepL API | **Argos Translate (Offline MT)** |
| **Voice Cloning & TTS** | ElevenLabs / PlayHT | **Chatterbox Multilingual TTS** |
| **Post-Processing** | Cloud DAW | **librosa + pyloudnorm (-20 LUFS target)** |

---

## 🔄 Pipeline Workflow

```text
               Input Audio (.mp3 / .wav)
                          │
                          ▼
             ┌─────────────────────────┐
             │    Meta Demucs Stem     │
             └────────────┬────────────┘
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
      [vocals.wav]               [no_vocals.wav]
            │                  (Background Ambience)
            ▼                           │
   faster-whisper large-v3              │
   (Word-level timestamps)              │
            │                           │
            ▼                           │
 Resemblyzer + Scikit-Learn             │
 (Speaker Fingerprint & Clustering)     │
            │                           │
            ▼                           │
    Smart Line Segmenter                │
  (Merges pauses / splits overflow)     │
            │                           │
            ▼                           │
     Argos Translate                    │
   (Offline target translation)         │
            │                           │
            ▼                           │
 Chatterbox Multilingual TTS            │
 (Clones voice & time-stretches)        │
            │                           │
            ▼                           │
   pyloudnorm (-20 LUFS)                │
 (Loudness match & reassembly)          │
            │                           │
            └─────────────┬─────────────┘
                          │
                          ▼
                   Final dubbed.wav

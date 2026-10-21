# Flixi Auto-Dub — Project Documentation

**An offline, token-free pipeline that automatically dubs audio from one language into another, cloning each speaker's own voice.**

---

## 1. What this project does

Give it an audio file (e.g. a movie clip or song) in one language, and it hands back a new audio file in a target language — where each speaker's dialogue is translated and spoken back in a voice that sounds like *them*, placed at the same timestamps as the original.

No paid APIs, no API keys/tokens, no login walls, no restrictive licenses. Every model used is open-weight and runs locally on a single GPU (developed on Google Colab's free T4 GPU tier).

**Input:** an audio file (e.g. `.mp3`, `.wav`) with one or more speakers talking.
**Output:** a `.wav` file with the dialogue re-spoken in the target language, mixed back over the original background music/sound.

---

## 2. Why we built it this way

Most auto-dubbing tools today rely on paid, cloud-hosted APIs (translation APIs, TTS APIs, diarization APIs) — which means recurring cost, rate limits, vendor lock-in, and data leaving your machine. The goal of this project was to prove that a **fully open-source, self-hosted stack** could do the same job end-to-end:

| Need | Paid-API equivalent | What we used instead |
|---|---|---|
| Separate voice from music | Cloud audio-splitting API | **Demucs** (Meta, open-source) |
| Speech-to-text | Whisper API / Google STT | **faster-whisper** (local, optimized) |
| "Who's speaking when" | Diarization API (e.g. pyannote cloud) | **Resemblyzer** + clustering |
| Translation | Google Translate API | **Argos Translate** (offline MT) |
| Voice cloning + TTS | ElevenLabs / paid voice clone APIs | **Chatterbox Multilingual TTS** |

This is also why the notebook spends real effort on things like GPU/torch version pinning and manual compatibility patches — every component is a separate open-source project with its own dependency expectations, and getting them to coexist in one environment was a large part of the actual work (hence "3 months to get it running reliably").

---

## 3. Pipeline overview

```
  Audio file
      │
      ▼
 ┌─────────────┐
 │   Demucs    │  splits into vocals.wav + background.wav
 └─────────────┘
      │ (vocals only)
      ▼
 ┌─────────────┐
 │faster-whisper│  transcribes speech -> text + word-level timestamps
 └─────────────┘
      │
      ▼
 ┌─────────────┐
 │ Resemblyzer │  embeds each line's voice -> clusters into N speakers
 │ + clustering│
 └─────────────┘
      │
      ▼
 ┌─────────────┐
 │ Line builder│  merges same-speaker lines, splits overly long ones
 └─────────────┘
      │
      ▼
 ┌─────────────┐
 │Argos Translate│ translates each line's text into the target language
 └─────────────┘
      │
      ▼
 ┌─────────────┐
 │ Voice sample │ grabs each speaker's longest clean line as a "reference voice"
 └─────────────┘
      │
      ▼
 ┌─────────────┐
 │  Chatterbox  │  clones each speaker's voice, speaks the translated line,
 │ Multilingual │  time-stretched to fit the original line's duration
 │     TTS      │
 └─────────────┘
      │
      ▼
 ┌─────────────┐
 │ Reassembly  │  loudness-normalizes each line, overlays it on the original
 │             │  timeline on top of the background track
 └─────────────┘
      │
      ▼
  dubbed.wav
```

---

## 4. Stage-by-stage explanation

### 4.1 Environment setup
- Checks for a GPU via `nvidia-smi` (checked *before* importing `torch`, so the correct pinned build of PyTorch loads instead of Colab's preinstalled one).
- Installs `demucs`, `faster-whisper`, `chatterbox-tts`, `argostranslate`, `resemblyzer`, `scikit-learn`, `pydub`, `librosa`, `soundfile`, `pyloudnorm`.
- Pins `torch==2.6.0` / `torchaudio==2.6.0` / `torchvision==0.21.0` on the CUDA 12.4 build specifically, because Chatterbox's TTS models need that exact combination — letting pip's dependency resolver pick versions on its own caused breakage.

### 4.2 Configuration
A single cell exposes the knobs that change per run:
- `NUM_SPEAKERS` — how many distinct voices are in the clip (must be set manually; the pipeline doesn't currently auto-detect this).
- `LANG_SRC` / `LANG_TGT` — source and target language codes (e.g. `en` → `hi`).
- `MAX_LINE_SECONDS` — a spoken line longer than this gets split at the next sentence boundary.
- `MERGE_GAP` — consecutive lines from the same speaker closer together than this (in seconds) get merged into one line.

### 4.3 Vocal separation — Demucs
Runs Meta's `htdemucs` model in 2-stem mode, splitting the uploaded audio into `vocals.wav` (speech only) and `no_vocals.wav` (music/background/effects). Separating vocals first matters because both the transcription step and the speaker-ID step work far better on clean speech than on speech mixed with music.

### 4.4 Transcription — faster-whisper
Runs OpenAI's Whisper `large-v3` model (via the `faster-whisper` implementation, which is faster and lighter on memory than the original) on the isolated vocals track, with word-level timestamps enabled. This produces a list of segments, each with start/end time, the transcribed text, and per-word timing.

### 4.5 Speaker identification — Resemblyzer + clustering
There's no ground-truth speaker labels, so the pipeline infers them:
1. For every transcribed segment, it extracts a short audio clip and runs it through Resemblyzer's `VoiceEncoder`, producing a voice embedding (a numeric fingerprint of how that voice sounds).
2. These embeddings are grouped into `NUM_SPEAKERS` clusters using `AgglomerativeClustering` (cosine distance, average linkage) — segments that "sound similar" end up in the same cluster.
3. Each cluster is labeled `speaker_0`, `speaker_1`, etc., and that label is attached back to each segment.

*Note:* a small compatibility patch is applied here because Resemblyzer's bundled checkpoint predates PyTorch 2.6's stricter default security setting for `torch.load` — the patch just calls the underlying loader directly rather than overriding `torch.load` in a way that could compound on repeated runs.

### 4.6 Turning the transcript into dubbing lines
Raw Whisper segments don't map cleanly onto "one thing a person said" — a sentence might be split across segments, or someone might ramble for 30 seconds straight. Two cleanup passes fix this:
- **`merge_same_speaker`**: joins consecutive segments from the same speaker if the gap between them is smaller than `MERGE_GAP`.
- **`split_long_lines`**: if a merged line is longer than `MAX_LINE_SECONDS`, it's cut at the next sentence-ending punctuation so the TTS step never has to generate one extremely long, hard-to-clone utterance.

### 4.7 Translation — Argos Translate
Argos Translate is a fully offline, open-source machine translation engine (no internet call needed once the language package is downloaded once). The appropriate `LANG_SRC → LANG_TGT` package is installed, and every dubbing line's text is translated independently.

### 4.8 Reference voice extraction
For each detected speaker, the pipeline picks their single *longest* line (on the theory that a longer clip gives the voice-cloning model the cleanest, most representative sample) and saves it as a short reference `.wav`. This reference clip is what Chatterbox uses to clone that speaker's voice.

### 4.9 Voice cloning + speech generation — Chatterbox Multilingual TTS
This is the core dubbing step, and it deliberately runs as a **separate subprocess** (`tts_worker.py`, written out and launched with `!python`) rather than being imported into the main notebook process — this keeps the notebook's own kernel state simple and avoids conflicts between Chatterbox's internal `torchaudio` usage and the rest of the pipeline.

For every line:
1. Chatterbox generates speech for the *translated* text, conditioned on that speaker's reference voice clip and the target language.
2. The generated audio is time-stretched (via `librosa.effects.time_stretch`) so its duration matches the original line's duration as closely as possible — capped to a 0.7x–1.4x stretch range so voices don't sound unnaturally sped up or slowed down.
3. Lines that fail to generate are skipped (not fatal to the whole run) and logged.

### 4.10 Reassembly
- Each generated line is loudness-normalized to a consistent **-20 LUFS** target (so quiet and loud lines don't jump around in volume) using `pyloudnorm`.
- Every line is overlaid onto a silent track at its original start timestamp, reconstructing the full dialogue track in the target language.
- That reconstructed dialogue track is overlaid on top of the original background/music track (`no_vocals.wav` from Demucs) to produce the final `dubbed.wav`.

### 4.11 Download
Uses Colab's `files.download()` to hand the final file back to the user.

---

## 5. Current limitations / known issues

- **`NUM_SPEAKERS` is manual.** The pipeline doesn't auto-detect how many speakers are in a clip — get this wrong and the clustering step misassigns lines.
- **Speaker clustering is voice-only, not context-aware.** Two different people with similar-sounding voices can get merged into one cluster; the same person's voice under background noise or emotional shift can get split across two.
- **No true lip-sync.** Timing is matched to each *line's* start/end, not to individual mouth movements, so it works for audio-only dubbing but isn't frame-accurate for video.
- **Time-stretch has limits.** The 0.7x–1.4x cap means a translation that's dramatically longer/shorter than the original line will sound noticeably sped up, slowed down, or will drift out of sync.
- **Single audio-file input only.** Currently takes a standalone audio track, not a video file directly (audio needs to be extracted first).
- **No token/API cost, but real compute cost.** Everything runs on-GPU locally, so processing time scales with clip length and GPU availability (built and tested on Colab's free T4 tier).
- **Environment fragility.** Because five separate open-source projects (Demucs, faster-whisper, Chatterbox, Argos Translate, Resemblyzer) each have their own dependency expectations, the pinned-version install cell is fairly brittle — a change in any one library's release can break the pinned combination.

---

## 6. Ideas for future work

- Auto-detect `NUM_SPEAKERS` instead of requiring it as manual input (e.g. via a clustering quality metric or an off-the-shelf diarization model).
- Accept video files directly, extracting audio and re-muxing the dubbed audio back onto the original video.
- Smarter duration matching — e.g. lightly rephrasing translated text when it's too long/short instead of relying solely on time-stretching.
- Batch/queue support for dubbing multiple files in one run.
- A lightweight UI (so teammates or others don't need to run the notebook cell-by-cell).
- Package the environment (e.g. Docker or a `requirements.txt` with hard pins) to make setup less fragile and reproducible outside Colab.

---

## 7. Tech stack summary

| Component | Library | Role |
|---|---|---|
| Runtime | Google Colab (T4 GPU) | Free GPU compute |
| Vocal separation | Demucs (`htdemucs`) | Splits vocals from background |
| Speech-to-text | faster-whisper (`large-v3`) | Transcription + word timestamps |
| Speaker ID | Resemblyzer + scikit-learn | Voice embedding + clustering |
| Translation | Argos Translate | Offline machine translation |
| Voice cloning / TTS | Chatterbox Multilingual TTS | Speaks translated text in cloned voice |
| Audio processing | pydub, librosa, soundfile, pyloudnorm | Time-stretching, loudness normalization, mixing |

---

## 8. How to run it

1. Open the notebook in Google Colab.
2. `Runtime > Change runtime type > T4 GPU`.
3. Run the **Setup** cells top to bottom (installs everything; takes a few minutes).
4. In the config cell, set `NUM_SPEAKERS`, `LANG_SRC`, and `LANG_TGT` for your clip.
5. Run the **Upload audio** cell and select an audio file (not video — audio track only).
6. Run the remaining cells in order: separate → transcribe → identify speakers → build lines → translate → extract reference voices → generate dubbed speech → reassemble → download.
7. Recommendation: test on a short clip (under a minute) first before running on a full-length file, since the TTS generation step is the slowest part and scales with the number of dialogue lines.

---

*Documentation prepared for internal team reference — describes the pipeline as implemented in `Flixi_Auto_Dub.ipynb`.*

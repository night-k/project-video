# AB Video Deduplicator: High-FPS Frame Blending + Perturbation

[简体中文](./README.md) | [English](./README_en.md)

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)

> ⚠️ For technical research and educational purposes only. Do not use for any illegal activities.

**AB Video Deduplicator** is an open-source desktop app for video creators. It uses a multi-layer strategy of "high-FPS frame blending + frame perturbation + audio perturbation + TikTok-only encoding" to fundamentally alter video data fingerprints, bypassing originality detection on short-video platforms.

<p align="center">
  <img src="./assets/cover_software.png" alt="Main UI" width="600"/>
  <br>
  <em>Clean and intuitive user interface</em>
</p>

---

## 💡 How It Works

### 1. High-FPS Frame Blending

| Dedup Level | Target FPS | A:B Frame Ratio |
| :---: | :---: | :---: |
| **50%** | 60 | 1 : 1 |
| **75%** | 120 | 1 : 3 |
| **87.5%**| 240 | 1 : 7 |

1. **Input two videos**: Video A (content) + Video B (material)
2. **Generate high-FPS stream** (60/120/240 fps)
3. **A frames at key positions**, B frames fill the gaps
4. **Result**: Mobile viewers still see smooth A playback, but the data fingerprint is completely different

### 2. Frame Perturbation

Subtle, invisible modifications to each A frame:
- Micro noise (2% intensity)
- Random color temperature shift
- 1.01x micro-scale + micro-translate
- A/B frame blending (default 80% A)

Even if the platform reconstructs via frame-dropping, it can't recover the original A frame.

### 3. Audio Perturbation

Micro speed adjustment on the audio track (default 0.99x), changing the audio fingerprint.

### 4. TikTok Mobile-Only Mode (optional)

Output video plays normally only on TikTok mobile app. PC players show color distortion / grayscale + no audio.

### 5. Playback Guard (optional, experimental)

Re-encodes with HEVC hardware-decode-friendly settings + guard metadata, improving hardware decode probability on real devices while discouraging simulator/software decoding.

---

## ✨ Core Features

- **Intuitive GUI** — PyQt5, no command-line needed
- **Three dedup levels** — 60 / 120 / 240 fps
- **Frame perturbation** — noise + color shift + micro-transform + A/B blend
- **Audio perturbation** — micro speed change
- **TikTok-only mode** — mobile-only playback
- **Playback guard** — HEVC hardware decode optimization (experimental)
- **NVIDIA GPU acceleration** — NVENC hardware encoding
- **Auto resolution matching** — Video B auto-resized to match Video A
- **Real-time progress & logging**

---

## 🚀 Quick Start

### Requirements

1. **Python**: 3.8+
2. **FFmpeg**: Must be installed and on PATH
   - macOS: `brew install ffmpeg`
   - Windows: download from [gyan.dev](https://gyan.dev/ffmpeg/builds/)
   - Linux: `sudo apt install ffmpeg`

### Install & Run

```bash
git clone <repo-url>
cd AB-Video-Deduplicator
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

### Usage

1. Select Video A (content video)
2. Select Video B (material video)
3. Choose dedup level (60 / 120 / 240 fps)
4. Optional: enable frame perturbation, TikTok-only, playback guard
5. Choose output path, click "Start Processing"

---

## 📂 Project Structure

```
├── src/
│   ├── main.py              # Entry point
│   ├── video_processor.py   # Core processing thread
│   ├── frame_perturb.py     # Frame perturbation (noise/color/micro-transform)
│   ├── audio_perturb.py     # Audio perturbation (micro speed change)
│   ├── tiktok_only.py       # TikTok mobile-only conversion
│   ├── playback_guard.py    # Playback guard (HEVC optimization)
│   ├── theme.py             # UI stylesheet
│   ├── resources.qrc        # Qt resource file
│   ├── resources.py         # Compiled resources
│   └── ui/                  # PyQt5 UI components
├── utils/
│   ├── extract_frames.py    # Frame extraction utility
│   └── gen_test_video.py    # Test video generator
├── assets/                  # Icons & screenshots
├── docs/
│   └── screenshot.png       # Software screenshot
├── requirements.txt
└── LICENSE
```

---

## 📜 License

MIT License

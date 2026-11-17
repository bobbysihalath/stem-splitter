# 🎵 Vocal Remover, Stem Splitter & Voice Cleaner

A local web app that uses AI ([Demucs](https://github.com/facebookresearch/demucs)) to:

- **Stem Splitter**: remove vocals or split a song into stems.
  - Vocal remover → Vocals + Instrumental
  - 4 stems → Vocals, Drums, Bass, Other
  - 6 stems → Vocals, Drums, Bass, Guitar, Piano, Other
- **Voice Cleaner**: remove background noise from voice in **audio or video**. For video files you get the video back with the cleaned audio.

Results open in a multitrack mixer with waveforms, mute/solo, volume, comparison with the original and downloads.

Everything runs on your own computer. No files are uploaded to the internet.

---

## Requirements

| | Version |
|---|---|
| Python | 3.10 – 3.12 (3.11 recommended) |
| ffmpeg | any recent version |
| Disk | ~3 GB (PyTorch + models) |

---

## 🍎 macOS

### 1. Install Python and ffmpeg
Install [Homebrew](https://brew.sh) if you don't have it, then:
```bash
brew install python@3.11 ffmpeg
```

### 2. Get the project
```bash
git clone https://github.com/<your-username>/stem-splitter.git
cd stem-splitter
```

### 3. Create a virtual environment and install packages
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Run
```bash
uvicorn app:app --port 8000
```
Open **http://localhost:8000**

> Next time, you only need these commands:
> ```bash
> cd stem-splitter
> source .venv/bin/activate
> uvicorn app:app --port 8000
> ```

---

## 🪟 Windows 10 / 11

### 1. Install Python and ffmpeg
Open **PowerShell** and run:
```powershell
winget install Python.Python.3.11
winget install Gyan.FFmpeg
```
Then **close PowerShell and open it again** so `python` and `ffmpeg` are found.

Check that they work:
```powershell
python --version
ffmpeg -version
```

> No winget? Download Python from https://www.python.org/downloads/ and tick **"Add python.exe to PATH"** during install. Download ffmpeg from https://www.gyan.dev/ffmpeg/builds/ and add its `bin` folder to PATH.

### 2. Get the project
```powershell
git clone https://github.com/<your-username>/stem-splitter.git
cd stem-splitter
```

### 3. Create a virtual environment and install packages
```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

> If activation fails with *"running scripts is disabled"*, run this once:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```

### 4. Run
```powershell
uvicorn app:app --port 8000
```
Open **http://localhost:8000**

> Next time, you only need these commands:
> ```powershell
> cd stem-splitter
> .venv\Scripts\activate
> uvicorn app:app --port 8000
> ```

---

## ⚡ Faster processing (optional)

- **Windows with an NVIDIA GPU:** install the CUDA build of PyTorch. Get the exact command from https://pytorch.org/get-started/locally/. For example:
  ```powershell
  pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu124
  ```
  Demucs then uses the GPU automatically.
- **Mac with Apple Silicon (M1–M4):** in `app.py`, add `"-d", "mps"` after `"-m", "demucs",`. If you get an error, remove it again.

Typical time for a 3-minute song: about 1–3 minutes on a processor, and 10–20 seconds on a GPU. The first run also downloads the AI model (~80 MB).

---

## 🛠 Troubleshooting

| Problem | Fix |
|---|---|
| `No module named 'numpy'` | `pip install "numpy<2"` |
| `ffmpeg not found` / `FileNotFoundError` | ffmpeg is not installed or not on PATH (see step 1). Restart the terminal. |
| Page looks old after an update | Hard refresh: **Cmd + Shift + R** (Mac) / **Ctrl + F5** (Windows) |
| Port 8000 is already in use | `uvicorn app:app --port 8001`, then open http://localhost:8001 |
| `uvicorn` not found | The virtual environment isn't active. Run the activate command from step 3. |

---

## 📁 Project structure
```
stem-splitter/
├── app.py            # FastAPI backend (Demucs + ffmpeg)
├── requirements.txt
├── static/
│   └── index.html    # Web UI (upload, progress, mixer)
└── jobs/             # Processed files (created automatically, git-ignored)
```

## API
- `POST /api/split`: form fields `file`, `mode` (`vocals` | `4stems` | `6stems` | `clean`), `denoise` (`1` | `0`)
- `GET /api/jobs/{id}`: returns `state`, `stems`, `source` and, for video, `video`

## Notes
- Synth, strings and wind have no separate stem in the open models, so they end up in **Other**.
- Processed files are stored in `jobs/`. You can delete that folder at any time.
- Only process audio you have the rights to use.

## Credits
Separation by [Demucs](https://github.com/facebookresearch/demucs) (Meta AI, MIT License).

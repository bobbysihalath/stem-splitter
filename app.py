"""Vocal Remover, Stem Splitter & Voice Cleaner — FastAPI + Demucs + ffmpeg.

Run:  uvicorn app:app --port 8000   then open http://localhost:8000
"""
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).parent
JOBS = BASE / "jobs"
JOBS.mkdir(exist_ok=True)
VIDEO_EXT = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}

# mode -> (demucs model, extra args)
MODES = {
    "vocals": ("htdemucs", ["--two-stems", "vocals"]),   # vocals + instrumental
    "4stems": ("htdemucs", []),                           # vocals, drums, bass, other
    "6stems": ("htdemucs_6s", []),                        # + guitar, piano
    "clean":  ("htdemucs", ["--two-stems", "vocals"]),   # voice + noise
}
RENAME = {
    "clean": {"vocals": "voice", "no_vocals": "noise"},
    "*": {"no_vocals": "instrumental"},
}

app = FastAPI(title="Stem Splitter")
status: dict[str, dict] = {}


def ff(*args):
    p = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr[-2000:])


def url(job_id, name):
    return f"/api/jobs/{job_id}/{name}"


def process(job_id: str, src: Path, mode: str, denoise: bool):
    d = JOBS / job_id
    st = status[job_id]
    st["state"] = "processing"
    try:
        is_video = src.suffix.lower() in VIDEO_EXT
        # Normalise input to WAV (handles video + odd formats); also make an MP3 preview of the original
        wav = d / "input.wav"
        ff("-i", str(src), "-vn", "-ac", "2", "-ar", "44100", str(wav))
        ff("-i", str(wav), "-b:a", "192k", str(d / "original.mp3"))
        st["source"] = url(job_id, "original.mp3")

        model, extra = MODES[mode]
        out = d / "out"
        cmd = [sys.executable, "-m", "demucs", "-n", model, "--mp3", "-o", str(out), *extra, str(wav)]
        p = subprocess.run(cmd, capture_output=True, text=True)
        if p.returncode != 0:
            raise RuntimeError(p.stderr[-2000:])

        rename = RENAME.get(mode, RENAME["*"])
        stems = {}
        for f in sorted(next((out / model).iterdir()).glob("*.mp3")):
            name = rename.get(f.stem, f.stem)
            final = d / f"{name}.mp3"
            shutil.move(str(f), final)
            stems[name] = url(job_id, final.name)
        shutil.rmtree(out, ignore_errors=True)

        if mode == "clean":
            voice = d / "voice.mp3"
            if denoise:  # remove hiss/hum left after AI separation
                tmp = d / "voice_dn.mp3"
                ff("-i", str(voice), "-af", "highpass=f=70,afftdn=nf=-25,lowpass=f=16000", "-b:a", "192k", str(tmp))
                tmp.replace(voice)
            if is_video:
                ff("-i", str(src), "-i", str(voice), "-map", "0:v:0", "-map", "1:a:0",
                   "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(d / "clean.mp4"))
                st["video"] = url(job_id, "clean.mp4")
        wav.unlink(missing_ok=True)
        st.update(state="done", stems=stems)
    except Exception as e:  # noqa: BLE001
        st.update(state="error", error=str(e))


@app.post("/api/split")
async def split(bg: BackgroundTasks, file: UploadFile = File(...), mode: str = Form("vocals"),
                denoise: str = Form("1")):
    if mode not in MODES:
        raise HTTPException(400, "invalid mode")
    job_id = uuid.uuid4().hex[:12]
    d = JOBS / job_id
    d.mkdir()
    src = d / f"source{Path(file.filename or 'a.mp3').suffix.lower()}"
    with src.open("wb") as fh:
        shutil.copyfileobj(file.file, fh)
    status[job_id] = {"state": "queued", "name": file.filename, "mode": mode}
    bg.add_task(process, job_id, src, mode, denoise == "1")
    return {"job_id": job_id}


@app.get("/api/jobs/{job_id}")
def job(job_id: str):
    if job_id not in status:
        raise HTTPException(404)
    return status[job_id]


@app.get("/api/jobs/{job_id}/{fname}")
def stem_file(job_id: str, fname: str):
    p = (JOBS / job_id / fname).resolve()
    if not p.is_file() or JOBS.resolve() not in p.parents:
        raise HTTPException(404)
    return FileResponse(p)


app.mount("/", StaticFiles(directory=BASE / "static", html=True), name="static")

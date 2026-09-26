import logging
import re
import shutil
import subprocess
from pathlib import Path
from typing import List, Tuple

logger = logging.getLogger("scenesense.ffmpeg")


def get_ffmpeg_exe() -> str:
    """System ffmpeg if on PATH, else the binary bundled with imageio-ffmpeg."""
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return ""


def is_ffmpeg_available() -> bool:
    return bool(get_ffmpeg_exe())


def _run(args: List[str]) -> subprocess.CompletedProcess:
    ff = get_ffmpeg_exe()
    if not ff:
        raise RuntimeError("FFmpeg not found. Install ffmpeg or `pip install imageio-ffmpeg`.")
    return subprocess.run([ff, "-hide_banner", "-y", *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def probe_video(path: str) -> Tuple[float, float]:
    """Returns (duration_seconds, fps). Parsed from ffmpeg's stream banner — no ffprobe needed."""
    err = _run(["-i", str(path)]).stderr  # exits non-zero (no output file); banner is what we want
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err)
    if not m:  # e.g. browser-recorded webm has "Duration: N/A" — decode audio-less to measure
        if "Stream" not in err or "Video" not in err:
            raise ValueError("Could not read video — is this a valid video file?")
        times = re.findall(r"time=(\d+):(\d+):([\d.]+)", _run(["-i", str(path), "-an", "-f", "null", "-"]).stderr)
        if not times:
            raise ValueError("Could not determine video duration")
        m = times[-1]
        m = (None, *m)
    duration = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3])
    fps_m = re.search(r"([\d.]+) fps", err)
    return round(duration, 3), float(fps_m[1]) if fps_m else 25.0


def extract_audio_mp3(video_path: str, out_path: str) -> bool:
    """16 kHz mono 32 kbps mp3 — ~14 MB/hour, well under Groq's upload limit."""
    res = _run(["-i", str(video_path), "-vn", "-ac", "1", "-ar", "16000", "-b:a", "32k", str(out_path)])
    ok = res.returncode == 0 and Path(out_path).exists() and Path(out_path).stat().st_size > 1000
    if not ok:
        logger.warning("Audio extraction failed (video may have no audio): %s", res.stderr[-300:])
    return ok


def detect_shots_and_frames(video_path: str, frames_dir: Path, frame_interval: float,
                            threshold: float = 0.28) -> List[float]:
    """
    One decode pass: frame-accurate shot cuts (ffmpeg scene score) + a keyframe every
    `frame_interval` seconds saved as frames_dir/f_00001.jpg (frame i is at ~(i-1)*interval seconds).
    """
    frames_dir.mkdir(parents=True, exist_ok=True)
    for old in frames_dir.glob("f_*.jpg"):
        old.unlink()
    graph = (
        f"[0:v]split=2[a][b];"
        f"[a]scale=160:-2,select='gt(scene\\,{threshold})',showinfo[cuts];"
        f"[b]fps=1/{frame_interval:.3f},scale=384:-2[frames]"
    )
    res = _run(["-i", str(video_path), "-an", "-filter_complex", graph,
                "-map", "[cuts]", "-f", "null", "-",
                "-map", "[frames]", "-q:v", "5", str(frames_dir / "f_%05d.jpg")])
    if res.returncode != 0:
        raise RuntimeError(f"Shot detection failed: {res.stderr[-400:]}")
    return sorted({round(float(t), 3) for t in re.findall(r"pts_time:([\d.]+)", res.stderr)})


def make_ad_creative(out_path: Path, title: str, subtitle: str, duration: float, hue: int) -> bool:
    """Renders a synthetic brand creative (solid colour card + name + soft tone)."""
    def esc(s: str) -> str:
        return re.sub(r"[^A-Za-z0-9 &/_.-]", "", s).replace(":", "")[:40] or "Sponsor"

    font = "C\\:/Windows/Fonts/arial.ttf" if Path("C:/Windows/Fonts/arial.ttf").exists() else ""
    font_opt = f"fontfile='{font}':" if font else ""
    vf = (
        f"drawtext={font_opt}text='{esc(title)}':fontcolor=white:fontsize=84:x=(w-tw)/2:y=(h-th)/2-40,"
        f"drawtext={font_opt}text='{esc(subtitle)}':fontcolor=0xDDDDDD:fontsize=34:x=(w-tw)/2:y=(h/2)+50,"
        f"drawtext={font_opt}text='Synthetic ad  -  SceneSense demo':fontcolor=0xAAAAAA:fontsize=22:x=(w-tw)/2:y=h-60"
    )
    res = _run([
        "-f", "lavfi", "-i", f"color=c=0x{_hue_to_hex(hue)}:s=1280x720:d={duration}:r=25",
        "-f", "lavfi", "-i", f"sine=frequency=196:duration={duration}",
        "-vf", vf, "-af", "volume=0.08", "-shortest",
        "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-c:a", "aac",
        "-movflags", "+faststart", str(out_path),
    ])
    if res.returncode != 0:
        logger.error("Ad creative render failed: %s", res.stderr[-300:])
    return res.returncode == 0


def _hue_to_hex(hue: int) -> str:
    import colorsys
    r, g, b = colorsys.hls_to_rgb((hue % 360) / 360, 0.22, 0.35)
    return f"{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"

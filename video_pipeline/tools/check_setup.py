#!/usr/bin/env python
"""Environment and tools capability setup checker.

Inspects all components of the AI video editor pipeline:
  - FFmpeg & FFprobe
  - Python runtime & required QA packages (numpy, Pillow)
  - FilmCraft CLI
  - EffectCraft CLI
  - DaVinci Resolve Studio edition & version (live API or parsed from log)
  - Resolve external scripting API status
  - Groq API key presence (YES/NO only; never printed)
  - Voicebox local neural TTS daemon status

Reports one line per component with actionable install/configuration hints if missing.
Does not install or modify anything.

Usage:
  python check_setup.py
"""
import json
import os
import re
import shutil
import subprocess
import sys


def check_ffmpeg():
    path = shutil.which("ffmpeg")
    if not path and sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        cand = os.path.join(local_app_data, "Microsoft", "WinGet", "Links", "ffmpeg.exe")
        if os.path.exists(cand):
            path = cand
    if path and os.path.exists(path):
        try:
            out = subprocess.check_output([path, "-version"], text=True, stderr=subprocess.STDOUT)
            ver = out.splitlines()[0].split()[2]
            return f"FFmpeg: {ver} ({path})"
        except Exception:
            return f"FFmpeg: FOUND ({path})"
    return "FFmpeg: MISSING (Install via: winget install Gyan.FFmpeg or add to PATH)"


def check_ffprobe():
    path = shutil.which("ffprobe")
    if not path and sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        cand = os.path.join(local_app_data, "Microsoft", "WinGet", "Links", "ffprobe.exe")
        if os.path.exists(cand):
            path = cand
    if path and os.path.exists(path):
        try:
            out = subprocess.check_output([path, "-version"], text=True, stderr=subprocess.STDOUT)
            ver = out.splitlines()[0].split()[2]
            return f"FFprobe: {ver} ({path})"
        except Exception:
            return f"FFprobe: FOUND ({path})"
    return "FFprobe: MISSING (Install via: winget install Gyan.FFmpeg or add to PATH)"


def check_python():
    return f"Python: {sys.version.split()[0]} ({sys.executable})"


def check_python_packages():
    """Verify required QA dependencies numpy and Pillow (Fix 22)."""
    pkgs = []
    missing = []
    # numpy
    try:
        import numpy as np
        pkgs.append(f"numpy {np.__version__}")
    except ImportError:
        missing.append("numpy")

    # Pillow
    try:
        import PIL
        from PIL import Image
        pkgs.append(f"Pillow {PIL.__version__}")
    except ImportError:
        missing.append("Pillow")

    if missing:
        return f"Python QA Packages: INCOMPLETE (missing: {', '.join(missing)}; run: pip install {' '.join(missing)})"
    return f"Python QA Packages: OK ({', '.join(pkgs)})"


def check_filmcraft():
    cand = r"C:\Program Files\FilmCraft\filmcraft-cli.exe"
    path = cand if os.path.exists(cand) else shutil.which("filmcraft-cli")
    if path and os.path.exists(path):
        try:
            out = subprocess.check_output([path, "--version"], text=True).strip()
            return f"FilmCraft CLI: {out} ({path})"
        except Exception:
            return f"FilmCraft CLI: FOUND ({path})"
    return "FilmCraft CLI: MISSING (Install ArtCraft FilmCraft suite to C:\\Program Files\\FilmCraft)"


def check_effectcraft():
    cand = r"C:\Program Files\EffectCraft\effectcraft-cli.exe"
    # Prefer the Program Files build (0.19) pinned in presets/*/style.json; an older
    # 0.16 copy under %LOCALAPPDATA%\Programs\EffectCraft sits on PATH.
    path = (cand if os.path.exists(cand) else None) or shutil.which("effectcraft-cli")
    if path and os.path.exists(path):
        try:
            out = subprocess.check_output([path, "--version"], text=True).strip()
            return f"EffectCraft CLI: {out} ({path})"
        except Exception:
            return f"EffectCraft CLI: FOUND ({path})"
    return "EffectCraft CLI: MISSING (Install ArtCraft EffectCraft suite to C:\\Program Files\\EffectCraft)"


def parse_resolve_log_version(log_path):
    """Parse actual DaVinci Resolve version string from application log (Fix 22)."""
    if not os.path.exists(log_path):
        return None
    pattern = re.compile(r"Running\s+(DaVinci Resolve(?:\s+Studio)?\s+v?[\d\.]+)")
    try:
        size = os.path.getsize(log_path)
        # The log appends one block per session: the LATEST "Running ..." line is the version that last ran.
        # Scan the tail first (newest lines), widening to the whole file only if the tail has no match.
        for tail_bytes in (4 * 1024 * 1024, size):
            with open(log_path, "rb") as f:
                f.seek(max(0, size - tail_bytes))
                text = f.read().decode("utf-8", errors="ignore")
            for line in reversed(text.splitlines()):
                m = pattern.search(line)
                if m:
                    return m.group(1).strip()
            if tail_bytes >= size:
                break
    except Exception as exc:
        print(f"Warning: could not parse Resolve log {log_path}: {exc}", file=sys.stderr)
    return None


def check_resolve():
    api_dir = r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting"
    os.environ["RESOLVE_SCRIPT_API"] = api_dir
    os.environ["RESOLVE_SCRIPT_LIB"] = r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll"
    mod = os.path.join(api_dir, "Modules")
    if mod not in sys.path:
        sys.path.append(mod)

    # 1. Live API probe
    try:
        import DaVinciResolveScript as d
        r = d.scriptapp("Resolve")
        if r:
            prod = r.GetProductName()
            ver = r.GetVersionString()
            return f"DaVinci Resolve: {prod} {ver} (Running)", "Resolve Scripting: CONNECTED (Live API verified)"
    except Exception:
        pass

    # 2. Parse from application log if not live (Fix 22: real parsing, never hardcoded)
    log_path = os.path.expandvars(r"%APPDATA%\Blackmagic Design\DaVinci Resolve\Support\logs\davinci_resolve.log")
    parsed_ver = parse_resolve_log_version(log_path)
    if parsed_ver:
        return (
            f"DaVinci Resolve: {parsed_ver} (from application log; not responding to live API)",
            "Resolve Scripting: DISCONNECTED (Start Resolve.exe and verify scripting is enabled in Preferences -> General)",
        )
    elif os.path.exists(log_path):
        return (
            "DaVinci Resolve: unknown (log present but version unparsed)",
            "Resolve Scripting: DISCONNECTED (Start Resolve.exe and verify scripting is enabled)",
        )

    return "DaVinci Resolve: MISSING (Install DaVinci Resolve Studio from blackmagicdesign.com)", "Resolve Scripting: UNAVAILABLE"


def check_groq_key():
    k = os.environ.get("GROQ_API_KEY")
    if k and k.startswith("gsk_"):
        return "Groq Key Presence: YES (Loaded from env GROQ_API_KEY)"
    # Check optional local .env if present
    env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
    if os.path.exists(env_file):
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("GROQ_API_KEY="):
                        val = line.strip().split("=", 1)[1].strip(" '\"")
                        if val.startswith("gsk_"):
                            return "Groq Key Presence: YES (Loaded from .env file)"
        except Exception:
            pass
    ahk_cfg = r"C:/portable_apps/my_scripts/autohotkey/ahk-whisper-paste-master/Ahk_Whisper_V2/config.json"
    if os.path.exists(ahk_cfg):
        try:
            c = json.load(open(ahk_cfg, encoding="utf-8-sig"))
            k2 = c.get("OpenapiKey") or ""
            if k2.startswith("gsk_"):
                return "Groq Key Presence: YES (Loaded from AHK Whisper V2 config)"
        except Exception:
            pass
    return "Groq Key Presence: NO (Set GROQ_API_KEY env or add to .env file)"


def check_voicebox():
    try:
        import urllib.request
        req = urllib.request.Request("http://127.0.0.1:8000/status", headers={"User-Agent": "check-setup/1.0"})
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            data = json.load(resp)
            return f"Voicebox Status: ONLINE ({data.get('engine', 'qwen3-tts')})"
    except Exception:
        return "Voicebox Status: OFFLINE (Bypass policy active: estimated timing + placeholder VO; start daemon when local neural TTS is needed)"


def main():
    print("=== Pipeline Environment & Setup Verification ===")
    print(check_ffmpeg())
    print(check_ffprobe())
    print(check_python())
    print(check_python_packages())
    print(check_filmcraft())
    print(check_effectcraft())
    res_info, script_info = check_resolve()
    print(res_info)
    print(script_info)
    print(check_groq_key())
    print(check_voicebox())


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""Word-level transcription via Groq's free Whisper API (whisper-large-v3).

Usage:
  python transcribe_groq.py --input media.mp4 --out transcript/words.json [--model whisper-large-v3]
                            [--language en] [--prompt "names, jargon"] [--chunk-s 600] [--force]
                            [--corrections transcript_corrections.json] [--no-repair]
                            [--repair-only words.json] [--max-repair-windows 2]
  python transcribe_groq.py --selftest

Writes words.json ({"words":[...], "segments":[...], "repairs":[...], "corrections":[...]}),
plus <stem>.srt and <stem>.txt next to it.
Never re-transcribes if --out exists unless --force is passed.

Gap Detector & Turbo Repair (Fixes 18 & 20):
  - Flags windows where words/sec < 0.5 over >=8s while ffmpeg silencedetect confirms audio is NOT silent.
  - Flags consecutive gaps >= 8s with non-silent speech audio.
  - Flags hallucination phrases ("and so on", "thank you") detected via rolling n-grams.
  - Re-transcribes flagged windows with whisper-large-v3-turbo (prompt="") and splices words back in.
  - Logs all operations in words.json["repairs"].
  - Supports --repair-only to repair existing words.json without re-transcribing the full file.
  - Rate limits: 429 responses wait for the retry-after header and retry. Groq sends no audio-seconds
    quota headers on success (observed: only x-ratelimit-*-requests), so there is no proactive audio pacing.
    Optional --min-interval N spaces consecutive requests at least N seconds apart.
  - --repair-only APPENDS to the existing repairs/corrections logs (provenance is never overwritten).

Vocabulary Corrections (Fix 19, rev. pass 3):
  - Preserves mixed case ("davinci" -> "DaVinci", "DAVINCI" -> "DAVINCI").
  - NEVER merges or splits tokens, so word indices stay stable (keep.json written on the raw file stays valid).
    A multi-word key is mapped over consecutive tokens one-to-one ("premiere pro" -> "Premiere Pro").
    A rule whose key and target have different token counts ("film craft" -> "FilmCraft") is REFUSED
    with a warning and logged as type "refused"; write it as a same-length rule instead.
  - Idempotent: a token is changed only if the replacement differs from the token as it stands, and every
    changed word carries "corrected_from" (a marker that also blocks a second correction of the same token).
  - Logs word edits (with stable "index") and segment edits in words.json["corrections"].

Error Handling (Fix 21):
  - Catches json.JSONDecodeError in get_key.
  - Logs ffmpeg errors in check_is_silent instead of swallowing.
"""
import argparse
from fractions import Fraction
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid

AHK_CONFIG = r"C:/portable_apps/my_scripts/autohotkey/ahk-whisper-paste-master/Ahk_Whisper_V2/config.json"
ENDPOINT = "https://api.groq.com/openai/v1/audio/transcriptions"


def get_key():
    """Retrieve Groq API key from environment or AHK Whisper V2 config (Fix 21: catches JSONDecodeError)."""
    k = os.environ.get("GROQ_API_KEY")
    if k and k.startswith("gsk_"):
        return k
    if os.path.exists(AHK_CONFIG):
        try:
            c = json.load(open(AHK_CONFIG, encoding="utf-8-sig"))
            k = c.get("OpenapiKey") or ""
            if k.startswith("gsk_"):
                return k
        except (OSError, json.JSONDecodeError) as e:
            print(f"Warning: could not parse AHK Whisper V2 config: {e}", file=sys.stderr)
    sys.exit("No Groq key: set GROQ_API_KEY or add a gsk_ key to the AHK Whisper V2 config.")


def duration(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", path],
        text=True,
    )
    return float(out.strip())


def extract(src, dst, start, length):
    subprocess.check_call(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-ss",
            f"{start:.3f}",
            "-t",
            f"{length:.3f}",
            "-i",
            src,
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "libmp3lame",
            "-b:a",
            "48k",
            dst,
        ]
    )


def check_is_silent(src, start, length, noise_thresh="-35dB"):
    """Returns True if the window is fully silent according to ffmpeg silencedetect (Fix 21: logs errors)."""
    if length <= 0.1:
        return True
    try:
        cmd = [
            "ffmpeg",
            "-v",
            "info",
            "-ss",
            f"{start:.3f}",
            "-t",
            f"{length:.3f}",
            "-i",
            src,
            "-af",
            f"silencedetect=noise={noise_thresh}:d=0.5",
            "-f",
            "null",
            "-",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            print(f"Warning: ffmpeg silencedetect failed with code {proc.returncode}: {proc.stderr[:150]}", file=sys.stderr)
            return False

        silence_durations = re.findall(r"silence_duration:\s*([\d\.]+)", proc.stderr)
        total_silent = sum(float(d) for d in silence_durations)
        return total_silent >= (length - 0.8)
    except Exception as exc:
        print(f"Warning: check_is_silent exception: {exc}", file=sys.stderr)
        return False


_LAST_REQUEST_TS = [0.0]


def post(path, key, model, language, prompt, retries=5, min_interval=0.0):
    """Post audio file to Groq Whisper endpoint. Waits for retry-after on 429; optional min_interval spacing."""
    boundary = uuid.uuid4().hex
    fields = [
        ("model", model),
        ("response_format", "verbose_json"),
        ("timestamp_granularities[]", "word"),
        ("timestamp_granularities[]", "segment"),
        ("temperature", "0"),
    ]
    if language:
        fields.append(("language", language))
    if prompt:
        fields.append(("prompt", prompt))

    body = b""
    for k, v in fields:
        body += f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
    body += (
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="a.mp3"\r\n'
        f"Content-Type: audio/mpeg\r\n\r\n"
    ).encode() + open(path, "rb").read() + f"\r\n--{boundary}--\r\n".encode()

    for attempt in range(retries):
        if min_interval > 0:
            wait_s = _LAST_REQUEST_TS[0] + min_interval - time.monotonic()
            if wait_s > 0:
                time.sleep(wait_s)
        _LAST_REQUEST_TS[0] = time.monotonic()
        req = urllib.request.Request(
            ENDPOINT,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "User-Agent": "video-pipeline/1.0",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="ignore")[:300]
            if e.code == 429 and attempt < retries - 1:
                wait = float(e.headers.get("retry-after") or 30)
                print(f"429 rate limit, waiting {wait:.0f}s...", file=sys.stderr)
                time.sleep(wait)
                continue
            sys.exit(f"Groq HTTP {e.code}: {msg}")


def srt_time(t):
    ms = int(round(t * 1000))
    return f"{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}"


def preserve_case(source_text, target_replacement):
    """Case-preserving word replacement (Fix 19).

    If target is mixed-case (e.g. 'DaVinci', 'FilmCraft', 'AI'):
      - Returns uppercase if source is all UPPERCASE ('DAVINCI' -> 'DAVINCI').
      - Returns target verbatim for lowercase or mixed source ('davinci' -> 'DaVinci').
    If target is single-case:
      - Preserves uppercase or capitalization.
    """
    is_mixed_target = any(c.isupper() for c in target_replacement[1:]) or target_replacement.isupper()

    if source_text.isupper():
        return target_replacement.upper()
    if is_mixed_target:
        return target_replacement
    if source_text.istitle() or (source_text and source_text[0].isupper()):
        return target_replacement.capitalize()
    return target_replacement


def _bare(token):
    """Token text without surrounding punctuation (keeps inner apostrophes/hyphens)."""
    return re.sub(r"[^\w'-]", "", token)


def load_correction_rules(corr_dict):
    """Split a {"wrong": "right"} dict into usable same-length rules and refused rules.

    Returns (rules, refused). A rule is (key_tokens_lower, target_tokens, raw_key, raw_target).
    A rule whose key and target token counts differ would merge or split tokens and shift word
    indices, so it is refused.
    """
    rules, refused = [], []
    for k, v in corr_dict.items():
        k_tokens = k.lower().split()
        t_tokens = str(v).split()
        if not k_tokens or not t_tokens:
            refused.append({"type": "refused", "rule": k, "target": v, "reason": "empty key or target"})
        elif len(k_tokens) != len(t_tokens):
            refused.append(
                {
                    "type": "refused",
                    "rule": k,
                    "target": v,
                    "reason": f"key has {len(k_tokens)} token(s) but target has {len(t_tokens)}; "
                              "applying it would merge/split tokens and shift word indices",
                }
            )
        else:
            rules.append((k_tokens, t_tokens, k, v))
    rules.sort(key=lambda r: len(r[0]), reverse=True)
    return rules, refused


def apply_corrections(words, segments, corrections_path):
    """Apply vocabulary corrections one-to-one on tokens (never merging/splitting) and on segment text.

    Idempotent: a token is rewritten only if the case-adjusted target differs from what it already is and
    it has no "corrected_from" marker. Returns (words, segments, log). Input lists are not mutated.
    """
    if not corrections_path or not os.path.exists(corrections_path):
        return words, segments, []

    try:
        corr_dict = json.load(open(corrections_path, "r", encoding="utf-8"))
    except Exception as e:
        print(f"Warning: could not read corrections file {corrections_path}: {e}", file=sys.stderr)
        return words, segments, []

    rules, refused = load_correction_rules(corr_dict)
    for r in refused:
        print(f"Warning: correction rule '{r['rule']}' -> '{r['target']}' REFUSED: {r['reason']}", file=sys.stderr)
    log = list(refused)

    # 1. Word stream: one-to-one over consecutive tokens
    new_words = [dict(w) for w in words]
    idx = 0
    while idx < len(new_words):
        matched = False
        for k_tokens, t_tokens, raw_key, _raw_target in rules:
            k_len = len(k_tokens)
            if idx + k_len > len(new_words):
                continue
            cand = [_bare(new_words[idx + j]["word"]).lower() for j in range(k_len)]
            if cand != k_tokens:
                continue
            if any("corrected_from" in new_words[idx + j] for j in range(k_len)):
                continue
            changed_any = False
            for j in range(k_len):
                w = new_words[idx + j]
                orig = w["word"]
                m_pfx = re.match(r"^([^\w]*)", orig)
                m_sfx = re.search(r"([^\w]*)$", orig)
                pfx = m_pfx.group(1) if m_pfx else ""
                sfx = m_sfx.group(1) if (m_sfx and m_sfx.group(1)) else ""
                bare = orig[len(pfx): len(orig) - len(sfx)] if sfx else orig[len(pfx):]
                body = preserve_case(bare, t_tokens[j])
                new_str = f"{pfx}{body}{sfx}"
                if new_str != orig:
                    w["word"] = new_str
                    w["corrected_from"] = orig
                    changed_any = True
                    log.append(
                        {
                            "type": "word",
                            "index": idx + j,
                            "rule": raw_key,
                            "original": orig,
                            "corrected": new_str,
                            "start": w["start"],
                            "end": w["end"],
                        }
                    )
            idx += k_len
            matched = True
            break
        if not matched:
            idx += 1

    # 2. Segment text (same same-length rules, idempotent by construction)
    new_segments = [dict(s) for s in segments]
    for s in new_segments:
        orig_text = s.get("text", "")
        updated = orig_text
        for _k, _t, raw_key, raw_target in rules:
            pattern = re.compile(rf"\b({re.escape(raw_key)})\b", re.IGNORECASE)
            updated = pattern.sub(lambda m: preserve_case(m.group(0), raw_target), updated)
        if updated != orig_text:
            log.append(
                {
                    "type": "segment",
                    "original": orig_text,
                    "corrected": updated,
                    "start": s.get("start"),
                    "end": s.get("end"),
                }
            )
            s["text"] = updated

    return new_words, new_segments, log


def detect_hallucinations(words):
    """Detect repetitive hallucination phrases using rolling n-grams (Fix 18)."""
    hallucination_phrases = ["and so on", "thank you"]
    matches = []
    num_words = len(words)

    cleaned_tokens = [re.sub(r"[^\w\s]", "", w.get("word", "")).lower().strip() for w in words]

    for i in range(num_words):
        for n in (2, 3, 4):
            if i + n <= num_words:
                ngram = " ".join(cleaned_tokens[i : i + n])
                for phrase in hallucination_phrases:
                    if ngram == phrase:
                        matches.append({"start_idx": i, "end_idx": i + n - 1, "phrase": phrase})

    flagged_windows = []
    if len(matches) >= 2:
        clusters = []
        cur_cluster = [matches[0]]
        for m in matches[1:]:
            prev = cur_cluster[-1]
            prev_end_time = words[prev["end_idx"]]["end"]
            cur_start_time = words[m["start_idx"]]["start"]
            if (cur_start_time - prev_end_time) <= 30.0:
                cur_cluster.append(m)
            else:
                if len(cur_cluster) >= 2:
                    clusters.append(cur_cluster)
                cur_cluster = [m]
        if len(cur_cluster) >= 2:
            clusters.append(cur_cluster)

        for cl in clusters:
            start_i = cl[0]["start_idx"]
            end_i = cl[-1]["end_idx"]
            w_start = max(0.0, words[start_i]["start"] - 0.5)
            w_end = words[end_i]["end"] + 0.5
            phrases = [m["phrase"] for m in cl]
            flagged_windows.append(
                {
                    "start": round(w_start, 3),
                    "end": round(w_end, 3),
                    "duration": round(w_end - w_start, 3),
                    "reason": f"repetitive hallucination cluster: {phrases}",
                }
            )

    return flagged_windows


def detect_density_drops(src_audio, words, total_duration, window_s=8.0, max_words_per_sec=0.5):
    """Detect windows where words/sec < 0.5 over >= 8s while audio is NOT silent (Fix 20)."""
    flagged = []
    if not words or total_duration < window_s:
        return flagged

    step = 4.0
    t = 0.0
    while t + window_s <= total_duration:
        t_end = t + window_s
        words_in_win = [w for w in words if not (w["end"] < t or w["start"] > t_end)]
        density = len(words_in_win) / window_s
        if density < max_words_per_sec:
            # Check if audio is non-silent
            if not check_is_silent(src_audio, t, window_s):
                if not flagged or (t > flagged[-1]["end"]):
                    flagged.append(
                        {
                            "start": round(t, 3),
                            "end": round(t_end, 3),
                            "duration": window_s,
                            "reason": f"words/sec density drop ({density:.2f} w/s < {max_words_per_sec}) over {window_s}s with non-silent audio",
                        }
                    )
        t += step
    return flagged


def detect_and_repair_gaps(src_audio, words, segments, key, language="en", max_windows=None, min_interval=0.0):
    """Unified gap and hallucination repair using whisper-large-v3-turbo."""
    if not words:
        return words, segments, []

    total_dur = max(words[-1]["end"], duration(src_audio) if os.path.exists(src_audio) else 0.0)
    gaps_to_repair = []

    # 1. Gaps >= 8.0s between consecutive words
    for i in range(len(words) - 1):
        w1 = words[i]
        w2 = words[i + 1]
        gap_dur = w2["start"] - w1["end"]
        if gap_dur >= 8.0:
            if not check_is_silent(src_audio, w1["end"], gap_dur):
                gaps_to_repair.append(
                    {
                        "start": round(w1["end"], 3),
                        "end": round(w2["start"], 3),
                        "duration": round(gap_dur, 3),
                        "reason": f"gap >= 8s ({gap_dur:.2f}s) with non-silent speech audio",
                    }
                )

    # 2. Sliding 8s density drops (Fix 20)
    density_drops = detect_density_drops(src_audio, words, total_dur)
    for d in density_drops:
        if not any(g["start"] <= d["start"] and g["end"] >= d["end"] for g in gaps_to_repair):
            gaps_to_repair.append(d)

    # 3. Hallucination clusters (Fix 18)
    hallucs = detect_hallucinations(words)
    for h in hallucs:
        if not any(g["start"] <= h["start"] and g["end"] >= h["end"] for g in gaps_to_repair):
            gaps_to_repair.append(h)

    # Consolidate overlapping windows
    gaps_to_repair.sort(key=lambda x: x["start"])
    consolidated = []
    for g in gaps_to_repair:
        if not consolidated:
            consolidated.append(g)
        else:
            prev = consolidated[-1]
            if g["start"] <= prev["end"]:
                prev["end"] = max(prev["end"], g["end"])
                prev["duration"] = round(prev["end"] - prev["start"], 3)
                prev["reason"] = f"{prev['reason']}; {g['reason']}"
            else:
                consolidated.append(g)

    if max_windows is not None and len(consolidated) > max_windows:
        print(f"Limiting repairs to first {max_windows} window(s) to conserve API quota.", file=sys.stderr)
        consolidated = consolidated[:max_windows]

    if not consolidated:
        return words, segments, []

    print(f"Gap detector flagged {len(consolidated)} window(s) for turbo re-transcription.", file=sys.stderr)

    repairs = []
    new_words = list(words)

    with tempfile.TemporaryDirectory() as td:
        for g_idx, gap in enumerate(consolidated):
            win_start = gap["start"]
            win_dur = gap["duration"]
            part = os.path.join(td, f"repair_{g_idx}.mp3")
            extract(src_audio, part, win_start, win_dur)
            print(f"Re-transcribing window [{win_start:.2f}s - {gap['end']:.2f}s] via whisper-large-v3-turbo...", file=sys.stderr)
            resp = post(part, key, model="whisper-large-v3-turbo", language=language, prompt="", min_interval=min_interval)

            repaired_words = []
            for w in resp.get("words") or []:
                w_start = round(w["start"] + win_start, 3)
                w_end = round(w["end"] + win_start, 3)
                repaired_words.append({"word": w["word"].strip(), "start": w_start, "end": w_end})

            repaired_segments = []
            for s in resp.get("segments") or []:
                repaired_segments.append(
                    {
                        "start": round(s["start"] + win_start, 3),
                        "end": round(s["end"] + win_start, 3),
                        "text": s["text"].strip(),
                    }
                )

            repairs.append(
                {
                    "window_start": round(win_start, 3),
                    "window_end": round(gap["end"], 3),
                    "duration_s": round(win_dur, 3),
                    "reason": gap["reason"],
                    "model": "whisper-large-v3-turbo",
                    "words_added": len(repaired_words),
                    "words": repaired_words,
                }
            )

            # Splice words into stream
            new_words = [w for w in new_words if not (w["start"] >= win_start - 0.05 and w["end"] <= gap["end"] + 0.05)]
            new_words.extend(repaired_words)
            new_words.sort(key=lambda x: x["start"])

            # Splice segments
            segments = [s for s in segments if not (s["start"] >= win_start - 0.05 and s["end"] <= gap["end"] + 0.05)]
            segments.extend(repaired_segments)
            segments.sort(key=lambda x: x["start"])

    return new_words, segments, repairs


def run_selftest():
    """Unit tests: case preservation, stable-index idempotent corrections, hallucinations, 429/pacing, append-only repair logs."""
    import io
    from unittest import mock

    print("Running transcribe_groq.py unit self-test suite...")

    # TC1: preserve_case
    assert preserve_case("davinci", "DaVinci") == "DaVinci"
    assert preserve_case("Davinci", "DaVinci") == "DaVinci"
    assert preserve_case("DAVINCI", "DaVinci") == "DAVINCI"
    assert preserve_case("ai", "AI") == "AI"
    assert preserve_case("filmcraft", "FilmCraft") == "FilmCraft"
    print("  [PASS] TC1: preserve_case handles mixed-case, lowercase, and uppercase targets")

    # TC2: corrections never merge tokens; indices stable; same-length multi-word rule maps 1:1; mismatched rule refused
    mock_words = [
        {"word": "The", "start": 0.0, "end": 0.2},
        {"word": "premiere", "start": 0.3, "end": 0.5},
        {"word": "pro,", "start": 0.5, "end": 0.8},
        {"word": "and", "start": 0.8, "end": 0.9},
        {"word": "film", "start": 0.9, "end": 1.0},
        {"word": "craft", "start": 1.0, "end": 1.2},
        {"word": "DAVINCI", "start": 1.2, "end": 1.6},
        {"word": "davinci.", "start": 1.6, "end": 2.0},
    ]
    mock_segments = [{"text": "The premiere pro, and film craft DAVINCI davinci.", "start": 0.0, "end": 2.0}]
    with tempfile.TemporaryDirectory() as td:
        cpath = os.path.join(td, "corr.json")
        with open(cpath, "w", encoding="utf-8") as f:
            json.dump({"premiere pro": "Premiere Pro", "film craft": "FilmCraft", "davinci": "DaVinci"}, f)
        err = io.StringIO()
        with mock.patch("sys.stderr", err):
            w1, s1, log1 = apply_corrections(mock_words, mock_segments, cpath)
        assert len(w1) == len(mock_words) == 8, "TC2: token count must not change"
        assert [w["start"] for w in w1] == [w["start"] for w in mock_words], "TC2: timestamps must not move"
        assert [w["word"] for w in w1] == ["The", "Premiere", "Pro,", "and", "film", "craft", "DAVINCI", "DaVinci."], [w["word"] for w in w1]
        assert w1[1]["corrected_from"] == "premiere" and w1[2]["corrected_from"] == "pro,", "TC2: marker missing"
        assert "corrected_from" not in w1[6], "TC2: 'DAVINCI' keeps its case, so it is not a change"
        refused = [e for e in log1 if e["type"] == "refused"]
        assert len(refused) == 1 and refused[0]["rule"] == "film craft", refused
        assert "REFUSED" in err.getvalue() and "film craft" in err.getvalue()
        assert [e["index"] for e in log1 if e["type"] == "word"] == [1, 2, 7], "TC2: logged indices"
        assert s1[0]["text"] == "The Premiere Pro, and film craft DAVINCI DaVinci.", s1[0]["text"]
        # idempotence: a second pass over the corrected output changes nothing and logs nothing but the refusal
        with mock.patch("sys.stderr", io.StringIO()):
            w2, s2, log2 = apply_corrections(w1, s1, cpath)
        assert w2 == w1 and s2 == s1, "TC2: second pass changed the data"
        assert [e["type"] for e in log2] == ["refused"], log2
    print("  [PASS] TC2: 1:1 corrections, stable indices, mismatched rule refused, second pass is a no-op")

    # TC3: Hallucination detection on [and, so, on, and, so, on]
    halluc_words = [
        {"word": "Start", "start": 1.0, "end": 1.2},
        {"word": "and", "start": 2.0, "end": 2.2}, {"word": "so", "start": 2.2, "end": 2.4}, {"word": "on", "start": 2.4, "end": 2.6},
        {"word": "and", "start": 3.0, "end": 3.2}, {"word": "so", "start": 3.2, "end": 3.4}, {"word": "on", "start": 3.4, "end": 3.6},
        {"word": "Finish", "start": 4.0, "end": 4.2},
    ]
    h_windows = detect_hallucinations(halluc_words)
    assert len(h_windows) == 1 and h_windows[0]["reason"] == "repetitive hallucination cluster: ['and so on', 'and so on']", h_windows
    print("  [PASS] TC3: hallucination cluster flagged with reason string")

    # TC4: post(): 429 waits retry-after then succeeds; NO audio-seconds pacing; min_interval spaces requests
    class _Resp:
        def __init__(self, body, headers=None):
            self._b, self.headers = body, headers or {}

        def read(self, *a):
            return self._b

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    with tempfile.NamedTemporaryFile("wb", suffix=".mp3", delete=False) as tf:
        tf.write(b"x")
        mp3 = tf.name
    try:
        calls = []

        def fake_urlopen(req, timeout=0):
            calls.append(1)
            if len(calls) == 1:
                raise urllib.error.HTTPError(req.full_url, 429, "Too Many", {"retry-after": "7"}, io.BytesIO(b"{}"))
            # a success response that carries the audio-seconds header must NOT trigger any sleep
            return _Resp(b'{"words": []}', {"x-ratelimit-remaining-audio-seconds": "1", "x-ratelimit-reset-audio-seconds": "99"})

        sleeps = []
        with mock.patch("urllib.request.urlopen", fake_urlopen), mock.patch("time.sleep", sleeps.append):
            out = post(mp3, "gsk_test", "m", "en", "")
        assert out == {"words": []} and len(calls) == 2
        assert sleeps == [7.0], f"TC4: expected exactly the 429 retry-after sleep, got {sleeps}"
        sleeps.clear()

        def ok_urlopen(req, timeout=0):
            return _Resp(b'{"words": []}')

        _LAST_REQUEST_TS[0] = time.monotonic()
        with mock.patch("urllib.request.urlopen", ok_urlopen), mock.patch("time.sleep", sleeps.append):
            post(mp3, "gsk_test", "m", "en", "", min_interval=3.0)
        assert len(sleeps) == 1 and 2.0 < sleeps[0] <= 3.0, sleeps
    finally:
        os.remove(mp3)
    print("  [PASS] TC4: 429 sleeps exactly retry-after (7 s); audio-seconds header ignored; --min-interval spacing applied")

    # TC5: --repair-only appends to existing repairs/corrections instead of replacing them
    with tempfile.TemporaryDirectory() as td:
        media = os.path.join(td, "m.mp4")
        with open(media, "wb") as f:
            f.write(b"x")
        wpath = os.path.join(td, "words.json")
        outp = os.path.join(td, "out.json")
        cpath = os.path.join(td, "corr.json")
        with open(cpath, "w") as f:
            json.dump({"instagram": "Instagram"}, f)
        prior_repair = {"window_start": 1.0, "window_end": 2.0, "reason": "PRIOR REPAIR"}
        prior_corr = {"type": "word", "index": 0, "original": "a", "corrected": "A"}
        with open(wpath, "w") as f:
            json.dump(
                {"source": media, "model": "whisper-large-v3", "duration_s": 5.0,
                 "words": [{"word": "instagram", "start": 0.0, "end": 0.5}],
                 "segments": [{"text": "instagram", "start": 0.0, "end": 0.5}],
                 "repairs": [prior_repair], "corrections": [prior_corr]},
                f,
            )
        new_repair = {"window_start": 3.0, "window_end": 4.0, "reason": "NEW REPAIR"}

        def fake_repair(src, words, segments, key, language="en", max_windows=None, min_interval=0.0):
            return words, segments, [new_repair]

        me = sys.modules[__name__]
        argv = ["transcribe_groq.py", "--repair-only", wpath, "--out", outp, "--corrections", cpath]
        with mock.patch.object(sys, "argv", argv), mock.patch.object(me, "detect_and_repair_gaps", fake_repair), \
                mock.patch.object(me, "get_key", lambda: "gsk_test"), mock.patch("sys.stdout", io.StringIO()):
            main()
        res = json.load(open(outp, encoding="utf-8"))
        assert [r["reason"] for r in res["repairs"]] == ["PRIOR REPAIR", "NEW REPAIR"], res["repairs"]
        assert res["corrections"][0] == prior_corr and any(c.get("original") == "instagram" for c in res["corrections"][1:]), res["corrections"]
        assert res["words"][0]["word"] == "Instagram" and res["words"][0]["corrected_from"] == "instagram"
    print("  [PASS] TC5: --repair-only appends: prior repair + prior correction preserved, new ones added")

    print("ALL 5 TRANSCRIBE_GROQ SELF-TEST CASES PASSED CLEANLY.")


def main():
    ap = argparse.ArgumentParser(description="Word-level transcription via Groq Whisper API with gap repair.")
    ap.add_argument("--input", help="Input media file (video or audio)")
    ap.add_argument("--out", help="Output words.json path")
    ap.add_argument("--model", default="whisper-large-v3", help="Groq Whisper model (default: whisper-large-v3)")
    ap.add_argument("--language", default="en", help="Language code (default: en)")
    ap.add_argument("--prompt", default="", help="Optional vocabulary bias prompt")
    ap.add_argument("--chunk-s", type=float, default=600, help="Chunk length in seconds (default: 600)")
    ap.add_argument("--force", action="store_true", help="Force re-transcription if --out exists")
    ap.add_argument("--corrections", default=None, help="Path to transcript_corrections.json")
    ap.add_argument("--no-repair", action="store_true", help="Disable automatic gap repair")
    ap.add_argument("--repair-only", help="Path to existing words.json to repair gaps/corrections on without full re-transcription (Fix 20)")
    ap.add_argument("--max-repair-windows", type=int, default=None, help="Cap number of repaired windows to conserve API quota")
    ap.add_argument("--min-interval", type=float, default=0.0, help="Minimum seconds between consecutive Groq requests (default: 0; 429 retry-after is always honoured)")
    ap.add_argument("--selftest", action="store_true", help="Run unit self-tests and exit")

    args = ap.parse_args()

    if args.selftest:
        run_selftest()
        sys.exit(0)

    if not args.out:
        ap.error("--out is required unless --selftest is passed.")

    # Fix 20: Support --repair-only mode
    if args.repair_only:
        if not os.path.exists(args.repair_only):
            sys.exit(f"File not found for --repair-only: {args.repair_only}")

        with open(args.repair_only, "r", encoding="utf-8") as f:
            existing_data = json.load(f)

        src_media = args.input or existing_data.get("source")
        if not src_media or not os.path.exists(src_media):
            sys.exit(f"Source media not found for repair: {src_media}")

        words = existing_data.get("words", [])
        segments = existing_data.get("segments", [])
        total = existing_data.get("duration_s") or duration(src_media)

        repairs = []
        if not args.no_repair:
            key = get_key()
            words, segments, repairs = detect_and_repair_gaps(
                src_media,
                words,
                segments,
                key,
                args.language,
                max_windows=args.max_repair_windows,
                min_interval=args.min_interval,
            )

        logged_corrections = []
        if args.corrections:
            words, segments, logged_corrections = apply_corrections(words, segments, args.corrections)

        # Append to (never replace) the existing provenance logs
        all_repairs = list(existing_data.get("repairs") or []) + repairs
        all_corrections = list(existing_data.get("corrections") or []) + logged_corrections

        payload = {
            "source": os.path.abspath(src_media),
            "engine": "groq",
            "model": existing_data.get("model", args.model),
            "language": args.language,
            "duration_s": round(total, 3),
            "words": words,
            "segments": segments,
            "repairs": all_repairs,
            "corrections": all_corrections,
        }

        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        stem = os.path.splitext(args.out)[0]
        with open(stem + ".srt", "w", encoding="utf-8") as f:
            for i, s in enumerate(segments, 1):
                f.write(f"{i}\n{srt_time(s['start'])} --> {srt_time(s['end'])}\n{s['text']}\n\n")
        with open(stem + ".txt", "w", encoding="utf-8") as f:
            f.write("\n".join(f"[{int(s['start'])//60:02d}:{int(s['start'])%60:02d}] {s['text']}" for s in segments))

        print(
            f"Repaired: {len(words)} words, {len(segments)} segments, {len(repairs)} new repairs "
            f"({len(all_repairs)} total), {len(logged_corrections)} new corrections ({len(all_corrections)} total) -> {args.out}"
        )
        return

    if not args.input:
        ap.error("--input is required unless --selftest or --repair-only is passed.")

    if os.path.exists(args.out) and not args.force:
        print(f"exists, not re-transcribing: {args.out}")
        return

    key = get_key()
    total = duration(args.input)
    words, segments = [], []
    with tempfile.TemporaryDirectory() as td:
        start = 0.0
        while start < total - 0.05:
            length = min(args.chunk_s, total - start)
            part = os.path.join(td, f"c{int(start)}.mp3")
            extract(args.input, part, start, length)
            r = post(part, key, args.model, args.language, args.prompt, min_interval=args.min_interval)
            for w in r.get("words") or []:
                words.append(
                    {
                        "word": w["word"].strip(),
                        "start": round(w["start"] + start, 3),
                        "end": round(w["end"] + start, 3),
                    }
                )
            for s in r.get("segments") or []:
                segments.append(
                    {
                        "start": round(s["start"] + start, 3),
                        "end": round(s["end"] + start, 3),
                        "text": s["text"].strip(),
                    }
                )
            print(f"chunk {start:.0f}-{start+length:.0f}s: {len(r.get('words') or [])} words", file=sys.stderr)
            start += length

    if not words:
        sys.exit("No word timestamps returned.")

    repairs = []
    if not args.no_repair:
        words, segments, repairs = detect_and_repair_gaps(
            args.input, words, segments, key, args.language, max_windows=args.max_repair_windows,
            min_interval=args.min_interval,
        )

    logged_corrections = []
    if args.corrections:
        words, segments, logged_corrections = apply_corrections(words, segments, args.corrections)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    payload = {
        "source": os.path.abspath(args.input),
        "engine": "groq",
        "model": args.model,
        "language": args.language,
        "duration_s": round(total, 3),
        "words": words,
        "segments": segments,
        "repairs": repairs,
        "corrections": logged_corrections,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    stem = os.path.splitext(args.out)[0]
    with open(stem + ".srt", "w", encoding="utf-8") as f:
        for i, s in enumerate(segments, 1):
            f.write(f"{i}\n{srt_time(s['start'])} --> {srt_time(s['end'])}\n{s['text']}\n\n")
    with open(stem + ".txt", "w", encoding="utf-8") as f:
        f.write("\n".join(f"[{int(s['start'])//60:02d}:{int(s['start'])%60:02d}] {s['text']}" for s in segments))

    print(
        f"{len(words)} words, {len(segments)} segments, {len(repairs)} repairs, "
        f"{len(logged_corrections)} corrections -> {args.out}"
    )


if __name__ == "__main__":
    main()

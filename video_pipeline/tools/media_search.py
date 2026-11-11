"""
Internet Media Search CLI (media_search.py)
Unified multi-engine search, extraction, and OSINT toolkit for images, stock video,
archival footage, spoken transcripts, sound effects, and video keyframes.

Engines & Capabilities:
1. High-Resolution Images:
   - Wikimedia Commons API (unlimited public domain & CC media, direct hi-res URLs)
   - DuckDuckGo / Bing Image API (filters: layout, size, type, transparent PNG)
   - Pixabay Images API (commercial CC0 imagery)
2. Stock Video & B-Roll:
   - Pexels Video API (4K & 1080p horizontal/vertical B-roll, direct MP4 streams)
   - Pixabay Video API (motion graphics, aerials, cinematic b-roll, direct MP4 streams)
3. Archival, Documentary & Science Footage:
   - Internet Archive Movies REST API (archive.org mediatype:movies, direct MP4 URLs)
   - NASA Image & Video Library API (images-api.nasa.gov, space/science 4K/HD MP4s)
4. Video Intelligence & Transcripts:
   - YouTube Deep Search via yt-dlp (metadata, view counts, duration, 1080p thumbnails)
   - YouTube Transcript API (word-level verbatim subtitles with timestamp navigation)
5. Sound Effects & Audio (SFX):
   - Wikimedia Commons Audio API (foley, nature, speech, public domain audio)
   - Freesound API (field recordings, sound effects, CC0/CC-BY audio)
6. Reverse Video Search & Visual Verification:
   - FFmpeg Scene-Detection Keyframe Extraction (select='gt(scene,0.35)')
   - Automated generation of Yandex Visual Search & Google Lens inspection links
7. Safe Asset Downloader:
   - Direct streaming downloads with PIL image validation and curl fallback
   - Video section clipping and thumbnail downloads via yt-dlp
"""

import os
import re
import sys
import warnings

# Suppress library deprecation and package rename warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message=".*renamed to.*")
warnings.filterwarnings("ignore", message=".*duckduckgo_search.*")

import json
import hashlib
import time
import argparse
import configparser
import subprocess
import urllib.parse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Enforce UTF-8 output on Windows pwsh / cmd
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import requests
from PIL import Image

# Graceful optional imports
try:
    from duckduckgo_search import DDGS
    HAS_DDGS = True
except ImportError:
    HAS_DDGS = False

try:
    import yt_dlp
    HAS_YTDLP = True
except ImportError:
    HAS_YTDLP = False

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    HAS_TRANSCRIPT_API = True
except ImportError:
    HAS_TRANSCRIPT_API = False


# ==============================================================================
# Configuration & API Key Discovery
# ==============================================================================
API_KEYS_FILE = r"C:\portable_apps\my_scripts\autohotkey\ApiKeys-Auth-Token-Passwords\ApiKeys.ini"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
REQUEST_TIMEOUT = 14

def get_api_key(key_name: str) -> Optional[str]:
    """Retrieve API key from environment or ApiKeys.ini without exposing secrets."""
    env_val = os.environ.get(key_name.upper()) or os.environ.get(key_name)
    if env_val:
        return env_val

    if os.path.exists(API_KEYS_FILE):
        try:
            config = configparser.ConfigParser()
            config.read(API_KEYS_FILE, encoding="utf-8")
            for section in config.sections():
                if config.has_option(section, key_name):
                    val = config.get(section, key_name).strip()
                    if val:
                        return val
        except Exception:
            pass
    return None


# ==============================================================================
# 1. Image Search Implementations
# ==============================================================================
def search_wikimedia_images(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search Wikimedia Commons for high-resolution public domain and CC images."""
    url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": 6,  # File namespace
        "gsrlimit": max(limit * 2, 10),
        "prop": "imageinfo",
        "iiprop": "url|size|mime|extmetadata",
        "iiurlwidth": 1920,
        "format": "json"
    }
    headers = {"User-Agent": f"MediaSearchAgent/2.5 ({USER_AGENT})"}
    results: List[Dict[str, Any]] = []

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            pages = data.get("query", {}).get("pages", {})
            for pid, pdata in pages.items():
                imageinfo = pdata.get("imageinfo", [{}])[0]
                meta = imageinfo.get("extmetadata", {})
                title = pdata.get("title", "").replace("File:", "")
                img_url = imageinfo.get("url")
                mime_t = (imageinfo.get("mime") or "").lower()
                if not img_url or ("image/" not in mime_t and not img_url.lower().split("?")[0].endswith((".jpg", ".jpeg", ".png", ".webp"))):
                    continue
                img_url = img_url.split("?")[0]
                if len(results) >= limit:
                    break

                results.append({
                    "title": title,
                    "image_url": img_url,
                    "thumbnail_url": imageinfo.get("thumburl") or img_url,
                    "width": imageinfo.get("width"),
                    "height": imageinfo.get("height"),
                    "mime_type": imageinfo.get("mime"),
                    "source": "Wikimedia Commons",
                    "license": meta.get("LicenseShortName", {}).get("value", "CC / Public Domain"),
                    "author": meta.get("Artist", {}).get("value", "Unknown"),
                    "description": meta.get("ImageDescription", {}).get("value", "")[:200]
                })
    except Exception as e:
        sys.stderr.write(f"[!] Wikimedia Commons search error: {e}\n")

    return results


def search_ddg_images(
    query: str,
    limit: int = 10,
    size: Optional[str] = None,
    type_image: Optional[str] = None,
    layout: Optional[str] = None,
    license_image: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Search images via DuckDuckGo / Bing media index."""
    if not HAS_DDGS:
        return []

    results: List[Dict[str, Any]] = []
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with DDGS() as ddgs:
                raw_results = ddgs.images(
                    keywords=query,
                    size=size,
                    type_image=type_image,
                    layout=layout,
                    license_image=license_image,
                    max_results=limit
                )
                for item in raw_results:
                    results.append({
                        "title": item.get("title", ""),
                        "image_url": item.get("image", ""),
                        "thumbnail_url": item.get("thumbnail", ""),
                        "width": item.get("width"),
                        "height": item.get("height"),
                        "source": item.get("source", "DuckDuckGo"),
                        "page_url": item.get("url", ""),
                        "license": "Web / Indexed"
                    })
    except Exception as e:
        sys.stderr.write(f"[!] DuckDuckGo image search error: {e}\n")

    return results


def search_pixabay_images(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search images via Pixabay API if key is available."""
    api_key = get_api_key("PixabayApiKey") or get_api_key("PIXABAY_API_KEY")
    if not api_key:
        return []

    url = "https://pixabay.com/api/"
    params = {
        "key": api_key,
        "q": query,
        "per_page": min(limit, 50),
        "safesearch": "true"
    }
    results: List[Dict[str, Any]] = []
    try:
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            hits = resp.json().get("hits", [])
            for hit in hits:
                results.append({
                    "title": hit.get("tags", query),
                    "image_url": hit.get("largeImageURL", ""),
                    "thumbnail_url": hit.get("previewURL", ""),
                    "width": hit.get("imageWidth"),
                    "height": hit.get("imageHeight"),
                    "source": "Pixabay",
                    "page_url": hit.get("pageURL", ""),
                    "license": "Pixabay Free License"
                })
    except Exception as e:
        sys.stderr.write(f"[!] Pixabay image search error: {e}\n")

    return results


def search_images(
    query: str,
    limit: int = 10,
    engine: str = "auto",
    size: Optional[str] = None,
    type_image: Optional[str] = None,
    layout: Optional[str] = None,
    license_image: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Unified multi-engine image search with automatic resilient fallback."""
    all_results: List[Dict[str, Any]] = []

    if engine == "wikimedia":
        return search_wikimedia_images(query, limit=limit)
    elif engine == "ddg":
        return search_ddg_images(query, limit=limit, size=size, type_image=type_image, layout=layout, license_image=license_image)
    elif engine == "pixabay":
        return search_pixabay_images(query, limit=limit)

    ddg_res = search_ddg_images(query, limit=limit, size=size, type_image=type_image, layout=layout, license_image=license_image)
    if ddg_res:
        all_results.extend(ddg_res)

    if len(all_results) < limit:
        wiki_limit = limit - len(all_results)
        wiki_res = search_wikimedia_images(query, limit=max(wiki_limit, 5))
        all_results.extend(wiki_res)

    if len(all_results) < limit:
        pix_res = search_pixabay_images(query, limit=limit)
        all_results.extend(pix_res)

    seen = set()
    deduped = []
    for item in all_results:
        url = item.get("image_url")
        if url and url not in seen:
            seen.add(url)
            deduped.append(item)

    return deduped[:limit]


# ==============================================================================
# 2. Archival & Scientific Video Search (Internet Archive + NASA)
# ==============================================================================
def search_internet_archive_videos(query: str, limit: int = 6) -> List[Dict[str, Any]]:
    """Search Internet Archive Movies collections (100% Free, No API Key needed)."""
    url = "https://archive.org/advancedsearch.php"
    params = {
        "q": f"mediatype:movies AND ({query})",
        "fl[]": ["identifier", "title", "description", "year", "downloads", "publicdate"],
        "sort[]": "downloads desc",
        "rows": limit,
        "output": "json"
    }
    headers = {"User-Agent": f"MediaSearchAgent/2.5 ({USER_AGENT})"}
    results: List[Dict[str, Any]] = []

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            docs = resp.json().get("response", {}).get("docs", [])
            for doc in docs:
                ident = doc.get("identifier")
                if not ident:
                    continue

                page_url = f"https://archive.org/details/{ident}"
                video_url = f"https://archive.org/download/{ident}/{ident}.mp4"
                thumb_url = f"https://archive.org/services/img/{ident}"

                results.append({
                    "id": ident,
                    "title": doc.get("title", ident),
                    "url": page_url,
                    "direct_video_url": video_url,
                    "thumbnail_url": thumb_url,
                    "year": doc.get("year"),
                    "downloads": doc.get("downloads"),
                    "source": "Internet Archive (Movies)",
                    "license": "Public Domain / CC / Open Archive",
                    "description": (doc.get("description") or "")[:250]
                })
    except Exception as e:
        sys.stderr.write(f"[!] Internet Archive search error: {e}\n")

    return results


def search_nasa_videos(query: str, limit: int = 6) -> List[Dict[str, Any]]:
    """Search NASA Image and Video Library (100% Free, No API Key needed)."""
    url = "https://images-api.nasa.gov/search"
    params = {
        "q": query,
        "media_type": "video"
    }
    headers = {"User-Agent": f"MediaSearchAgent/2.5 ({USER_AGENT})"}
    results: List[Dict[str, Any]] = []

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            items = resp.json().get("collection", {}).get("items", [])[:limit]
            for item in items:
                data = item.get("data", [{}])[0]
                nasa_id = data.get("nasa_id")
                if not nasa_id:
                    continue

                title = data.get("title", nasa_id)
                links = item.get("links", [])
                thumb = links[0].get("href") if links else ""
                
                mp4_url = ""
                try:
                    asset_resp = requests.get(f"https://images-api.nasa.gov/asset/{nasa_id}", timeout=6)
                    if asset_resp.status_code == 200:
                        manifest_items = asset_resp.json().get("collection", {}).get("items", [])
                        mp4_candidates = [f["href"] for f in manifest_items if f.get("href", "").endswith(".mp4")]
                        for c in mp4_candidates:
                            if "~orig.mp4" in c or "~medium.mp4" in c or "~large.mp4" in c:
                                mp4_url = c
                                break
                        if not mp4_url and mp4_candidates:
                            mp4_url = mp4_candidates[0]
                except Exception:
                    pass

                results.append({
                    "id": nasa_id,
                    "title": title,
                    "url": f"https://images.nasa.gov/details/{nasa_id}",
                    "direct_video_url": mp4_url or f"https://images.nasa.gov/details/{nasa_id}",
                    "thumbnail_url": thumb,
                    "center": data.get("center"),
                    "date_created": data.get("date_created"),
                    "source": "NASA Media Library",
                    "license": "Public Domain (NASA)",
                    "description": (data.get("description") or "")[:250]
                })
    except Exception as e:
        sys.stderr.write(f"[!] NASA Media search error: {e}\n")

    return results


def search_archive_media(query: str, limit: int = 6, collection: str = "all") -> List[Dict[str, Any]]:
    """Unified search across Internet Archive and NASA media repositories."""
    results: List[Dict[str, Any]] = []

    if collection in ["all", "nasa"]:
        nasa_res = search_nasa_videos(query, limit=limit)
        results.extend(nasa_res)

    if collection in ["all", "internetarchive"] and len(results) < limit:
        arch_limit = limit - len(results) if collection == "all" else limit
        arch_res = search_internet_archive_videos(query, limit=max(arch_limit, 3))
        results.extend(arch_res)

    return results[:limit]


# ==============================================================================
# 3. Stock Video & B-Roll APIs (Pexels + Pixabay)
# ==============================================================================
def search_pexels_videos(
    query: str,
    limit: int = 6,
    orientation: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Search Pexels Videos API for 4K/HD royalty-free B-roll."""
    api_key = get_api_key("PexelsApiKey") or get_api_key("PEXELS_API_KEY")
    if not api_key:
        return []

    url = "https://api.pexels.com/videos/search"
    headers = {"Authorization": api_key}
    params: Dict[str, Any] = {
        "query": query,
        "per_page": min(limit, 30)
    }
    if orientation in ["landscape", "portrait", "square"]:
        params["orientation"] = orientation

    results: List[Dict[str, Any]] = []
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            videos = resp.json().get("videos", [])
            for v in videos:
                vid_files = v.get("video_files", [])
                best_file = None
                max_w = 0
                for f in vid_files:
                    if f.get("file_type") == "video/mp4" and (f.get("width") or 0) > max_w:
                        max_w = f.get("width") or 0
                        best_file = f

                results.append({
                    "id": v.get("id"),
                    "title": f"Pexels B-Roll: {query} ({v.get('width')}x{v.get('height')})",
                    "url": v.get("url"),
                    "direct_video_url": best_file.get("link") if best_file else "",
                    "thumbnail_url": v.get("image"),
                    "width": v.get("width"),
                    "height": v.get("height"),
                    "duration_seconds": v.get("duration"),
                    "author": v.get("user", {}).get("name", "Pexels Creator"),
                    "source": "Pexels Video",
                    "license": "Pexels Free Commercial License"
                })
    except Exception as e:
        sys.stderr.write(f"[!] Pexels video search error: {e}\n")

    return results


def search_pixabay_videos(query: str, limit: int = 6) -> List[Dict[str, Any]]:
    """Search Pixabay Videos API for stock footage."""
    api_key = get_api_key("PixabayApiKey") or get_api_key("PIXABAY_API_KEY")
    if not api_key:
        return []

    url = "https://pixabay.com/api/videos/"
    params = {
        "key": api_key,
        "q": query,
        "per_page": min(limit, 30),
        "safesearch": "true"
    }
    results: List[Dict[str, Any]] = []
    try:
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            hits = resp.json().get("hits", [])
            for hit in hits:
                vids = hit.get("videos", {})
                best = vids.get("large") or vids.get("medium") or vids.get("small") or {}
                results.append({
                    "id": hit.get("id"),
                    "title": hit.get("tags", query),
                    "url": hit.get("pageURL"),
                    "direct_video_url": best.get("url"),
                    "thumbnail_url": hit.get("videos", {}).get("tiny", {}).get("thumbnail") or f"https://i.vimeocdn.com/video/{hit.get('picture_id')}_640x360.jpg",
                    "width": best.get("width"),
                    "height": best.get("height"),
                    "duration_seconds": hit.get("duration"),
                    "views": hit.get("views"),
                    "downloads": hit.get("downloads"),
                    "source": "Pixabay Video",
                    "license": "Pixabay Free Commercial License"
                })
    except Exception as e:
        sys.stderr.write(f"[!] Pixabay video search error: {e}\n")

    return results


def search_stock_videos(
    query: str,
    limit: int = 6,
    orientation: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Unified B-roll stock video search across Pexels, Pixabay, and fallback sources."""
    results: List[Dict[str, Any]] = []

    # 1. Pexels Videos
    pex_res = search_pexels_videos(query, limit=limit, orientation=orientation)
    results.extend(pex_res)

    # 2. Pixabay Videos
    if len(results) < limit:
        pix_res = search_pixabay_videos(query, limit=limit - len(results))
        results.extend(pix_res)

    # 3. Fallback to open Archive / NASA if no stock API keys configured
    if not results:
        archive_res = search_archive_media(query, limit=limit)
        results.extend(archive_res)

    return results[:limit]


# ==============================================================================
# 4. Audio & Sound Effects Search (Wikimedia Audio + Freesound)
# ==============================================================================
def search_wikimedia_audio(query: str, limit: int = 6) -> List[Dict[str, Any]]:
    """Search Wikimedia Commons for public domain & Creative Commons sound effects and music."""
    url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": f"filetype:audio {query}",
        "gsrnamespace": 6,
        "gsrlimit": limit,
        "prop": "imageinfo",
        "iiprop": "url|size|mime|extmetadata",
        "format": "json"
    }
    headers = {"User-Agent": f"MediaSearchAgent/2.5 ({USER_AGENT})"}
    results: List[Dict[str, Any]] = []

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            pages = resp.json().get("query", {}).get("pages", {})
            for pid, pdata in pages.items():
                imageinfo = pdata.get("imageinfo", [{}])[0]
                meta = imageinfo.get("extmetadata", {})
                title = pdata.get("title", "").replace("File:", "")
                audio_url = imageinfo.get("url")
                if not audio_url:
                    continue

                results.append({
                    "title": title,
                    "audio_url": audio_url,
                    "mime_type": imageinfo.get("mime"),
                    "size_bytes": imageinfo.get("size"),
                    "source": "Wikimedia Commons Audio",
                    "license": meta.get("LicenseShortName", {}).get("value", "CC / Public Domain"),
                    "author": meta.get("Artist", {}).get("value", "Unknown"),
                    "description": meta.get("ImageDescription", {}).get("value", "")[:200]
                })
    except Exception as e:
        sys.stderr.write(f"[!] Wikimedia Audio search error: {e}\n")

    return results


def search_freesound_audio(query: str, limit: int = 6) -> List[Dict[str, Any]]:
    """Search Freesound.org API for sound effects and foley if API key is present."""
    api_key = get_api_key("FreesoundApiKey") or get_api_key("FREESOUND_API_KEY")
    if not api_key:
        return []

    url = "https://freesound.org/apiv2/search/text/"
    headers = {"Authorization": f"Token {api_key}"}
    params = {
        "query": query,
        "page_size": min(limit, 30),
        "fields": "id,name,tags,description,previews,license,duration,username"
    }
    results: List[Dict[str, Any]] = []
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            items = resp.json().get("results", [])
            for item in items:
                previews = item.get("previews", {})
                audio_link = previews.get("preview-hq-mp3") or previews.get("preview-lq-mp3") or ""
                results.append({
                    "id": item.get("id"),
                    "title": item.get("name"),
                    "audio_url": audio_link,
                    "duration_seconds": item.get("duration"),
                    "author": item.get("username"),
                    "license": item.get("license"),
                    "source": "Freesound.org",
                    "description": (item.get("description") or "")[:200]
                })
    except Exception as e:
        sys.stderr.write(f"[!] Freesound search error: {e}\n")

    return results


def search_audio_sfx(query: str, limit: int = 6) -> List[Dict[str, Any]]:
    """Unified audio & SFX search across Freesound and Wikimedia Commons Audio."""
    results: List[Dict[str, Any]] = []

    fs_res = search_freesound_audio(query, limit=limit)
    results.extend(fs_res)

    if len(results) < limit:
        wiki_res = search_wikimedia_audio(query, limit=limit - len(results))
        results.extend(wiki_res)

    return results[:limit]


# ==============================================================================
# 5. Reverse Video Search & Keyframe Visual OSINT
# ==============================================================================
def extract_video_keyframes(
    video_path_or_url: str,
    output_dir: str,
    max_frames: int = 5,
    threshold: float = 0.35
) -> Dict[str, Any]:
    """
    Extract scene-detection keyframes from video using FFmpeg and prepare
    direct reverse image search URLs (Yandex Visual & Google Lens).
    """
    os.makedirs(output_dir, exist_ok=True)
    local_video_path = video_path_or_url

    is_temp_download = False
    if "http://" in video_path_or_url or "https://" in video_path_or_url:
        is_temp_download = True
        temp_dl = download_video_clip(video_path_or_url, output_dir, filename="temp_reverse_target.mp4", max_height=360)
        if temp_dl.get("status") != "success":
            return {"status": "error", "error": f"Failed to download video snippet for keyframe extraction: {temp_dl.get('error')}"}
        local_video_path = temp_dl["file_path"]

    out_pattern = os.path.join(output_dir, "keyframe_%03d.jpg")

    cmd = [
        "ffmpeg", "-y", "-i", local_video_path,
        "-vf", f"select=gt(scene\\,{threshold})",
        "-vsync", "vfr",
        "-frames:v", str(max_frames),
        "-q:v", "2",
        out_pattern
    ]

    try:
        subprocess.run(cmd, capture_output=True, timeout=60)
    except Exception as e:
        return {"status": "error", "error": f"FFmpeg scene extraction failed: {e}"}

    frames = sorted([str(p.resolve()) for p in Path(output_dir).glob("keyframe_*.jpg")])

    if len(frames) < 2:
        fallback_pattern = os.path.join(output_dir, "frame_fallback_%03d.jpg")
        cmd_fallback = [
            "ffmpeg", "-y", "-i", local_video_path,
            "-vf", "fps=1/4",
            "-frames:v", str(max_frames),
            "-q:v", "2",
            fallback_pattern
        ]
        try:
            subprocess.run(cmd_fallback, capture_output=True, timeout=60)
            frames = sorted([str(p.resolve()) for p in Path(output_dir).glob("*.jpg")])
        except Exception:
            pass

    keyframe_data = []
    for f in frames[:max_frames]:
        fname = os.path.basename(f)
        keyframe_data.append({
            "frame_file": fname,
            "absolute_path": f,
            "yandex_reverse_url": "https://yandex.com/images/search?rpt=imageview",
            "google_lens_url": "https://lens.google.com/upload",
            "reverse_search_instructions": (
                f"1. Upload '{fname}' to Yandex Images (https://yandex.com/images/search?rpt=imageview) for exact face/scene matching.\n"
                f"2. Or upload to Google Lens for OCR, landmarks, and social context."
            )
        })

    if is_temp_download and os.path.exists(local_video_path):
        try:
            os.remove(local_video_path)
        except Exception:
            pass

    return {
        "status": "success",
        "source_video": video_path_or_url,
        "keyframes_extracted": len(keyframe_data),
        "output_directory": os.path.abspath(output_dir),
        "keyframes": keyframe_data
    }


# ==============================================================================
# 6. YouTube & General Video Search
# ==============================================================================
def search_youtube_ytdlp(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search YouTube videos with yt-dlp extracting rich metadata and HD thumbnails."""
    if not HAS_YTDLP:
        return []

    results: List[Dict[str, Any]] = []
    ydl_opts = {
        "extract_flat": True,
        "quiet": True,
        "no_warnings": True,
        "skip_download": True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_query = f"ytsearch{limit}:{query}"
            info = ydl.extract_info(search_query, download=False)
            entries = info.get("entries", []) if info else []

            for entry in entries:
                vid_id = entry.get("id")
                if not vid_id:
                    continue

                duration_sec = entry.get("duration")
                duration_str = None
                if duration_sec is not None:
                    mins = int(duration_sec // 60)
                    secs = int(duration_sec % 60)
                    duration_str = f"{mins}:{secs:02d}"

                results.append({
                    "id": vid_id,
                    "title": entry.get("title", ""),
                    "url": f"https://www.youtube.com/watch?v={vid_id}",
                    "channel": entry.get("channel") or entry.get("uploader") or "",
                    "duration_seconds": duration_sec,
                    "duration_formatted": duration_str,
                    "view_count": entry.get("view_count"),
                    "thumbnail_url": f"https://i.ytimg.com/vi/{vid_id}/maxresdefault.jpg",
                    "thumbnail_fallback": f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg",
                    "source": "YouTube (yt-dlp)"
                })
    except Exception as e:
        sys.stderr.write(f"[!] yt-dlp search error: {e}\n")

    return results


def search_ddg_videos(
    query: str,
    limit: int = 5,
    resolution: Optional[str] = None,
    duration: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Search videos across the web via DuckDuckGo video index."""
    if not HAS_DDGS:
        return []

    results: List[Dict[str, Any]] = []
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with DDGS() as ddgs:
                raw_results = ddgs.videos(
                    keywords=query,
                    resolution=resolution,
                    duration=duration,
                    max_results=limit
                )
                for item in raw_results:
                    images = item.get("images", {})
                    thumb = images.get("large") or images.get("medium") or images.get("small") or ""
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("content", ""),
                        "channel": item.get("uploader", ""),
                        "duration_formatted": item.get("duration", ""),
                        "view_count": item.get("statistics", {}).get("viewCount"),
                        "thumbnail_url": thumb,
                        "embed_url": item.get("embed_url", ""),
                        "publisher": item.get("publisher", "Web"),
                        "source": "DuckDuckGo Videos"
                    })
    except Exception as e:
        sys.stderr.write(f"[!] DuckDuckGo video search error: {e}\n")

    return results


def search_videos(
    query: str,
    limit: int = 5,
    engine: str = "auto",
    duration: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Unified video search across YouTube and multi-platform aggregators."""
    if engine == "youtube":
        return search_youtube_ytdlp(query, limit=limit)
    elif engine == "ddg":
        return search_ddg_videos(query, limit=limit, duration=duration)

    results = search_youtube_ytdlp(query, limit=limit)
    if not results or len(results) < limit:
        ddg_res = search_ddg_videos(query, limit=limit, duration=duration)
        seen_urls = {r.get("url") for r in results}
        for dr in ddg_res:
            if dr.get("url") not in seen_urls:
                results.append(dr)
                seen_urls.add(dr.get("url"))

    return results[:limit]


# ==============================================================================
# 7. YouTube Transcript Intelligence
# ==============================================================================
def extract_video_id(url_or_id: str) -> str:
    """Extract YouTube video ID from full URL, short URL, or direct ID."""
    clean = url_or_id.strip()
    if "youtu.be/" in clean:
        return clean.split("youtu.be/")[1].split("?")[0].split("&")[0]
    if "watch?v=" in clean:
        parsed = urllib.parse.urlparse(clean)
        qs = urllib.parse.parse_qs(parsed.query)
        if "v" in qs:
            return qs["v"][0]
    return clean


def get_video_transcript(
    url_or_id: str,
    search_term: Optional[str] = None,
    languages: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Fetch and format complete YouTube video transcripts with timestamp navigation."""
    if not HAS_TRANSCRIPT_API:
        return {"error": "youtube-transcript-api library not available"}

    video_id = extract_video_id(url_or_id)

    try:
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id)
    except Exception as e:
        try:
            api = YouTubeTranscriptApi()
            transcript = api.fetch(video_id, languages=["en", "en-US", "en-GB", "fr", "es", "de"])
        except Exception as e2:
            return {"error": f"Could not retrieve transcript for video '{video_id}': {e2}"}

    formatted_snippets = []
    full_text_parts = []

    for item in transcript:
        text = getattr(item, "text", None) or (item.get("text") if isinstance(item, dict) else "")
        start = getattr(item, "start", None) or (item.get("start") if isinstance(item, dict) else 0.0)
        duration = getattr(item, "duration", None) or (item.get("duration") if isinstance(item, dict) else 0.0)

        clean_text = text.replace("\n", " ").strip()
        full_text_parts.append(clean_text)

        mins = int(start // 60)
        secs = int(start % 60)
        timestamp_str = f"{mins:02d}:{secs:02d}"

        include = True
        if search_term:
            if search_term.lower() not in clean_text.lower():
                include = False

        if include:
            formatted_snippets.append({
                "start_seconds": round(float(start), 2),
                "timestamp": timestamp_str,
                "duration": round(float(duration), 2),
                "text": clean_text
            })

    return {
        "video_id": video_id,
        "video_url": f"https://www.youtube.com/watch?v={video_id}",
        "total_snippets": len(transcript),
        "matched_snippets_count": len(formatted_snippets),
        "search_term": search_term,
        "snippets": formatted_snippets,
        "full_text": " ".join(full_text_parts) if not search_term else None
    }


# ==============================================================================
# 8. Asset Downloader & Verifier (Images, Video & Audio)
# ==============================================================================
def is_video_source(url_or_id: str) -> bool:
    """Detect if URL or ID corresponds to a video platform."""
    clean = url_or_id.strip()
    clean_l = clean.lower()
    if "youtube.com" in clean_l or "youtu.be" in clean_l or "vimeo.com" in clean_l:
        return True
    # YouTube 11-char ID check: base64url characters only, must NOT contain '.' or path separators
    if len(clean) == 11 and "." not in clean and "/" not in clean and "\\" not in clean:
        return bool(re.match(r"^[A-Za-z0-9_-]{11}$", clean))
    return False


def find_sentence_clip_window(
    url_or_id: str,
    search_phrase: str,
    pre_roll_sec: float = 0.8,
    post_roll_sec: float = 1.2
) -> Dict[str, Any]:
    """
    Locate a spoken phrase in a YouTube video's transcript and compute a clean,
    sentence-bounded clip window (with pre-roll and post-roll padding) so cuts
    never slice a speaker mid-sentence.
    """
    tr = get_video_transcript(url_or_id)
    snippets = tr.get("snippets", [])
    if not snippets:
        return {"status": "error", "error": tr.get("error", "No transcript snippets found")}

    needle = search_phrase.lower().strip()
    match_idx = -1
    for i, s in enumerate(snippets):
        if needle in s.get("text", "").lower():
            match_idx = i
            break

    if match_idx == -1:
        # Try matching across two consecutive snippets
        for i in range(len(snippets) - 1):
            combined = f"{snippets[i].get('text', '')} {snippets[i+1].get('text', '')}".lower()
            if needle in combined:
                match_idx = i
                break

    if match_idx == -1:
        return {"status": "error", "error": f"Phrase '{search_phrase}' not found in transcript"}

    # Expand backward if previous snippet ends < 0.25s before current and doesn't end with sentence punctuation
    start_idx = match_idx
    while start_idx > 0:
        prev = snippets[start_idx - 1]
        curr = snippets[start_idx]
        gap = curr["start_seconds"] - (prev["start_seconds"] + prev["duration"])
        prev_text = prev.get("text", "").strip()
        if gap < 0.25 and not prev_text.endswith((".", "!", "?", "]")) and (curr["start_seconds"] - snippets[match_idx]["start_seconds"]) > -6.0:
            start_idx -= 1
            break
        break

    # Expand forward by 1 snippet if current snippet doesn't complete the clause
    end_idx = min(len(snippets) - 1, match_idx + 1)
    raw_start = max(0.0, snippets[start_idx]["start_seconds"] - pre_roll_sec)
    raw_end = snippets[end_idx]["start_seconds"] + snippets[end_idx]["duration"] + post_roll_sec

    def _fmt(sec: float) -> str:
        m = int(sec // 60)
        s = sec - (m * 60)
        return f"{m:02d}:{s:05.2f}"

    joined_text = " ".join(s.get("text", "") for s in snippets[start_idx:end_idx + 1])
    return {
        "status": "success",
        "video_id": extract_video_id(url_or_id),
        "sections_arg": f"{_fmt(raw_start)}-{_fmt(raw_end)}",
        "start_seconds": round(raw_start, 2),
        "end_seconds": round(raw_end, 2),
        "duration_seconds": round(raw_end - raw_start, 2),
        "spoken_text": joined_text
    }


def download_video_clip(
    url_or_id: str,
    dest_dir: str,
    filename: Optional[str] = None,
    thumbnail_only: bool = False,
    max_height: int = 720,
    sections: Optional[str] = None,
    strip_audio: bool = False,
    force_keyframes: bool = True
) -> Dict[str, Any]:
    """
    Download a video clip, section, or high-res thumbnail using yt-dlp.
    When `sections` is provided, `force_keyframes=True` forces frame-exact cutting
    at the requested timestamps (with pre/post-roll silence padding) rather than
    snapping to coarse 5-second GOP keyframes that cut speakers mid-sentence.
    """
    if not HAS_YTDLP:
        return {"status": "error", "error": "yt-dlp library is not available"}

    os.makedirs(dest_dir, exist_ok=True)
    video_url = url_or_id if ("http://" in url_or_id or "https://" in url_or_id) else f"https://www.youtube.com/watch?v={url_or_id}"

    if thumbnail_only:
        vid_id = extract_video_id(url_or_id)
        thumb_url = f"https://i.ytimg.com/vi/{vid_id}/maxresdefault.jpg"
        out_name = filename or f"{vid_id}_thumb.jpg"
        return download_image_file(thumb_url, dest_dir, out_name)

    outtmpl = os.path.join(dest_dir, filename if filename else "%(title)s [%(id)s].%(ext)s")
    ydl_opts = {
        "outtmpl": outtmpl,
        "format": f"bestvideo[height<={max_height}][ext=mp4]+bestaudio[ext=m4a]/best[height<={max_height}][ext=mp4]/best",
        "quiet": False,
        "no_warnings": True,
        "merge_output_format": "mp4",
        "overwrites": True,
    }
    if sections:
        def _parse_time_val(t_val: str) -> float:
            parts = t_val.strip().split(":")
            if len(parts) == 3:
                return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
            elif len(parts) == 2:
                return float(parts[0]) * 60 + float(parts[1])
            return float(t_val.strip())

        parsed_ranges = []
        for s_chunk in sections.split(","):
            s_clean = s_chunk.strip().lstrip("*")
            if "-" in s_clean:
                s_start, s_end = s_clean.split("-", 1)
                try:
                    parsed_ranges.append((_parse_time_val(s_start.lstrip("*")), _parse_time_val(s_end.lstrip("*"))))
                except Exception:
                    pass
        if not parsed_ranges:
            return {"status": "error", "error": f"Invalid section range specification '{sections}'", "source_url": video_url}
        ydl_opts["download_ranges"] = yt_dlp.utils.download_range_func(None, parsed_ranges)
        if force_keyframes:
            ydl_opts["force_keyframes_at_cuts"] = True

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            meta = ydl.extract_info(video_url, download=True)
            saved_filename = ydl.prepare_filename(meta)
            if not os.path.exists(saved_filename):
                base, _ = os.path.splitext(saved_filename)
                if os.path.exists(f"{base}.mp4"):
                    saved_filename = f"{base}.mp4"

            file_size = os.path.getsize(saved_filename) if os.path.exists(saved_filename) else 0

            # Optional YouTube ContentID Protection: Strip sync studio audio to eliminate acoustic fingerprinting
            if strip_audio and os.path.exists(saved_filename) and not thumbnail_only:
                p = Path(saved_filename)
                temp_stripped = str(p.parent / f"{p.stem}_stripped{p.suffix}")
                try:
                    strip_cmd = ["ffmpeg", "-y", "-i", saved_filename, "-an", "-c:v", "copy", temp_stripped]
                    s_res = subprocess.run(strip_cmd, capture_output=True, timeout=60)
                    if s_res.returncode == 0 and os.path.exists(temp_stripped):
                        # Verify zero audio streams via ffprobe
                        probe_cmd = ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=codec_name", "-of", "csv=p=0", temp_stripped]
                        probe_res = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=15)
                        if probe_res.returncode == 0 and probe_res.stdout.strip() == "":
                            os.replace(temp_stripped, saved_filename)
                            file_size = os.path.getsize(saved_filename)
                        else:
                            if os.path.exists(temp_stripped):
                                os.remove(temp_stripped)
                            if os.path.exists(saved_filename):
                                os.remove(saved_filename)
                            err_msg = "FFprobe returned non-zero exit code during verification" if probe_res.returncode != 0 else "FFprobe detected residual audio stream"
                            return {"status": "error", "error": f"{err_msg}; aborted to prevent ContentID flag.", "source_url": video_url}
                    else:
                        if os.path.exists(saved_filename):
                            os.remove(saved_filename)
                        return {"status": "error", "error": f"Audio stripping FFmpeg command failed: {s_res.stderr.decode('utf-8', errors='ignore')}", "source_url": video_url}
                except Exception as strip_err:
                    if os.path.exists(saved_filename):
                        os.remove(saved_filename)
                    return {"status": "error", "error": f"Audio stripping exception: {strip_err}", "source_url": video_url}

            return {
                "status": "success",
                "media_type": "video",
                "file_path": os.path.abspath(saved_filename),
                "file_name": os.path.basename(saved_filename),
                "file_size_bytes": file_size,
                "title": meta.get("title"),
                "duration_seconds": meta.get("duration"),
                "resolution": f"{meta.get('width')}x{meta.get('height')}" if meta.get("width") else None,
                "source_url": video_url
            }
    except Exception as e:
        return {"status": "error", "error": str(e), "source_url": video_url}


def _resolve_wikimedia_thumb_url(url: str, width: int = 1920) -> Optional[str]:
    """Resolve a Wikimedia Commons original URL to its rate-limit-exempt 1920px CDN thumburl."""
    if "wikimedia.org" not in url:
        return None
    try:
        parsed_path = urllib.parse.unquote(urllib.parse.urlparse(url).path)
        fname = os.path.basename(parsed_path)
        if fname.startswith("File:"):
            fname = fname[5:]
        api_url = "https://commons.wikimedia.org/w/api.php"
        params = {
            "action": "query",
            "titles": f"File:{fname}",
            "prop": "imageinfo",
            "iiprop": "url|size",
            "iiurlwidth": width,
            "format": "json"
        }
        bot_headers = {"User-Agent": "VideoPipelineMediaBot/2.5 (https://github.com/antigravity/pipeline; media@antigravity.dev)"}
        r = requests.get(api_url, params=params, headers=bot_headers, timeout=10)
        if r.status_code == 200:
            pages = r.json().get("query", {}).get("pages", {})
            for p in pages.values():
                ii = p.get("imageinfo", [{}])[0]
                if ii.get("thumburl"):
                    return ii["thumburl"]
                if ii.get("url"):
                    return ii["url"]
    except Exception:
        pass
    return None


def download_image_file(url: str, dest_dir: str, filename: Optional[str] = None) -> Dict[str, Any]:
    """Download and verify an image file safely with Wikimedia 1920px CDN resolution and strict PIL validation."""
    os.makedirs(dest_dir, exist_ok=True)
    bot_ua = "VideoPipelineMediaBot/2.5 (https://github.com/antigravity/pipeline; media@antigravity.dev)"
    headers = {"User-Agent": bot_ua}

    if not filename:
        parsed_path = urllib.parse.urlparse(url).path
        base = os.path.basename(parsed_path)
        if not base or "." not in base:
            filename = f"media_{int(time.time())}.jpg"
        else:
            filename = base

    filepath = os.path.join(dest_dir, filename)
    candidate_urls = [url]
    if "upload.wikimedia.org" in url or "commons.wikimedia.org" in url:
        thumb_u = _resolve_wikimedia_thumb_url(url, width=1920)
        if thumb_u and thumb_u not in candidate_urls:
            candidate_urls.insert(0, thumb_u)

    width, height, img_format = None, None, None
    last_error = None

    for cand_url in candidate_urls:
        try:
            resp = requests.get(cand_url, headers=headers, stream=True, timeout=20)
            if resp.status_code == 200:
                with open(filepath, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=16384):
                        if chunk:
                            f.write(chunk)
                if os.path.exists(filepath) and os.path.getsize(filepath) > 200:
                    with Image.open(filepath) as img:
                        img.verify()
                    with Image.open(filepath) as img2:
                        width, height = img2.size
                        img_format = img2.format
                    if width and height:
                        last_error = None
                        break
            else:
                last_error = f"HTTP {resp.status_code}"
        except Exception as e:
            last_error = str(e)
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except Exception:
                    pass

    if not width or not height or not os.path.exists(filepath):
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass
        return {"status": "error", "error": f"Invalid or rate-limited image ({last_error})", "source_url": url}

    file_size = os.path.getsize(filepath)
    return {
        "status": "success",
        "media_type": "file",
        "file_path": os.path.abspath(filepath),
        "file_name": filename,
        "file_size_bytes": file_size,
        "width": width,
        "height": height,
        "format": img_format,
        "source_url": url
    }


def conform_and_upscale_image(
    input_path: str,
    output_path: str,
    target_w: int = 1920,
    target_h: int = 1080
) -> Dict[str, Any]:
    """
    Conform and upscale an image to 1920x1080 broadcast raster using FFmpeg Lanczos
    interpolation + unsharp mask sharpening + blurred background fill (zero black bars).
    Especially sharpens lower-resolution archival scans (<1080p).
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    vf_filter = (
        f"split=2[bg][fg];"
        f"[bg]scale={target_w}:{target_h}:force_original_aspect_ratio=increase:flags=lanczos,"
        f"crop={target_w}:{target_h},boxblur=25:5,eq=brightness=-0.18:saturation=0.85[bg_b];"
        f"[fg]scale={target_w}:{target_h}:force_original_aspect_ratio=decrease:flags=lanczos,"
        f"unsharp=5:5:0.85:5:5:0.0[fg_s];"
        f"[bg_b][fg_s]overlay=(W-w)/2:(H-h)/2"
    )
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-vf", vf_filter,
        "-frames:v", "1",
        output_path
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, timeout=45)
        if res.returncode == 0 and os.path.exists(output_path):
            return {
                "status": "success",
                "output_path": os.path.abspath(output_path),
                "width": target_w,
                "height": target_h,
                "size_bytes": os.path.getsize(output_path)
            }
        return {"status": "error", "error": res.stderr.decode("utf-8", errors="ignore")}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def download_asset(
    url_or_id: str,
    dest_dir: str,
    filename: Optional[str] = None,
    thumbnail_only: bool = False,
    max_height: int = 720,
    sections: Optional[str] = None,
    strip_audio: bool = False
) -> Dict[str, Any]:
    """Unified downloader routing between video platforms and direct files."""
    if is_video_source(url_or_id):
        return download_video_clip(url_or_id, dest_dir, filename, thumbnail_only=thumbnail_only, max_height=max_height, sections=sections, strip_audio=strip_audio)
    else:
        return download_image_file(url_or_id, dest_dir, filename)



# ==============================================================================
# 9. YouTube Copyright & ContentID Risk Engine
# ==============================================================================
def assess_copyright_risk(
    title: str,
    url: str,
    source: str,
    media_type: str = "image",
    license_hint: str = "",
    audio_present: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Evaluate YouTube ContentID and copyright risk tier for documentary media.
    Tiers:
    - Tier 1: Safe / Zero Risk (archival stills, Wikimedia, NASA, IA public domain, Pexels/Pixabay CC0)
    - Tier 2: Low Risk / Fair Use (archival interviews, news broadcasts, trailers with audio stripped)
    - Tier 3: High Risk (studio feature film scene rips, commercial music/soundtracks)
    """
    clean_title = (title or "").lower()
    clean_source = (source or "").lower()
    clean_url = (url or "").lower()

    if media_type == "image":
        clean_hint = (license_hint or "").lower().strip()
        
        # 1. Non-Commercial (NC) restrictions: High Risk for monetized distribution
        if any(x in clean_hint for x in ["-nc", " nc", "non-commercial", "noncommercial", "non commercial"]):
            return {
                "risk_tier": "Tier 3 (High Risk / Non-Commercial Restriction)",
                "safety_score": 30,
                "content_id_flag": False,
                "fair_use_notes": "NonCommercial (NC) clause strictly prohibits monetized YouTube distribution. Puts channel ad revenue at direct risk of copyright strike.",
                "recommended_action": "DO NOT USE on monetized channels. Replace with commercial CC BY or public domain asset."
            }

        # 2. No-Derivatives (ND) restrictions: High Risk for editing/cropping
        if any(x in clean_hint for x in ["-nd", " nd", "no-derivatives", "noderivatives", "no derivatives"]):
            return {
                "risk_tier": "Tier 3 (High Risk / No-Derivatives Restriction)",
                "safety_score": 35,
                "content_id_flag": False,
                "fair_use_notes": "NoDerivatives (ND) clause prohibits cropping, pan-and-scan, or integration into a video timeline.",
                "recommended_action": "DO NOT USE. Video adaptations and conformed crops violate ND licensing terms."
            }

        # 3. Explicit Copyright / All Rights Reserved / GFDL / Not Public Domain: Fail closed
        if any(x in clean_hint for x in ["all rights reserved", "copyrighted", "not public domain", "not pd", "gfdl"]):
            return {
                "risk_tier": "Tier 3 (High Risk / All Rights Reserved or Incompatible License)",
                "safety_score": 20,
                "content_id_flag": False,
                "fair_use_notes": "Media is explicitly copyrighted, unfree, or incompatible (GFDL / All Rights Reserved).",
                "recommended_action": "Replace with verified public domain or CC BY asset, or establish explicit Fair Use clearance."
            }

        # 4. Verified Public Domain
        pd_patterns = [r"\bpublic domain\b", r"\bpd\b", r"\bpd-us\b", r"\bcc0\b", r"\bus gov\b", r"\bus_gov\b", r"\bno copyright\b"]
        is_pd = any(re.search(pat, clean_hint) or re.search(pat, clean_source) for pat in pd_patterns)
        if is_pd:
            return {
                "risk_tier": "Tier 1 (Safe / Public Domain)",
                "safety_score": 100,
                "content_id_flag": False,
                "fair_use_notes": "Public domain still image (US government work, CC0, or verified expired copyright). Zero copyright restrictions or ContentID fingerprint matching.",
                "recommended_action": "Use directly in 03_media/raw, conform and upscale to 1080p in 03_media/conformed."
            }

        # 5. CC BY-SA (ShareAlike)
        is_cc_by_sa = bool(re.search(r"\bcc[- ]by[- ]sa(\b|[- ]\d)", clean_hint) or re.search(r"\bshare[- ]?alike\b", clean_hint) or re.search(r"\bcc[- ]by[- ]sa\b", clean_source))
        if is_cc_by_sa:
            return {
                "risk_tier": "Tier 1 (Safe / Creative Commons ShareAlike with Attribution)",
                "safety_score": 85,
                "content_id_flag": False,
                "fair_use_notes": "Creative Commons ShareAlike (CC BY-SA) still image. Commercial use permitted with mandatory author attribution; adapted crops must carry compatible CC BY-SA license.",
                "recommended_action": "Record author and license in asset_registry.json; display attribution in credits and apply CC BY-SA to adapted crop."
            }

        # 6. CC BY (Attribution only, versioned)
        is_cc_by = bool(re.search(r"\bcc[- ]by(\b|[- ]\d)", clean_hint) or re.search(r"\bcreative commons attribution\b", clean_hint) or "geograph" in clean_source)
        if is_cc_by:
            return {
                "risk_tier": "Tier 1 (Safe / Creative Commons with Attribution)",
                "safety_score": 90,
                "content_id_flag": False,
                "fair_use_notes": "Creative Commons Attribution (CC BY) still image. Commercial use permitted with mandatory author attribution in video credits.",
                "recommended_action": "Record author and license in asset_registry.json; display attribution in credits."
            }

        # 7. Pre-1978 notice check
        if "pre1978" in clean_hint or "pre-1978" in clean_hint:
            return {
                "risk_tier": "Tier 2 (Requires Notice / Renewal Verification)",
                "safety_score": 70,
                "content_id_flag": False,
                "fair_use_notes": "Pre-1978 media requires verification of copyright notice omission or non-renewal before treating as definitive public domain.",
                "recommended_action": "Verify absence of copyright notice on original publication or search US Copyright Office renewal records."
            }

        # 8. Unrecognized / Ambiguous: Fail closed
        return {
            "risk_tier": "Tier 2 (Unverified License / Manual Check Required)",
            "safety_score": 50,
            "content_id_flag": False,
            "fair_use_notes": "License terms could not be definitively validated as public domain or commercial Creative Commons. Fails closed.",
            "recommended_action": "Inspect asset page and verify commercial distribution rights prior to conformed pipeline use."
        }

    # Video checks: Use boundary regex so 'ost' does not match 'Peter Ostrum' or 'most'
    high_risk_patterns = [
        r"\bfull movie\b", r"\bfull scene\b", r"\bclip\b", r"\bsoundtrack\b",
        r"\bost\b", r"\btheme song\b", r"\bofficial clip\b", r"\bwarner bros\b",
        r"\bparamount\b", r"\bdisney\b", r"\buniversal pictures\b"
    ]
    is_feature_film_clip = any(re.search(pat, clean_title) for pat in high_risk_patterns) and not ("interview" in clean_title or "trailer" in clean_title)

    if "pexels" in clean_source or "pixabay" in clean_source or "nasa" in clean_source:
        return {
            "risk_tier": "Tier 1 (Safe / Zero Risk)",
            "safety_score": 95,
            "content_id_flag": False,
            "fair_use_notes": "Royalty-free commercial / public domain stock B-roll. Cleared for monetized YouTube distribution.",
            "recommended_action": "Download to 03_media/raw, conform to 1080p30 in 03_media/conformed."
        }

    if "internet archive" in clean_source or "prelinger" in clean_title:
        return {
            "risk_tier": "Tier 1 (Safe / Public Domain)",
            "safety_score": 90,
            "content_id_flag": False,
            "fair_use_notes": "Public domain historical archive / vintage newsreel. Cleared for documentary distribution.",
            "recommended_action": "Download to 03_media/raw, verify pre-1978 provenance."
        }

    if is_feature_film_clip:
        return {
            "risk_tier": "Tier 3 (High Risk / ContentID Trigger)",
            "safety_score": 25,
            "content_id_flag": True,
            "fair_use_notes": "Feature film footage is aggressively fingerprinted by studio ContentID bots (audio & video). High probability of automated claim or blocked video.",
            "recommended_action": "REPLACE with high-res archival stills (Tier 1) + Ken Burns OR short promotional trailer clip (<5s) with sync studio audio completely stripped."
        }

    # Archival TV, interviews, trailers, talk shows
    return {
        "risk_tier": "Tier 2 (Low Risk / Fair Use Editorial)",
        "safety_score": 75,
        "content_id_flag": False,
        "fair_use_notes": "Archival broadcast/interview footage used for factual historical commentary under US Fair Use (17 U.S.C. § 107). Preserve interview speech audio by default; cut cleanly on sentence boundaries.",
        "recommended_action": "Download to 03_media/raw with sentence-bounded --sections, conform to 1080p30 in 03_media/conformed."
    }


def compute_sha256(filepath: str) -> str:
    """Compute deterministic SHA-256 hash of a media file."""
    h = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""


# ==============================================================================
# 10. Pipeline Media Ingestion & Asset Registry Engine
# ==============================================================================
def ingest_media_plan(
    plan_file_or_data: Any,
    project_dir: str,
    strip_video_audio: bool = False,
    unified_dir_name: str = "03_media"
) -> Dict[str, Any]:
    """
    Ingest a list of media assets (both images and videos) into the unified pipeline
    media folder hierarchy:
    - Raw Media (Images & Videos) -> <project_dir>/03_media/raw/SHOT_{XX}_{MMSS-MMSS}_{A1|A2|A3}_{slug}.{png|mp4}
    - Conformed 1080p Media       -> <project_dir>/03_media/conformed/SHOT_{XX}_{MMSS-MMSS}_{A1|A2|A3}_{slug}.{png|mp4}
    Preserves original audio on video clips by default, upscales/conforms images via
    FFmpeg Lanczos + unsharp mask, computes SHA-256 hashes, and writes asset_registry.json.
    """
    if isinstance(plan_file_or_data, str):
        with open(plan_file_or_data, "r", encoding="utf-8") as f:
            items = json.load(f)
    else:
        items = plan_file_or_data

    raw_dir = os.path.join(project_dir, unified_dir_name, "raw")
    conf_dir = os.path.join(project_dir, unified_dir_name, "conformed")
    registry_file = os.path.join(project_dir, unified_dir_name, "asset_registry.json")
    root_registry_file = os.path.join(project_dir, "asset_registry.json")

    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(conf_dir, exist_ok=True)

    existing_registry = {}
    is_schema_v1 = False
    old_root_meta = {}
    for candidate_reg in [registry_file, root_registry_file]:
        if os.path.exists(candidate_reg):
            try:
                with open(candidate_reg, "r", encoding="utf-8") as rf:
                    reg_data = json.load(rf)
                    if isinstance(reg_data, dict) and reg_data.get("schema_version") in ("1.0", "2.0"):
                        is_schema_v1 = True
                        old_root_meta = reg_data
                    assets_list = reg_data.get("assets", []) if isinstance(reg_data, dict) else reg_data
                    for a in assets_list:
                        k = a.get("asset_id") or a.get("shot_id")
                        if k:
                            existing_registry[k] = a
                break
            except Exception:
                pass

    ingested = []
    for item in items:
        shot_id = item.get("shot_id", f"SHOT_{int(time.time()*1000)%100000:05d}")
        ts = item.get("timestamp") or item.get("timestamp_range") or ""
        alt = item.get("alt") or item.get("alternative") or ""
        media_type = item.get("media_type", "image").lower()
        url = item.get("url") or item.get("image_url") or item.get("direct_video_url") or item.get("source_url")
        slug = item.get("slug") or item.get("title", "asset").replace(" ", "_")[:30]
        slug = "".join(c for c in slug if c.isalnum() or c in ("_", "-"))

        if not url:
            continue

        ext = ".png" if media_type == "image" else ".mp4"
        name_parts = [shot_id]
        if ts:
            name_parts.append(ts)
        if alt:
            name_parts.append(alt)
        name_parts.append(slug)
        out_name = "_".join(name_parts) + ext

        target_path = os.path.join(raw_dir, out_name)
        conf_path = os.path.join(conf_dir, out_name)

        dl_res = {}
        if not os.path.exists(target_path) or os.path.getsize(target_path) < 1000:
            if media_type == "image":
                dl_res = download_image_file(url, raw_dir, out_name)
                if dl_res.get("status") == "success":
                    conform_and_upscale_image(target_path, conf_path, 1920, 1080)
            else:
                dl_res = download_video_clip(
                    url,
                    raw_dir,
                    filename=out_name,
                    sections=item.get("sections"),
                    strip_audio=strip_video_audio,
                    force_keyframes=True
                )
                if dl_res.get("status") == "success":
                    cmd_v = [
                        "ffmpeg", "-y", "-i", target_path,
                        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease:flags=lanczos,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p",
                        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
                        *(["-an"] if strip_video_audio else ["-c:a", "aac", "-b:a", "192k", "-ar", "48000"]),
                        conf_path
                    ]
                    subprocess.run(cmd_v, capture_output=True, timeout=90)
        else:
            dl_res = {
                "status": "success",
                "file_path": target_path,
                "file_size_bytes": os.path.getsize(target_path)
            }

        if dl_res.get("status") == "success" and os.path.exists(target_path):
            file_sha = compute_sha256(target_path)
            conf_sha = compute_sha256(conf_path) if os.path.exists(conf_path) else ""
            risk = assess_copyright_risk(
                title=item.get("title", slug),
                url=url,
                source=item.get("source", "Web"),
                media_type=media_type,
                license_hint=item.get("license") or item.get("license_hint") or ""
            )

            asset_key = f"{shot_id}_{ts}_{alt}".strip("_") if (ts or alt) else shot_id
            registry_entry = {
                "asset_id": asset_key,
                "shot_id": shot_id,
                "timestamp_range": ts,
                "alternative": alt,
                "title": item.get("title", slug),
                "script_beat": item.get("script_beat") or item.get("narration_quote") or "",
                "media_type": media_type,
                "raw_path": Path(target_path).relative_to(project_dir).as_posix(),
                "conformed_path": Path(conf_path).relative_to(project_dir).as_posix() if os.path.exists(conf_path) else "",
                "file_name": out_name,
                "file_size_bytes": os.path.getsize(target_path),
                "raw_sha256": file_sha,
                "conformed_sha256": conf_sha,
                "source_url": url,
                "source_platform": item.get("source", "Web"),
                "copyright_tier": risk.get("risk_tier"),
                "content_id_safe": not risk.get("content_id_flag", False),
                "fair_use_justification": risk.get("fair_use_notes"),
                "recommended_treatment": risk.get("recommended_action")
            }
            existing_registry[asset_key] = registry_entry
            ingested.append(registry_entry)

    # Save finalized asset registry in both 03_media/asset_registry.json and root asset_registry.json
    if is_schema_v1:
        old_root_meta["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        old_root_meta["total_assets"] = len(existing_registry)
        old_root_meta["assets"] = list(existing_registry.values())
        final_registry_payload = old_root_meta
    else:
        final_registry_payload = {
            "schema_version": "2.0",
            "project": Path(project_dir).name,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_assets": len(existing_registry),
            "assets": list(existing_registry.values())
        }
    for reg_dest in [registry_file, root_registry_file]:
        with open(reg_dest, "w", encoding="utf-8") as rf:
            json.dump(final_registry_payload, rf, indent=2, ensure_ascii=False)

    return {
        "status": "success",
        "ingested_count": len(ingested),
        "registry_file": os.path.abspath(registry_file),
        "assets": ingested
    }


# ==============================================================================
# CLI Entrypoint & Argument Dispatcher
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Unified Internet Media Research & Extraction Toolkit (Images, B-Roll, Archives, Audio, Reverse Video)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. Subcommand: images
    img_parser = subparsers.add_parser("images", help="Search high-resolution images (Wikimedia, DDG, Pixabay)")
    img_parser.add_argument("query", help="Keywords or description")
    img_parser.add_argument("--limit", type=int, default=8, help="Max results (default: 8)")
    img_parser.add_argument("--engine", choices=["auto", "ddg", "wikimedia", "pixabay"], default="auto")
    img_parser.add_argument("--size", choices=["Small", "Medium", "Large", "Wallpaper"], default=None)
    img_parser.add_argument("--type", choices=["photo", "clipart", "gif", "transparent", "line"], default=None)
    img_parser.add_argument("--layout", choices=["Square", "Tall", "Wide"], default=None)
    img_parser.add_argument("--download-dir", default=None, help="Directory to auto-download matches")
    img_parser.add_argument("--json", action="store_true", help="Output JSON")

    # 2. Subcommand: stock (B-Roll)
    stock_parser = subparsers.add_parser("stock", help="Search royalty-free stock footage & B-roll (Pexels, Pixabay)")
    stock_parser.add_argument("query", help="Keywords (e.g. 'aerial drone city night')")
    stock_parser.add_argument("--limit", type=int, default=6, help="Max results (default: 6)")
    stock_parser.add_argument("--orientation", choices=["landscape", "portrait", "square"], default=None)
    stock_parser.add_argument("--download-dir", default=None, help="Directory to auto-download matches")
    stock_parser.add_argument("--json", action="store_true", help="Output JSON")

    # 3. Subcommand: archive (Internet Archive + NASA)
    arch_parser = subparsers.add_parser("archive", help="Search public domain historical & scientific video (Internet Archive, NASA)")
    arch_parser.add_argument("query", help="Keywords (e.g. 'apollo 11 launch' or '1950s documentary')")
    arch_parser.add_argument("--limit", type=int, default=6, help="Max results (default: 6)")
    arch_parser.add_argument("--collection", choices=["all", "nasa", "internetarchive"], default="all")
    arch_parser.add_argument("--download-dir", default=None, help="Directory to auto-download matches")
    arch_parser.add_argument("--json", action="store_true", help="Output JSON")

    # 4. Subcommand: audio (SFX + Music)
    audio_parser = subparsers.add_parser("audio", help="Search sound effects and background audio (Freesound, Wikimedia Audio)")
    audio_parser.add_argument("query", help="Sound keywords (e.g. 'thunderstorm heavy rain' or 'laser beam')")
    audio_parser.add_argument("--limit", type=int, default=6, help="Max results (default: 6)")
    audio_parser.add_argument("--download-dir", default=None, help="Directory to auto-download matches")
    audio_parser.add_argument("--json", action="store_true", help="Output JSON")

    # 5. Subcommand: reverse (Keyframe Extraction & Visual OSINT)
    rev_parser = subparsers.add_parser("reverse", help="Extract video keyframes via FFmpeg and generate Yandex/Google Lens visual reverse links")
    rev_parser.add_argument("video", help="Local video file path or web video URL")
    rev_parser.add_argument("--dest", default="./keyframes", help="Output folder for keyframes")
    rev_parser.add_argument("--max-frames", type=int, default=5, help="Number of keyframes to extract (default: 5)")
    rev_parser.add_argument("--threshold", type=float, default=0.35, help="Scene detection threshold (default: 0.35)")
    rev_parser.add_argument("--json", action="store_true", help="Output JSON")

    # 6. Subcommand: videos (YouTube + Web)
    vid_parser = subparsers.add_parser("videos", help="Search YouTube and web videos via yt-dlp")
    vid_parser.add_argument("query", help="Keywords")
    vid_parser.add_argument("--limit", type=int, default=5, help="Max results")
    vid_parser.add_argument("--engine", choices=["auto", "youtube", "ddg"], default="auto")
    vid_parser.add_argument("--duration", choices=["short", "medium", "long"], default=None)
    vid_parser.add_argument("--json", action="store_true", help="Output JSON")

    # 7. Subcommand: transcript
    tr_parser = subparsers.add_parser("transcript", help="Extract verbatim YouTube transcripts with timestamps")
    tr_parser.add_argument("video", help="YouTube video URL or Video ID")
    tr_parser.add_argument("--search", default=None, help="Filter lines mentioning specific phrase")
    tr_parser.add_argument("--json", action="store_true", help="Output JSON")

    # 8. Subcommand: download
    dl_parser = subparsers.add_parser("download", help="Download an image, audio, or video file safely")
    dl_parser.add_argument("url", help="Direct URL or Video ID")
    dl_parser.add_argument("--dest", default=".", help="Target directory")
    dl_parser.add_argument("--filename", default=None, help="Custom filename")
    dl_parser.add_argument("--thumbnail-only", action="store_true", help="Download high-res video thumbnail only")
    dl_parser.add_argument("--max-height", type=int, default=720, help="Max video resolution height")
    dl_parser.add_argument("--sections", default=None, help="Download section e.g. '*00:10-00:30'")
    dl_parser.add_argument("--strip-audio", action="store_true", help="Strip audio to eliminate YouTube ContentID risk")
    dl_parser.add_argument("--json", action="store_true", help="Output JSON")

    # 9. Subcommand: ingest (Pipeline Media Ingestion & Asset Registry)
    ingest_parser = subparsers.add_parser("ingest", help="Ingest a media plan JSON into pipeline directories and generate asset_registry.json")
    ingest_parser.add_argument("plan", help="Path to media_plan.json or raw JSON string")
    ingest_parser.add_argument("--project-dir", required=True, help="Target video project directory (e.g. Videos-Scripts/NN_Slug)")
    ingest_parser.add_argument("--strip-audio", action="store_true", help="Strip audio on downloaded video clips (default: preserve audio)")
    ingest_parser.add_argument("--json", action="store_true", help="Output JSON")

    # 10. Subcommand: assess (Copyright & ContentID Risk Check)
    assess_parser = subparsers.add_parser("assess", help="Assess YouTube ContentID and copyright risk for an asset")
    assess_parser.add_argument("title", help="Asset title or film name")
    assess_parser.add_argument("--url", default="", help="Source URL")
    assess_parser.add_argument("--source", default="Web", help="Platform source (e.g. YouTube, Wikimedia, Pexels)")
    assess_parser.add_argument("--media-type", choices=["image", "video", "audio"], default="video", help="Media modality")
    assess_parser.add_argument("--license", default="", help="License hint or tag string (e.g. 'CC BY-SA 4.0', 'CC BY-NC', 'PD')")
    assess_parser.add_argument("--json", action="store_true", help="Output JSON")

    # 11. Subcommand: upscale-image
    up_parser = subparsers.add_parser("upscale-image", help="Upscale and conform an image to 1920x1080 using FFmpeg Lanczos + unsharp mask")
    up_parser.add_argument("input", help="Input image path")
    up_parser.add_argument("output", help="Output 1920x1080 image path")
    up_parser.add_argument("--width", type=int, default=1920)
    up_parser.add_argument("--height", type=int, default=1080)
    up_parser.add_argument("--json", action="store_true", help="Output JSON")

    # 12. Subcommand: sentence-window
    sw_parser = subparsers.add_parser("sentence-window", help="Find a sentence-bounded clip timestamp window from a YouTube transcript")
    sw_parser.add_argument("video", help="YouTube video URL or ID")
    sw_parser.add_argument("phrase", help="Spoken phrase to locate in transcript")
    sw_parser.add_argument("--pre-roll", type=float, default=0.8, help="Pre-roll padding in seconds (default: 0.8)")
    sw_parser.add_argument("--post-roll", type=float, default=1.2, help="Post-roll padding in seconds (default: 1.2)")
    sw_parser.add_argument("--json", action="store_true", help="Output JSON")

    args = parser.parse_args()

    if args.command == "images":
        results = search_images(
            query=args.query, limit=args.limit, engine=args.engine,
            size=args.size, type_image=args.type, layout=args.layout
        )
        if args.download_dir and results:
            for item in results:
                item["download_info"] = download_asset(item["image_url"], args.download_dir)
        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            print(f"\n[+] Image Results for '{args.query}' ({len(results)} found):\n")
            for idx, r in enumerate(results, 1):
                dims = f"{r.get('width')}x{r.get('height')}" if r.get("width") else "Dims unknown"
                print(f"[{idx}] {r.get('title')}\n    Direct URL: {r.get('image_url')}\n    Dimensions: {dims} | Source: {r.get('source')} | License: {r.get('license')}\n")

    elif args.command == "stock":
        results = search_stock_videos(query=args.query, limit=args.limit, orientation=args.orientation)
        if args.download_dir and results:
            for item in results:
                target_url = item.get("direct_video_url") or item.get("url")
                if target_url:
                    item["download_info"] = download_asset(target_url, args.download_dir)
        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            print(f"\n[+] Stock Video / B-Roll Results for '{args.query}' ({len(results)} found):\n")
            for idx, r in enumerate(results, 1):
                dims = f"{r.get('width')}x{r.get('height')}" if r.get("width") else "Dims unknown"
                dur = f"{r.get('duration_seconds')}s" if r.get("duration_seconds") else "Duration unknown"
                print(f"[{idx}] {r.get('title')}\n    Page URL:   {r.get('url')}\n    Direct MP4: {r.get('direct_video_url')}\n    Duration:   {dur} | Dims: {dims} | Source: {r.get('source')}\n")

    elif args.command == "archive":
        results = search_archive_media(query=args.query, limit=args.limit, collection=args.collection)
        if args.download_dir and results:
            for item in results:
                target_url = item.get("direct_video_url") or item.get("url")
                if target_url:
                    item["download_info"] = download_asset(target_url, args.download_dir)
        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            print(f"\n[+] Archival & Public Domain Video Results for '{args.query}' ({len(results)} found):\n")
            for idx, r in enumerate(results, 1):
                print(f"[{idx}] {r.get('title')}\n    Details:    {r.get('url')}\n    Direct MP4: {r.get('direct_video_url')}\n    Source:     {r.get('source')} | License: {r.get('license')}\n    Summary:    {r.get('description')}\n")

    elif args.command == "audio":
        results = search_audio_sfx(query=args.query, limit=args.limit)
        if args.download_dir and results:
            for item in results:
                target_url = item.get("audio_url")
                if target_url:
                    item["download_info"] = download_asset(target_url, args.download_dir)
        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            print(f"\n[+] Audio / SFX Results for '{args.query}' ({len(results)} found):\n")
            for idx, r in enumerate(results, 1):
                dur = f"{r.get('duration_seconds')}s" if r.get("duration_seconds") else ""
                print(f"[{idx}] {r.get('title')}\n    Audio URL:  {r.get('audio_url')}\n    Source:     {r.get('source')} | License: {r.get('license')} {dur}\n")

    elif args.command == "reverse":
        res = extract_video_keyframes(args.video, args.dest, max_frames=args.max_frames, threshold=args.threshold)
        if args.json:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            if res.get("status") == "success":
                print(f"\n[+] Keyframe Extraction Complete ({res.get('keyframes_extracted')} frames saved):\n")
                print(f"    Folder: {res.get('output_directory')}\n")
                for idx, kf in enumerate(res.get("keyframes", []), 1):
                    print(f"[{idx}] Frame: {kf.get('frame_file')}")
                    print(f"    Path:   {kf.get('absolute_path')}")
                    print(f"    Reverse Search: {kf.get('yandex_reverse_url')}")
                    print(f"    Instructions:   {kf.get('reverse_search_instructions')}\n")
            else:
                print(f"[!] Reverse extraction error: {res.get('error')}")
                sys.exit(1)

    elif args.command == "videos":
        results = search_videos(query=args.query, limit=args.limit, engine=args.engine, duration=args.duration)
        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            print(f"\n[+] Video Search Results for '{args.query}' ({len(results)} found):\n")
            for idx, r in enumerate(results, 1):
                dur = r.get("duration_formatted") or f"{r.get('duration_seconds')}s" or "Unknown"
                views = f"{r.get('view_count'):,}" if r.get("view_count") else "Unknown"
                print(f"[{idx}] {r.get('title')}\n    Video URL:  {r.get('url')}\n    Channel:    {r.get('channel')} | Duration: {dur} | Views: {views}\n    Thumbnail:  {r.get('thumbnail_url')}\n")

    elif args.command == "transcript":
        data = get_video_transcript(args.video, search_term=args.search)
        if args.json:
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            if "error" in data:
                print(f"[!] Error: {data['error']}")
                sys.exit(1)
            print(f"\n[+] YouTube Video Transcript: {data.get('video_url')}")
            print(f"    Total snippets: {data.get('total_snippets')} | Filter matches: {data.get('matched_snippets_count')}\n")
            for s in data.get("snippets", []):
                print(f"  [{s.get('timestamp')}] {s.get('text')}")
            print()

    elif args.command == "download":
        res = download_asset(
            args.url, args.dest, filename=args.filename,
            thumbnail_only=args.thumbnail_only, max_height=args.max_height,
            sections=args.sections, strip_audio=getattr(args, "strip_audio", False)
        )
        if args.json:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            if res.get("status") == "success":
                mtype = res.get("media_type", "asset")
                print(f"[+] Successfully downloaded {mtype}: {res.get('file_path')}")
                if mtype == "video":
                    print(f"    Title: {res.get('title')}\n    Duration: {res.get('duration_seconds')}s | Size: {res.get('file_size_bytes'):,} bytes")
                else:
                    dims = f"{res.get('width')}x{res.get('height')}" if res.get("width") else "Unknown"
                    print(f"    Size: {res.get('file_size_bytes'):,} bytes | Dims: {dims} | Format: {res.get('format')}")
            else:
                print(f"[!] Download failed: {res.get('error')}")
                sys.exit(1)

    elif args.command == "ingest":
        res = ingest_media_plan(
            args.plan,
            project_dir=args.project_dir,
            strip_video_audio=getattr(args, "strip_audio", False)
        )
        if args.json:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            print(f"[+] Successfully ingested {res.get('ingested_count')} assets into project.")
            print(f"    Asset Registry: {res.get('registry_file')}")
            for a in res.get("assets", []):
                print(f"    - [{a['shot_id']}] {a['file_name']} ({a['copyright_tier']})")

    elif args.command == "assess":
        res = assess_copyright_risk(
            title=args.title,
            url=args.url,
            source=args.source,
            media_type=args.media_type,
            license_hint=getattr(args, "license", "") or ""
        )
        if args.json:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            print(f"[*] Copyright & ContentID Risk Assessment for: {args.title}")
            print(f"    Tier: {res.get('risk_tier')}")
            print(f"    ContentID Safe: {'YES (No Claim Risk)' if not res.get('content_id_flag') else 'NO (HIGH RISK OF CLAIM)'}")
            print(f"    Notes: {res.get('fair_use_notes')}")
            print(f"    Action: {res.get('recommended_action')}")

    elif args.command == "upscale-image":
        res = conform_and_upscale_image(args.input, args.output, args.width, args.height)
        if args.json:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            print(f"[+] Conformed & upscaled image: {res}")

    elif args.command == "sentence-window":
        res = find_sentence_clip_window(args.video, args.phrase, args.pre_roll, args.post_roll)
        if args.json:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            if res.get("status") == "success":
                print(f"[+] Sentence-Bounded Clip Window for '{args.phrase}':")
                print(f"    --sections \"{res['sections_arg']}\" ({res['duration_seconds']}s)")
                print(f"    Spoken text: \"{res['spoken_text']}\"")
            else:
                print(f"[!] {res.get('error')}")
                sys.exit(1)


if __name__ == "__main__":
    main()

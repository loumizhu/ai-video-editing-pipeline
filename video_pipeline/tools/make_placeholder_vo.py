#!/usr/bin/env python3
"""make_placeholder_vo.py - Generates a 48kHz silent/scratch narration WAV placeholder.
Used when Voicebox is unavailable and owner will record narration later.
Matches Vcut A1 voice stem format: 48000 Hz, 16-bit PCM, mono (or stereo).
"""

import argparse
import json
import os
import struct
import sys
import wave

def create_silent_wav(output_path, duration_seconds, sample_rate=48000, channels=1):
    """Generates a standard PCM 16-bit silent WAV file using Python standard library."""
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        
    num_samples = int(duration_seconds * sample_rate)
    with wave.open(output_path, 'wb') as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)  # 16-bit PCM
        wav_file.setframerate(sample_rate)
        
        # Write frames in 1-second chunks of zeros
        chunk_size = sample_rate * channels
        zero_chunk = b'\x00' * (chunk_size * 2)
        remaining = num_samples * channels
        
        while remaining > 0:
            to_write = min(remaining, chunk_size)
            if to_write == chunk_size:
                wav_file.writeframes(zero_chunk)
            else:
                wav_file.writeframes(b'\x00' * (to_write * 2))
            remaining -= to_write

    print(f"Silent VO placeholder generated:")
    print(f"  Path: {output_path}")
    print(f"  Duration: {duration_seconds:.2f} s ({num_samples} samples)")
    print(f"  Sample Rate: {sample_rate} Hz, Channels: {channels} ({'mono' if channels==1 else 'stereo'}), 16-bit PCM")

def main():
    parser = argparse.ArgumentParser(description="Create silent VO placeholder WAV")
    parser.add_argument('--timing', help="Path to timing.json to read duration from")
    parser.add_argument('--duration', type=float, help="Explicit duration in seconds")
    parser.add_argument('--out', required=True, help="Output WAV path (e.g. 05_VoiceOver/take_01.wav)")
    parser.add_argument('--sample-rate', type=int, default=48000, help="Audio sample rate (default 48000 Hz)")
    parser.add_argument('--channels', type=int, default=1, choices=[1, 2], help="Channels: 1 for mono (default), 2 for stereo")
    args = parser.parse_args()

    duration = args.duration
    if duration is None:
        if args.timing and os.path.exists(args.timing):
            with open(args.timing, 'r', encoding='utf-8') as f:
                data = json.load(f)
                dur = data.get("total_duration_s") or data.get("total_duration_seconds")
                if dur is None and data.get("chapters"):
                    dur = data["chapters"][-1].get("end_s")
                duration = float(dur or 0.0)
        else:
            print("Error: must provide either --duration or existing --timing JSON file", file=sys.stderr)
            sys.exit(1)

    if duration <= 0.0:
        print(f"Error: invalid or zero duration ({duration} s)", file=sys.stderr)
        sys.exit(1)

    create_silent_wav(args.out, duration, sample_rate=args.sample_rate, channels=args.channels)

if __name__ == '__main__':
    main()

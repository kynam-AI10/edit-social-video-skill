#!/usr/bin/env python3
"""Check an exported MP4's streams, dimensions, duration, and long silences."""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def run(*args):
    return subprocess.run(args, capture_output=True, text=True, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--duration", type=float, help="Expected seconds")
    parser.add_argument("--tolerance", type=float, default=0.1)
    parser.add_argument("--orientation", choices=("portrait", "landscape", "square"))
    parser.add_argument("--max-silence", type=float, default=1.5)
    parser.add_argument("--silence-db", type=float, default=-38)
    args = parser.parse_args()

    if not args.file.is_file() or args.file.stat().st_size == 0:
        parser.error("MP4 file is missing or empty")
    try:
        probe = run("ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(args.file))
        info = json.loads(probe.stdout)
        streams = info["streams"]
        video = next((s for s in streams if s.get("codec_type") == "video"), None)
        audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
        duration = float(info["format"]["duration"])
        failures = []
        if video is None:
            failures.append("missing video stream")
        if audio is None:
            failures.append("missing audio stream")
        if args.duration is not None and abs(duration - args.duration) > args.tolerance:
            failures.append(f"duration {duration:.3f}s differs from {args.duration:.3f}s")
        if video is not None and args.orientation:
            width, height = int(video["width"]), int(video["height"])
            actual = "portrait" if height > width else "landscape" if width > height else "square"
            if actual != args.orientation:
                failures.append(f"orientation is {actual}, expected {args.orientation}")

        silences = []
        if audio is not None:
            scan = subprocess.run(
                ["ffmpeg", "-hide_banner", "-i", str(args.file), "-vn", "-af",
                 f"silencedetect=n={args.silence_db}dB:d={args.max_silence}", "-f", "null", "NUL" if sys.platform == "win32" else "/dev/null"],
                capture_output=True, text=True,
            )
            if scan.returncode != 0:
                failures.append("silence scan failed")
            else:
                starts = re.findall(r"silence_start: ([0-9.]+)", scan.stderr)
                ends = re.findall(r"silence_end: ([0-9.]+) \| silence_duration: ([0-9.]+)", scan.stderr)
                silences = [{"start": float(s), "end": float(e), "duration": float(d)} for s, (e, d) in zip(starts, ends)]
                if len(starts) > len(ends):
                    silences.append({"start": float(starts[-1]), "end": duration, "duration": duration - float(starts[-1])})
                if silences:
                    failures.append(f"{len(silences)} silence interval(s) exceed {args.max_silence}s; review whether intentional")

        result = {
            "ok": not failures,
            "file": str(args.file.resolve()),
            "duration": duration,
            "video": {"codec": video.get("codec_name"), "width": video.get("width"), "height": video.get("height")} if video else None,
            "audio": {"codec": audio.get("codec_name"), "channels": audio.get("channels")} if audio else None,
            "long_silences": silences,
            "findings": failures,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if not failures else 1
    except (FileNotFoundError, subprocess.CalledProcessError, ValueError, KeyError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

# Edit Social Video — Codex skill

A project-local Codex skill for creating a finished MP4 from either (1) a presenter plus screen recording or (2) multiple scenes. It uses restrained sans-serif text, preserves supplied speech, and does not require an editable CapCut project.

Place this folder at `<your-project>/.Codex/skills/edit-social-video/` and ask Codex to edit footage with `$edit-social-video`. Supply the source paths, target duration, orientation, and must-keep spoken sections. The skill plans cuts, previews the result, and exports MP4 after approval.

Check an exported video with Python 3 and FFmpeg/FFprobe:

```sh
python scripts/verify_mp4.py output.mp4 --duration 60 --orientation portrait
```

This repository contains no source footage or rendered output.

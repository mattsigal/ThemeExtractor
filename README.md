# Theme Extractor 🎵🎬

A professional-grade Windows desktop application to extract high-quality theme songs from media files (TV shows and movies) for use with the Jellyfin `xThemeSong` plugin.

## Features
- **🎨 Visual Identity**: Modern dark mode UI with 16:9 aspect ratio preservation.
- **⚙️ Advanced Extraction**: EBU R128 (-14 LUFS) normalization, customizable bitrates, and silent processing.
- **🚀 Smoooth Performance**: Background workers for non-blocking network scans and metadata lookups.
- **🔍 Auto-Detection**: Scans media files for "Intro", "Opening", "Theme", or "OP" chapters and auto-seeds trim points.
- **📦 Zero Config**: Automatically discovers FFmpeg/FFprobe in its own directory.
- **💎 Single File**: Distributed as a standalone Windows EXE.

## Installation
1. Download the latest `Theme Extractor.exe` from the [Releases](https://github.com/m-batchelor/ThemeExtractor/releases) page.
2. (Optional) Place `ffmpeg.exe` and `ffprobe.exe` in the same folder as the app for a portable experience.
3. Run the application.

## Usage
1. **Set Path**: Click **Settings** to point to your Jellyfin TV or Movie library.
2. **Select Media**: Choose a show/movie and a source file.
3. **Fine-tune**: If a theme chapter is found, it will be auto-selected. Use **Preview Segment** to verify or use navigation buttons to adjust.
4. **Extract**: Click **Extract Theme**. The app generates `theme.mp3` and `theme.json` in the item's folder.

## Build from Source
```bash
pip install -r requirements.txt
pyinstaller --onefile --windowed --icon=icon.ico --add-data "icon.ico;." --name="Theme Extractor" ThemeExtractor.py
```

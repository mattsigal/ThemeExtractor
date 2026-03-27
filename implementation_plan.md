# Implementation Plan - Theme Extractor

Create a Windows application (Python/PySide6) to extract theme songs from episode files for Jellyfin, compatible with the `xThemeSong` plugin.

## Proposed Changes

### [New] [ThemeExtractor.py](file:///C:/Users/matth/OneDrive%20-%20Simon%20Fraser%20University%20%281sfu%29/attn/DeveloperMode/antigravity/2026-03-26_Theme-Extractor/ThemeExtractor.py)

Create the main application file using PySide6.

- **UI Components**:
  - **Header**: Premium branded title ("Theme Extractor").
  - **File Browser**: Left sidebar or top section to browse `\\BrokenClouds\BlackLodge\Media\Shows`.
  - **Media Player**: Integrated preview using `QMediaPlayer` and `QVideoWidget`.
  - **Trim Controls**: Input fields/sliders for Start Time and End Time (HH:MM:SS.mmm).
  - **Action Buttons**: "Preview Segment", "Extract Theme", "Refresh Directory".
  - **Details Pane**: Show metadata from existing `theme.json` in selected folders.

- **Logic**:
  - **FFmpeg Integration**: Use `subprocess` to run `ffmpeg` for extraction:
    `ffmpeg -ss [start] -to [end] -i [input] -ab 192k -ar 44100 -vn theme.mp3`
  - **Metadata Generation**: Create `theme.json` with the following structure:

    ```json
    {
      "YouTubeId": null,
      "YouTubeUrl": null,
      "Title": "[Show Name] Theme",
      "Uploader": "Local Extractor",
      "DateAdded": "[Current ISO Timestamp]",
      "DateModified": "[Current ISO Timestamp]",
      "IsUserUploaded": true,
      "OriginalFileName": "[Source Filename]"
    }
    ```

  - **Directory Scanning**: Walk show directories to find `theme.mp3` and `theme.json` to display status (Length, bitrate, etc.).

### [New] [requirements.txt](file:///C:/Users/matth/OneDrive%20-%20Simon%20Fraser%20University%20%281sfu%29/attn/DeveloperMode/antigravity/2026-03-26_Theme-Extractor/requirements.txt)

Define dependencies:

- `PySide6`

## Verification Plan

### Automated Tests

- None planned due to GUI and external hardware/media dependencies.

### Manual Verification

1. **Launch App**: Run `python ThemeExtractor.py`.
2. **Browse Directory**: Verify that `\\BrokenClouds\BlackLodge\Media\Shows` (if reachable) or a fallback local directory is listed.
3. **Select Episode**: Select an `.mkv` file.
4. **Preview**: Set a start/end time and click "Preview". Verify audio plays for that segment.
5. **Extract**: Click "Extract Theme".
6. **Check Output**:
   1. Verify `theme.mp3` is created in the show root folder.
   2. Verify `theme.json` is created with correct metadata.
   3. Verify the app updates the directory view to show "Theme Extracted" status.

## Phase 4: Refined Settings & Metadata Overhaul
- **Settings Dialog**:
  - Add "Audio Bitrate" (input field, default 192).
  - Add "FFmpeg Path" (input + browse, default "ffmpeg").
- **Metadata Display**:
  - Implement a more structured information block for selected shows.
  - Calculate theme duration using `ffprobe`.
  - Format `DateAdded` into a human-friendly string (e.g., "March 26, 2026").
  - Dynamically display "Source" as a clickable YouTube link or local filename.
## Phase 9: GitHub & Final Release
- **UI Refinement**:
  - Add a "Preview Segment" button next to the Start/End time inputs using a `QHBoxLayout` and `QGridLayout`.
  - Logic: Parse `start_input`, set media position, and call `play()`.
- **Code Migration**:
  - Target: `C:\Users\matth\OneDrive - Simon Fraser University (1sfu)\attn\DeveloperMode\Scripts\ThemeExtractor`.
  - Move Python sources, icon, and requirements.
- **CI/CD Infrastructure**:
  - [NEW] `README.md`: Project overview, installation, and usage.
  - [NEW] `.github/workflows/release.yml`: Trigger on tag push. Build EXE with PyInstaller on Windows runner and upload to GitHub Releases.
- **Git Initialization**:
  - `git init`, `git add .`, `git commit -m "Initialize Theme Extractor v1.0.0"`.
  - `git tag v1.0.0`.

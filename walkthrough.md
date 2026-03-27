# Walkthrough - Theme Extractor (Prototype)

I've implemented a working prototype of the **Theme Extractor** application in the task directory.

## Location

- Path: [2026-03-26_Theme-Extractor](file:///C:/Users/matth/OneDrive%20-%20Simon%20Fraser%20University%20%281sfu%29/attn/DeveloperMode/antigravity/2026-03-26_Theme-Extractor/)
- Main Script: [ThemeExtractor.py](file:///C:/Users/matth/OneDrive%20-%20Simon%20Fraser%20University%20%281sfu%29/attn/DeveloperMode/antigravity/2026-03-26_Theme-Extractor/ThemeExtractor.py)

## Key Features

- **File Browsing**: Directly browses your show directory at `\\BrokenClouds\BlackLodge\Media\Shows`.
- **Season Folder Support**: Automatically finds episodes nested in `Season XX` folders.
- **Integrated Preview**: Uses PySide6's Multimedia module to play episode audio/video.
- **Advanced Playback Controls**:
  - **Skips**: Big skips (10s) and small skips (1s) forward and back.
  - **Play/Pause**: Dedicated button to control media.
  - **Marking**: **Mark Start** and **Mark End** buttons capture the *exact* current timestamp from the video player and fill the input fields for you.
- **Settings & Persistence**: Save your default Media Root path via the **Settings** button (gear icon). It persists between sessions in `settings.json`.
- **Strict 16:9 Video**: The video player now strictly maintains a 16:9 aspect ratio, centering itself within the available space without stretching or squishing.
- **Improved Show Dashboard**:
  - **Combined Status**: A single column shows theme availability (✓/✗) and the preview link.
  - **Preview Toggle**: Click **(preview)** to start, and click it again to stop.
  - **Auto-Stop**: Previews stop automatically when you switch shows.
- **Audio Normalization**: Automatically applies **loudness normalization** (-14 LUFS) to ensure your themes match the volume levels of YouTube and other streaming sources.
- **Visual Feedback**: The **Extract Theme** button turns green and updates its text to "Theme Extracted!" once the process is successful. It resets automatically if you select a new file or adjust your timestamps.
- **FFmpeg Extraction**: Captures high-quality 192kbps MP3 segments.
- **Metadata Management**: Automatically generates `theme.json` in the same folder as the MP3, following the `xThemeSong` structure.
- **Show Directory View**: Shows the status of your library (e.g., length, bitrate, source file) directly in the app.

## How to Test

1. **Ensure Dependencies**: The app requires `PySide6`. I've verified it's already installed on your system (v6.10.1).
2. **Run the App**:

   ```bash
   python "C:\Users\matth\OneDrive - Simon Fraser University (1sfu)\attn\DeveloperMode\antigravity\2026-03-26_Theme-Extractor\ThemeExtractor.py"
   ```

3. **Usage**:
  - Select a show from the left list.
  - Select an episode MKV.
  - Use the playback controls to find the theme.
  - Click **Mark Start** at the beginning and **Mark End** at the end of the theme.
- **Safety First**: Navigation and Marking buttons will now alert you if you forget to select an episode first, preventing accidental misfires.
- **Clean Interface**: Removed the redundant "Preview Segment" button to simplify the workflow.
- **Optimized Layout**: The "Show Name" column is now much wider, ensuring long titles are clearly visible.
- Click **Extract Theme** to generate the files.

## Next Steps

- Once you've verified the prototype's core functionality, we can:
  - Refine the UI for a more premium "AutoBubbler-like" aesthetic.
  - Set up the GitHub repository and CI/CD actions as discussed.

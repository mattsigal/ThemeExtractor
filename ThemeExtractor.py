import sys
import os
import json
import subprocess
import ctypes
import time
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QListWidget, QPushButton, 
                               QFileDialog, QSplitter, QFrame, QLineEdit, 
                               QFormLayout, QMessageBox, QStatusBar, QTreeWidget,
                               QTreeWidgetItem, QHeaderView, QSizePolicy, QDialog)
from PySide6.QtCore import Qt, QUrl, QSize, QPoint, QRect, QThread, Signal, QObject
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtGui import QFont, QIcon, QPalette, QColor, QDesktopServices

# Paths
TASK_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(TASK_DIR, "settings.json")
DEFAULT_PATH = r"\\BrokenClouds\BlackLodge\Media\Shows"

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_bin(name, settings):
    set_v = settings.get("ffmpeg_path", "ffmpeg")
    if os.path.isdir(set_v):
        f = os.path.join(set_v, f"{name}.exe" if os.name == 'nt' else name)
        if os.path.exists(f): return f
    elif os.path.isfile(set_v) and name in os.path.basename(set_v).lower(): return set_v
    app_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    app_f = os.path.join(app_dir, f"{name}.exe" if os.name == 'nt' else name)
    if os.path.exists(app_f): return app_f
    return name

def quiet_subprocess(args, timeout=None):
    si = None
    if os.name == 'nt':
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout, startupinfo=si)

class LoadWorker(QThread):
    finished = Signal(dict, str) # paths, metadata_html
    error = Signal(str)

    def __init__(self, show_path, settings):
        super().__init__()
        self.show_path = show_path; self.settings = settings

    def get_duration(self, fp):
        fc = get_bin("ffprobe", self.settings)
        try:
            res = quiet_subprocess([fc, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", fp], timeout=5)
            return float(res.stdout.strip()) if res.returncode == 0 else 0
        except: return 0

    def format_duration(self, s): m, sec = divmod(int(s), 60); return f"{m:02}:{sec:02}"

    def run(self):
        try:
            sp = self.show_path; paths = {}
            for root, dirs, files in os.walk(sp):
                for f in files:
                    if f.lower().endswith(('.mkv', '.mp4', '.avi', '.ts', '.m2ts', '.m4v')):
                        rel = os.path.relpath(os.path.join(root, f), sp); paths[rel] = os.path.join(root, f)
            jp, mp = os.path.join(sp, "theme.json"), os.path.join(sp, "theme.mp3")
            ex = os.path.exists(mp); status_color = '#28a745' if ex else '#CC0633'
            html = f"<b>Selected Media Status:</b> <span style='color: {status_color};'>{'theme.mp3 exists' if ex else 'theme.mp3 does not exist'}</span><br>"
            if ex and os.path.exists(jp):
                try:
                    with open(jp) as f: d = json.load(f)
                    ar = d.get('DateAdded', '')
                    try: ads = datetime.fromisoformat(ar.replace('Z', '+00:00')).strftime("%B %d, %Y")
                    except: ads = ar
                    ds = self.format_duration(self.get_duration(mp))
                    yt_u = d.get('YouTubeUrl') or (f"https://youtube.com/watch?v={d.get('YouTubeId')}" if d.get('YouTubeId') else None)
                    src = f"<a href='{yt_u}' style='color: #007acc;'>YouTube Link</a>" if yt_u else d.get('OriginalFileName', 'None')
                    html += f"Title: {d.get('Title','Unknown')}<br>Added: {ads}<br>Length: {ds}<br>Source: {src}"
                except: html += "<i>Error reading theme.json</i>"
            elif not ex: html += "<br><i>No theme metadata available. Select a file to extract one.</i>"
            self.finished.emit(paths, html)
        except Exception as e: self.error.emit(str(e))

class SettingsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings"); self.setFixedWidth(600)
        layout = QVBoxLayout(self); form = QFormLayout()
        self.path_input = QLineEdit(settings.get("path", DEFAULT_PATH))
        browse_path_btn = QPushButton("Browse"); browse_path_btn.clicked.connect(self.browse_path)
        path_layout = QHBoxLayout(); path_layout.addWidget(self.path_input); path_layout.addWidget(browse_path_btn)
        form.addRow("Default Media Path:", path_layout)
        self.bitrate_input = QLineEdit(str(settings.get("bitrate", 192)))
        form.addRow("Audio Bitrate (kbps):", self.bitrate_input)
        self.ffmpeg_input = QLineEdit(settings.get("ffmpeg_path", "ffmpeg"))
        browse_ffmpeg_btn = QPushButton("Browse"); browse_ffmpeg_btn.clicked.connect(self.browse_ffmpeg)
        ffmpeg_layout = QHBoxLayout(); ffmpeg_layout.addWidget(self.ffmpeg_input); ffmpeg_layout.addWidget(browse_ffmpeg_btn)
        form.addRow("FFmpeg Path:", ffmpeg_layout); layout.addLayout(form)
        btns = QHBoxLayout(); save_btn = QPushButton("Save"); save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel"); cancel_btn.clicked.connect(self.reject)
        btns.addWidget(save_btn); btns.addWidget(cancel_btn); layout.addLayout(btns)

    def browse_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Media Directory", self.path_input.text())
        if path: self.path_input.setText(path)

    def browse_ffmpeg(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select FFmpeg", "", "Executable (*.exe);;All Files (*)")
        if path: self.ffmpeg_input.setText(path)

    def get_settings(self):
        return {"path": self.path_input.text(), "bitrate": int(self.bitrate_input.text()) if self.bitrate_input.text().isdigit() else 192, "ffmpeg_path": self.ffmpeg_input.text()}

class VideoContainer(QFrame):
    def __init__(self, video_widget, parent=None):
        super().__init__(parent)
        self.video_widget = video_widget; self.video_widget.setParent(self)
        self.setObjectName("videoContainer"); self.setStyleSheet("background-color: black;")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def resizeEvent(self, event):
        w, h = self.width(), self.height()
        if w <= 0 or h <= 0: return
        if w / h > 16 / 9: tw, th = int(h * 16 / 9), h
        else: tw, th = w, int(w * 9 / 16)
        self.video_widget.setGeometry((w - tw) // 2, (h - th) // 2, tw, th)

class ThemeExtractor(QMainWindow):
    def __init__(self):
        super().__init__()
        try: ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('antigravity.themeextractor.v1')
        except: pass
        self.setWindowTitle("Theme Extractor"); self.resize(1550, 950)
        icon_path = resource_path("icon.ico")
        if os.path.exists(icon_path): self.setWindowIcon(QIcon(icon_path))
        self.settings = {"path": DEFAULT_PATH, "bitrate": 192, "ffmpeg_path": "ffmpeg"}; self.load_settings()
        self.episode_paths = {}; self.current_preview_path = None
        self.media_player = QMediaPlayer(); self.audio_output = QAudioOutput(); self.media_player.setAudioOutput(self.audio_output)
        self.theme_player = QMediaPlayer(); self.theme_audio = QAudioOutput(); self.theme_player.setAudioOutput(self.theme_audio)
        self.setup_ui(); self.apply_styles(); self.load_items(self.settings["path"])

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f: self.settings.update(json.load(f))
            except: pass

    def save_settings(self, settings):
        self.settings.update(settings)
        try:
            with open(SETTINGS_FILE, 'w') as f: json.dump(self.settings, f, indent=4)
        except: pass

    def open_settings(self):
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec():
            new_settings = dialog.get_settings(); self.save_settings(new_settings)
            self.path_display.setText(self.settings["path"]); self.load_items(self.settings["path"])

    def setup_ui(self):
        central_widget = QWidget(); self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget); main_layout.setContentsMargins(15, 10, 15, 10); main_layout.setSpacing(0)
        header_widget = QWidget(); header_widget.setFixedHeight(80); header_v = QVBoxLayout(header_widget); header_v.setContentsMargins(0, 0, 0, 5)
        header_top = QHBoxLayout(); header_lbl = QLabel("Theme Extractor"); header_lbl.setObjectName("header")
        header_lbl.setFont(QFont("Segoe UI", 24, QFont.Bold)); header_top.addWidget(header_lbl); header_top.addStretch()
        settings_btn = QPushButton("⚙ Settings"); settings_btn.setFixedWidth(120); settings_btn.clicked.connect(self.open_settings)
        header_top.addWidget(settings_btn); header_v.addLayout(header_top)
        path_panel = QHBoxLayout(); path_panel.addWidget(QLabel("<b>Media Root:</b>"))
        self.path_display = QLabel(self.settings["path"]); self.path_display.setStyleSheet("color: #888; font-family: Consolas; background: #222; padding: 2px 5px;")
        path_panel.addWidget(self.path_display, 1); header_v.addLayout(path_panel); main_layout.addWidget(header_widget)
        self.splitter = QSplitter(Qt.Horizontal)
        left_panel = QWidget(); left_panel.setMinimumWidth(600); left_v = QVBoxLayout(left_panel); left_v.setContentsMargins(0, 5, 10, 0)
        left_v.addWidget(QLabel("<b>Media Selection:</b>"))
        self.item_list = QTreeWidget(); self.item_list.setColumnCount(2); self.item_list.setHeaderLabels(["Name", "Theme Status"])
        self.item_list.header().setStretchLastSection(False); self.item_list.header().setSectionResizeMode(0, QHeaderView.Stretch); self.item_list.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.item_list.itemClicked.connect(self.on_item_selected); left_v.addWidget(self.item_list, 6)
        left_v.addWidget(QLabel("<b>Source Files:</b>"))
        self.source_list = QListWidget(); self.source_list.itemClicked.connect(self.on_source_selected)
        left_v.addWidget(self.source_list, 4); self.splitter.addWidget(left_panel)
        center_panel = QWidget(); center_v = QVBoxLayout(center_panel); center_v.setContentsMargins(10, 5, 0, 0)
        self.video_widget = QVideoWidget(); self.media_player.setVideoOutput(self.video_widget)
        self.video_container = VideoContainer(self.video_widget); center_v.addWidget(self.video_container, 20)
        play_h = QHBoxLayout()
        for t in ["<< 10s", "< 1s", "Play", "> 1s", ">> 10s"]:
            btn = QPushButton(t); btn.clicked.connect(lambda checked=False, tag=t: self.on_nav_btn_clicked(tag))
            if t == "Play": self.btn_play = btn
            play_h.addWidget(btn)
        center_v.addLayout(play_h)
        mark_h = QHBoxLayout(); self.btn_mark_start = QPushButton("Mark Start"); self.btn_mark_end = QPushButton("Mark End")
        self.btn_mark_start.clicked.connect(lambda: self.on_mark_clicked("start")); self.btn_mark_end.clicked.connect(lambda: self.on_mark_clicked("end"))
        mark_h.addWidget(self.btn_mark_start, 1); mark_h.addWidget(self.btn_mark_end, 1); center_v.addLayout(mark_h)
        
        # Updated Time Inputs with Preview Button
        time_grid = QHBoxLayout()
        form_frame = QFrame(); form_l = QFormLayout(form_frame); self.start_input = QLineEdit("00:00:00.000"); self.end_input = QLineEdit("00:00:50.000")
        form_l.addRow("Start Time:", self.start_input); form_l.addRow("End Time:", self.end_input); time_grid.addWidget(form_frame, 3)
        self.btn_preview_segment = QPushButton("Preview\nSegment")
        self.btn_preview_segment.setFixedWidth(120); self.btn_preview_segment.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.btn_preview_segment.clicked.connect(self.preview_segment)
        time_grid.addWidget(self.btn_preview_segment, 1); center_v.addLayout(time_grid)

        ext_h = QHBoxLayout(); self.extract_btn = QPushButton("Extract Theme"); self.extract_btn.clicked.connect(self.extract_theme); self.extract_btn.setEnabled(False); self.extract_btn.setFixedHeight(50); ext_h.addWidget(self.extract_btn, 1); center_v.addLayout(ext_h)
        meta_f = QFrame(); meta_f.setObjectName("statusFrame"); meta_v = QVBoxLayout(meta_f); self.metadata_display = QLabel("No item selected"); self.metadata_display.setWordWrap(True); self.metadata_display.setOpenExternalLinks(True)
        meta_v.addWidget(self.metadata_display); center_v.addWidget(meta_f); self.splitter.addWidget(center_panel); self.splitter.setStretchFactor(1, 1); main_layout.addWidget(self.splitter, 1); self.status_bar = QStatusBar(); self.setStatusBar(self.status_bar)

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #1a1a1b; color: #e0e0e0; }
            QLabel { color: #e0e0e0; }
            QLabel#header { color: #CC0633; }
            QTreeWidget, QListWidget { background-color: #252526; color: #d4d4d4; border: 1px solid #3e3e42; border-radius: 4px; padding: 2px; }
            QTreeWidget::item { padding: 4px; border-bottom: 1px solid #2d2d2d; }
            QTreeWidget::item:selected, QListWidget::item:selected { background-color: #37373d; }
            QLineEdit { background-color: #2d2d2d; color: #ffffff; border: 1px solid #3e3e42; border-radius: 4px; padding: 5px; }
            QPushButton { background-color: #333333; color: #aaaaaa; border: 1px solid #555555; border-radius: 4px; padding: 6px 12px; }
            QPushButton:hover { background-color: #444444; color: #ffffff; border: 1px solid #777777; }
            QPushButton:pressed { background-color: #CC0633; color: white; }
            QPushButton:disabled { color: #444444; border: 1px solid #333333; }
            QPushButton#previewBtn { color: #007acc; text-decoration: underline; background: transparent; border: none; padding: 0; }
            QSplitter::handle { background-color: #1a1a1b; width: 6px; }
            QFrame#statusFrame { background-color: #252526; border: 1px solid #3e3e42; border-radius: 4px; padding: 8px; min-height: 120px; }
            QHeaderView::section { background-color: #333333; color: #cccccc; padding: 4px; border: 1px solid #222222; }
        """)

    def load_items(self, path):
        self.item_list.clear()
        if not path or not os.path.exists(path): return
        try:
            items = sorted([d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))])
            for s in items:
                has = os.path.exists(os.path.join(path, s, "theme.mp3"))
                check = QLabel("✓" if has else "✗"); check.setStyleSheet(f"color: {'#28a745' if has else '#CC0633'}; font-weight: bold; font-size: 13pt;")
                sc = QWidget(); sl = QHBoxLayout(sc); sl.setContentsMargins(2,0,10,0); sl.setSpacing(5); sl.addWidget(check)
                if has:
                    pb = QPushButton("(preview)"); pb.setObjectName("previewBtn"); pb.setFlat(True); pb.setCursor(Qt.PointingHandCursor); pb.clicked.connect(lambda c=False, p=os.path.join(path, s): self.preview_existing_theme(p)); sl.addWidget(pb)
                sl.addStretch(); it = QTreeWidgetItem([s, ""]); self.item_list.addTopLevelItem(it); self.item_list.setItemWidget(it, 1, sc)
            self.item_list.header().resizeSection(1, 100)
        except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def preview_existing_theme(self, sp):
        tp = os.path.join(sp, "theme.mp3")
        if os.path.exists(tp):
            if self.current_preview_path == tp and self.theme_player.playbackState() == QMediaPlayer.PlayingState: self.theme_player.stop(); self.status_bar.showMessage("Stopped preview.")
            else: self.theme_player.stop(); self.theme_player.setSource(QUrl.fromLocalFile(tp)); self.theme_player.play(); self.current_preview_path = tp; self.status_bar.showMessage(f"Previewing Theme: {os.path.basename(sp)}")

    def preview_segment(self):
        ms = self.format_to_ms(self.start_input.text())
        if ms is not None:
            if not self.source_list.currentItem(): QMessageBox.warning(self, "No Source Selected", "Please select a file first."); return
            self.media_player.setPosition(ms); self.media_player.play(); self.btn_play.setText("Pause")

    def on_nav_btn_clicked(self, tag):
        if not self.source_list.currentItem(): QMessageBox.warning(self, "No Source Selected", "Please select a file first."); return
        if tag == "<< 10s": self.skip(-10000)
        elif tag == "< 1s": self.skip(-1000)
        elif tag == "Play": self.toggle_play()
        elif tag == "> 1s": self.skip(1000)
        elif tag == ">> 10s": self.skip(10000)

    def on_mark_clicked(self, type):
        if not self.source_list.currentItem(): QMessageBox.warning(self, "No Source Selected", "Please select a file first."); return
        if type == "start": self.mark_start()
        else: self.mark_end()

    def on_item_selected(self, it, col):
        if self.theme_player.playbackState() == QMediaPlayer.PlayingState: self.theme_player.stop()
        self.reset_extract_button(); sp = os.path.join(self.settings["path"], it.text(0)); self.status_bar.showMessage(f"Loading {it.text(0)}...")
        self.source_list.clear(); self.metadata_display.setText("Loading metadata..."); self.worker = LoadWorker(sp, self.settings); self.worker.finished.connect(self.on_load_finished); self.worker.error.connect(lambda e: self.status_bar.showMessage(f"Error: {e}")); self.worker.start()

    def on_load_finished(self, paths, html):
        self.episode_paths = paths; [self.source_list.addItem(rel) for rel in sorted(paths.keys())]; self.metadata_display.setText(html); self.status_bar.showMessage("Ready", 3000)

    def on_source_selected(self, it):
        self.reset_extract_button(); p = self.episode_paths.get(it.text())
        if p: self.media_player.setSource(QUrl.fromLocalFile(p)); self.extract_btn.setEnabled(True); self.detect_chapter(p)

    def detect_chapter(self, fp):
        fc = get_bin("ffprobe", self.settings)
        try:
            res = quiet_subprocess([fc, "-v", "error", "-show_chapters", "-print_format", "json", fp], timeout=5)
            if res.returncode == 0:
                data = json.loads(res.stdout); chaps = data.get("chapters", [])
                self.status_bar.showMessage(f"Scanned {len(chaps)} chapters...", 2000)
                for chap in chaps:
                    title = chap.get("tags", {}).get("title", "").lower()
                    if any(x in title for x in ["intro", "opening", "theme", "op", "prolog", "prologue", "chapter 2"]):
                        st, en = float(chap.get("start_time", 0)), float(chap.get("end_time", 0))
                        self.start_input.setText(self.sec_to_format(st)); self.end_input.setText(self.sec_to_format(en))
                        self.status_bar.showMessage(f"Auto-detected segment: {title}", 3000); return
                self.status_bar.showMessage(f"No theme chapter found in {len(chaps)} segments.", 4000)
            self.start_input.setText("00:00:00.000"); self.end_input.setText("00:00:50.000")
        except: self.start_input.setText("00:00:00.000"); self.end_input.setText("00:00:50.000")

    def sec_to_format(self, sec): 
        m, s = divmod(sec, 60); h, m = divmod(m, 60); return f"{int(h):02}:{int(m):02}:{s:06.3f}"
    def skip(self, ms): self.reset_extract_button(); self.media_player.setPosition(max(0, self.media_player.position() + ms))
    def toggle_play(self):
        if self.media_player.playbackState() == QMediaPlayer.PlayingState: self.media_player.pause(); self.btn_play.setText("Play")
        else: self.media_player.play(); self.btn_play.setText("Pause")
    def mark_start(self): self.reset_extract_button(); self.start_input.setText(self.ms_to_format(self.media_player.position()))
    def mark_end(self): self.reset_extract_button(); self.end_input.setText(self.ms_to_format(self.media_player.position()))
    def reset_extract_button(self): self.extract_btn.setText("Extract Theme"); self.extract_btn.setStyleSheet(""); self.extract_btn.setEnabled(True if self.source_list.currentItem() else False)
    def ms_to_format(self, ms): s = (ms / 1000) % 60; m, h = int((ms / 60000) % 60), int((ms / 3600000) % 24); return f"{h:02}:{m:02}:{s:06.3f}"
    def format_to_ms(self, ts):
        try: h, m, s = ts.split(':'); return int((int(h)*3600 + int(m)*60 + float(s))*1000)
        except: return None

    def extract_theme(self):
        it, et = self.item_list.currentItem(), self.source_list.currentItem()
        if not it or not et: return
        sp, ep = os.path.join(self.settings["path"], it.text(0)), self.episode_paths.get(et.text()); st, en = self.start_input.text(), self.end_input.text()
        fc = get_bin("ffmpeg", self.settings); br = str(self.settings.get("bitrate", 192)) + "k"; om, oj = os.path.join(sp, "theme.mp3"), os.path.join(sp, "theme.json")
        try:
            self.status_bar.showMessage("Extracting theme..."); self.extract_btn.setText("Extraction in Progress..."); self.extract_btn.setStyleSheet("background-color: #f1c40f; color: black; font-weight: bold;"); self.extract_btn.setEnabled(False); QApplication.processEvents()
            if quiet_subprocess([fc, '-y', '-ss', st, '-to', en, '-i', ep, '-af', 'loudnorm=I=-14:LRA=11:tp=-1', '-ab', br, '-ar', '44100', '-vn', om]).returncode != 0: raise Exception("FFmpeg failed")
            meta = {"YouTubeId": None, "YouTubeUrl": None, "Title": f"{it.text(0)} Theme", "Uploader": "Local Extractor", "DateAdded": datetime.now().isoformat()+"Z", "DateModified": datetime.now().isoformat()+"Z", "IsUserUploaded": True, "OriginalFileName": et.text()}
            with open(oj,'w') as f: json.dump(meta, f, indent=4)
            self.status_bar.showMessage("Extraction complete!", 5000); self.on_item_selected(it, 0); self.extract_btn.setText("Theme Extracted!"); self.extract_btn.setStyleSheet("background-color: #28a745; color: white;"); self.load_items(self.settings["path"])
        except Exception as e: QMessageBox.critical(self, "Error", str(e)); self.reset_extract_button()
        finally: self.extract_btn.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv); window = ThemeExtractor(); window.show(); sys.exit(app.exec())

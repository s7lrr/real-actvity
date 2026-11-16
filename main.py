import json
import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QComboBox, QFileDialog,
    QFrame, QStackedWidget, QMessageBox, QCheckBox, QSizePolicy
)

APP_NAME = "Presence Studio"
APP_DIR = Path(os.getenv("APPDATA", str(Path.home()))) / "PresenceStudio"
CONFIG_FILE = APP_DIR / "settings.json"

ACTIVITY_TYPES = {
    "Playing": 0,
    "Listening": 2,
    "Watching": 3,
    "Competing": 5,
}

def load_settings():
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}

def save_settings(data):
    APP_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

class PresenceWorker(QThread):
    done = Signal(bool, str)

    def __init__(self, settings, action="apply"):
        super().__init__()
        self.settings = settings
        self.action = action

    def run(self):
        rpc = None
        try:
            from pypresence import Presence
            client_id = self.settings.get("client_id", "").strip()
            if not client_id.isdigit():
                raise ValueError("Application ID must contain numbers only.")
            rpc = Presence(client_id)
            rpc.connect()

            if self.action == "stop":
                rpc.clear()
                rpc.close()
                self.done.emit(True, "Activity cleared.")
                return

            activity = self.settings.get("activity_type", "Playing")
            if activity not in ACTIVITY_TYPES:
                raise ValueError("Unsupported activity type.")

            payload = {
                "details": self.settings.get("details", "").strip() or None,
                "state": self.settings.get("state", "").strip() or None,
                "large_image": self.settings.get("asset_key", "").strip() or None,
                "large_text": self.settings.get("image_text", "").strip() or None,
                "small_image": self.settings.get("small_asset_key", "").strip() or None,
                "small_text": self.settings.get("small_image_text", "").strip() or None,
                "buttons": self.settings.get("buttons", []),
                "activity_type": ACTIVITY_TYPES[activity],
            }
            payload = {k: v for k, v in payload.items() if v is not None and v != []}
            rpc.update(**payload)
            rpc.close()
            self.done.emit(True, "Rich Presence updated.")
        except Exception as exc:
            try:
                if rpc:
                    rpc.close()
            except Exception:
                pass
            self.done.emit(False, str(exc))

class StatCard(QFrame):
    def __init__(self, title, description):
        super().__init__()
        self.setObjectName("statCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        t = QLabel(title)
        t.setObjectName("cardTitle")
        d = QLabel(description)
        d.setObjectName("muted")
        d.setWordWrap(True)
        layout.addWidget(t)
        layout.addWidget(d)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(1080, 720)
        self.resize(1240, 820)
        self.settings = load_settings()
        self.worker = None
        self.selected_image = self.settings.get("local_image", "")
        self._build_ui()
        self._load_form()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        outer = QHBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(224)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(18, 22, 18, 18)
        side.setSpacing(12)

        brand_row = QHBoxLayout()
        mark = QLabel("P")
        mark.setObjectName("brandMark")
        mark.setAlignment(Qt.AlignCenter)
        brand = QLabel("PRESENCE\nSTUDIO")
        brand.setObjectName("brandText")
        brand_row.addWidget(mark)
        brand_row.addWidget(brand)
        brand_row.addStretch()
        side.addLayout(brand_row)
        side.addSpacing(26)

        nav_label = QLabel("WORKSPACE")
        nav_label.setObjectName("navLabel")
        side.addWidget(nav_label)
        self.nav_activity = QPushButton("  Activity editor")
        self.nav_activity.setObjectName("navActive")
        self.nav_activity.setCursor(Qt.PointingHandCursor)
        side.addWidget(self.nav_activity)
        side.addSpacing(18)

        nav_label2 = QLabel("INFORMATION")
        nav_label2.setObjectName("navLabel")
        side.addWidget(nav_label2)
        info = QLabel("Configure your Discord Rich Presence using your own application assets.")
        info.setObjectName("sideInfo")
        info.setWordWrap(True)
        side.addWidget(info)
        side.addStretch()

        version = QLabel("DESKTOP EDITION  •  1.1.0")
        version.setObjectName("version")
        side.addWidget(version)

        content = QWidget()
        content.setObjectName("content")
        main = QVBoxLayout(content)
        main.setContentsMargins(34, 26, 34, 26)
        main.setSpacing(20)

        top = QHBoxLayout()
        top_text = QVBoxLayout()
        eyebrow = QLabel("DISCORD INTEGRATION")
        eyebrow.setObjectName("eyebrow")
        heading = QLabel("Activity editor")
        heading.setObjectName("pageTitle")
        subtitle = QLabel("Build and publish a clean Rich Presence for your Discord application.")
        subtitle.setObjectName("muted")
        top_text.addWidget(eyebrow)
        top_text.addWidget(heading)
        top_text.addWidget(subtitle)
        top.addLayout(top_text)
        top.addStretch()
        self.connection_badge = QLabel("NOT CONNECTED")
        self.connection_badge.setObjectName("statusBadge")
        top.addWidget(self.connection_badge, 0, Qt.AlignTop)
        main.addLayout(top)

        cards = QHBoxLayout()
        cards.setSpacing(12)
        cards.addWidget(StatCard("One application", "Use one Application ID that you own and manage."))
        cards.addWidget(StatCard("Local image preview", "Choose an image from your computer to preview it here."))
        cards.addWidget(StatCard("Saved settings", "Your configuration is stored locally on this Windows account."))
        main.addLayout(cards)

        body = QHBoxLayout()
        body.setSpacing(18)

        editor = QFrame()
        editor.setObjectName("panel")
        editor_layout = QVBoxLayout(editor)
        editor_layout.setContentsMargins(22, 20, 22, 22)
        editor_layout.setSpacing(13)

        section = QLabel("PRESENCE CONFIGURATION")
        section.setObjectName("sectionLabel")
        editor_layout.addWidget(section)

        self.client_id = self._add_field(editor_layout, "Application ID", "Enter your Discord Application ID")
        id_row = QHBoxLayout()
        id_row.addWidget(self.client_id, 1)
        self.portal_btn = QPushButton("Open Developer Portal")
        self.portal_btn.setObjectName("secondaryButton")
        self.portal_btn.clicked.connect(self.open_portal)
        id_row.addWidget(self.portal_btn)
        # Move the input out of its original row and place it in the combined row.
        editor_layout.removeWidget(self.client_id)
        editor_layout.addLayout(id_row)

        self.activity_type = QComboBox()
        self.activity_type.addItems(["Playing", "Watching", "Listening", "Competing"])
        self._field_label(editor_layout, "Activity type")
        editor_layout.addWidget(self.activity_type)

        self.details = self._add_field(editor_layout, "Title / details", "For example: Beyond the ordinary.")
        self.state = self._add_field(editor_layout, "Description / state", "For example: Living in my own world")

        divider = QFrame()
        divider.setObjectName("divider")
        divider.setFixedHeight(1)
        editor_layout.addWidget(divider)

        image_head = QHBoxLayout()
        image_title = QLabel("LARGE IMAGE")
        image_title.setObjectName("sectionLabel")
        image_head.addWidget(image_title)
        image_head.addStretch()
        self.choose_image_btn = QPushButton("Choose local image")
        self.choose_image_btn.setObjectName("secondaryButton")
        self.choose_image_btn.clicked.connect(self.choose_image)
        image_head.addWidget(self.choose_image_btn)
        editor_layout.addLayout(image_head)

        self.asset_key = self._add_field(editor_layout, "Discord asset key", "Exact asset name uploaded in Developer Portal")
        self.image_text = self._add_field(editor_layout, "Image hover text", "Optional text shown when hovering over the image")
        self.local_path_label = QLabel("No local preview image selected.")
        self.local_path_label.setObjectName("mutedSmall")
        self.local_path_label.setWordWrap(True)
        editor_layout.addWidget(self.local_path_label)

        self.advanced_toggle = QCheckBox("Show small image and button settings")
        self.advanced_toggle.setObjectName("check")
        self.advanced_toggle.stateChanged.connect(self.toggle_advanced)
        editor_layout.addWidget(self.advanced_toggle)

        self.advanced = QWidget()
        adv = QVBoxLayout(self.advanced)
        adv.setContentsMargins(0, 0, 0, 0)
        adv.setSpacing(10)
        self.small_asset_key = self._add_field(adv, "Small image asset key", "Optional second asset key")
        self.small_image_text = self._add_field(adv, "Small image hover text", "Optional")
        self.button_label = self._add_field(adv, "Button label", "For example: Visit website")
        self.button_url = self._add_field(adv, "Button URL", "https://example.com")
        editor_layout.addWidget(self.advanced)
        self.advanced.hide()

        action_row = QHBoxLayout()
        self.save_btn = QPushButton("Save settings")
        self.save_btn.setObjectName("secondaryButton")
        self.save_btn.clicked.connect(self.save_only)
        self.apply_btn = QPushButton("Apply Rich Presence")
        self.apply_btn.setObjectName("primaryButton")
        self.apply_btn.clicked.connect(self.apply_presence)
        self.stop_btn = QPushButton("Stop activity")
        self.stop_btn.setObjectName("dangerButton")
        self.stop_btn.clicked.connect(self.stop_presence)
        action_row.addWidget(self.save_btn)
        action_row.addStretch()
        action_row.addWidget(self.stop_btn)
        action_row.addWidget(self.apply_btn)
        editor_layout.addLayout(action_row)

        preview = QFrame()
        preview.setObjectName("previewPanel")
        preview.setFixedWidth(310)
        pv = QVBoxLayout(preview)
        pv.setContentsMargins(18, 20, 18, 20)
        pv.setSpacing(14)
        pv_head = QHBoxLayout()
        pv_label = QLabel("LIVE PREVIEW")
        pv_label.setObjectName("sectionLabel")
        pv_head.addWidget(pv_label)
        pv_head.addStretch()
        preview_tag = QLabel("LOCAL")
        preview_tag.setObjectName("localTag")
        pv_head.addWidget(preview_tag)
        pv.addLayout(pv_head)

        self.preview_image = QLabel()
        self.preview_image.setObjectName("previewImage")
        self.preview_image.setAlignment(Qt.AlignCenter)
        self.preview_image.setFixedSize(272, 180)
        self.preview_image.setText("IMAGE PREVIEW")
        pv.addWidget(self.preview_image, 0, Qt.AlignHCenter)

        self.preview_type = QLabel("PLAYING")
        self.preview_type.setObjectName("previewType")
        pv.addWidget(self.preview_type)
        self.preview_title = QLabel("Your activity title")
        self.preview_title.setObjectName("previewTitle")
        self.preview_title.setWordWrap(True)
        pv.addWidget(self.preview_title)
        self.preview_desc = QLabel("Your activity description")
        self.preview_desc.setObjectName("muted")
        self.preview_desc.setWordWrap(True)
        pv.addWidget(self.preview_desc)

        note = QFrame()
        note.setObjectName("noteBox")
        note_layout = QVBoxLayout(note)
        note_layout.setContentsMargins(12, 12, 12, 12)
        note_title = QLabel("Important")
        note_title.setObjectName("noteTitle")
        note_text = QLabel("A local image is only used for preview. To show an image to other Discord users, upload it as an Application Asset and enter its exact asset key.")
        note_text.setObjectName("mutedSmall")
        note_text.setWordWrap(True)
        note_layout.addWidget(note_title)
        note_layout.addWidget(note_text)
        pv.addStretch()
        pv.addWidget(note)

        body.addWidget(editor, 1)
        body.addWidget(preview)
        main.addLayout(body, 1)

        outer.addWidget(sidebar)
        outer.addWidget(content, 1)

        self.activity_type.currentTextChanged.connect(self.refresh_preview)
        self.details.textChanged.connect(self.refresh_preview)
        self.state.textChanged.connect(self.refresh_preview)
        self.refresh_preview()

    def _field_label(self, layout, text):
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        layout.addWidget(label)

    def _add_field(self, layout, label, placeholder):
        self._field_label(layout, label)
        field = QLineEdit()
        field.setPlaceholderText(placeholder)
        field.setMinimumHeight(40)
        field.setObjectName("input")
        layout.addWidget(field)
        return field

    def _load_form(self):
        s = self.settings
        self.client_id.setText(s.get("client_id", ""))
        self.activity_type.setCurrentText(s.get("activity_type", "Playing"))
        self.details.setText(s.get("details", ""))
        self.state.setText(s.get("state", ""))
        self.asset_key.setText(s.get("asset_key", ""))
        self.image_text.setText(s.get("image_text", ""))
        self.small_asset_key.setText(s.get("small_asset_key", ""))
        self.small_image_text.setText(s.get("small_image_text", ""))
        self.button_label.setText(s.get("button_label", ""))
        self.button_url.setText(s.get("button_url", ""))
        self.selected_image = s.get("local_image", "")
        if self.selected_image and Path(self.selected_image).exists():
            self._show_image(self.selected_image)
        self.refresh_preview()

    def collect_settings(self):
        buttons = []
        label = self.button_label.text().strip()
        url = self.button_url.text().strip()
        if label and url:
            buttons = [{"label": label[:32], "url": url}]
        return {
            "client_id": self.client_id.text().strip(),
            "activity_type": self.activity_type.currentText(),
            "details": self.details.text().strip(),
            "state": self.state.text().strip(),
            "asset_key": self.asset_key.text().strip(),
            "image_text": self.image_text.text().strip(),
            "small_asset_key": self.small_asset_key.text().strip(),
            "small_image_text": self.small_image_text.text().strip(),
            "button_label": label,
            "button_url": url,
            "buttons": buttons,
            "local_image": self.selected_image,
        }

    def save_only(self):
        self.settings = self.collect_settings()
        save_settings(self.settings)
        self.set_status("SAVED LOCALLY", True)
        QMessageBox.information(self, "Settings saved", "Your settings have been saved on this computer.")

    def apply_presence(self):
        data = self.collect_settings()
        if not data["client_id"]:
            QMessageBox.warning(self, "Application ID required", "Enter your Discord Application ID first.")
            return
        if data["button_label"] and data["button_url"] and not data["button_url"].startswith(("https://", "http://")):
            QMessageBox.warning(self, "Invalid button URL", "Button URL must start with http:// or https://.")
            return
        self.settings = data
        save_settings(data)
        self._run_worker(data, "apply")

    def stop_presence(self):
        data = self.collect_settings()
        if not data["client_id"]:
            QMessageBox.warning(self, "Application ID required", "Enter your Discord Application ID to clear this application's activity.")
            return
        self._run_worker(data, "stop")

    def _run_worker(self, data, action):
        if self.worker and self.worker.isRunning():
            QMessageBox.information(self, "Please wait", "An operation is already running.")
            return
        self.apply_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.set_status("CONNECTING", False)
        self.worker = PresenceWorker(data, action)
        self.worker.done.connect(self._worker_done)
        self.worker.start()

    def _worker_done(self, ok, message):
        self.apply_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.set_status("CONNECTED" if ok else "NOT CONNECTED", ok)
        if ok:
            QMessageBox.information(self, "Presence Studio", message)
        else:
            QMessageBox.critical(self, "Could not update activity", message + "\n\nMake sure the Discord desktop app is running and the Application ID is correct.")

    def set_status(self, text, ok):
        self.connection_badge.setText(text)
        self.connection_badge.setProperty("good", bool(ok))
        self.connection_badge.style().unpolish(self.connection_badge)
        self.connection_badge.style().polish(self.connection_badge)

    def choose_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose preview image", "", "Images (*.png *.jpg *.jpeg *.webp *.bmp)")
        if path:
            self.selected_image = path
            self._show_image(path)

    def _show_image(self, path):
        pix = QPixmap(path)
        if not pix.isNull():
            self.preview_image.setPixmap(pix.scaled(self.preview_image.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
            self.local_path_label.setText(Path(path).name)

    def toggle_advanced(self, state):
        self.advanced.setVisible(bool(state))

    def refresh_preview(self, *_):
        self.preview_type.setText(self.activity_type.currentText().upper())
        self.preview_title.setText(self.details.text().strip() or "Your activity title")
        self.preview_desc.setText(self.state.text().strip() or "Your activity description")

    def open_portal(self):
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        QDesktopServices.openUrl(QUrl("https://discord.com/developers/applications"))

def apply_style(app):
    app.setStyleSheet("""
    QWidget { color: #e8ebf1; font-family: "Segoe UI"; font-size: 10pt; }
    QMainWindow { background: #0b0e13; }
    #sidebar { background: #0e1219; border-right: 1px solid #202733; }
    #brandMark { background: #dce5f2; color: #10151d; border-radius: 10px; font-size: 18pt; font-weight: 800; min-width: 42px; max-width: 42px; min-height: 42px; max-height: 42px; }
    #brandText { font-size: 10pt; font-weight: 800; letter-spacing: 1.5px; line-height: 1.2; }
    #navLabel, #sectionLabel, #eyebrow { color: #8793a5; font-size: 8pt; font-weight: 700; letter-spacing: 1.5px; }
    #navActive { text-align: left; color: #f4f6fa; background: #202a38; border: 1px solid #2b3a4d; border-radius: 8px; padding: 12px; font-weight: 600; }
    #sideInfo, #muted, #mutedSmall { color: #909bad; }
    #sideInfo { font-size: 9pt; line-height: 1.5; }
    #mutedSmall { font-size: 8pt; }
    #version { color: #657184; font-size: 7.5pt; letter-spacing: 1px; }
    #content { background: #0b0e13; }
    #pageTitle { font-size: 25pt; font-weight: 750; color: #f5f7fb; }
    #statusBadge { background: #242b36; color: #aeb8c8; border: 1px solid #354052; border-radius: 12px; padding: 7px 11px; font-size: 8pt; font-weight: 700; }
    #statusBadge[good="true"] { background: #142b25; color: #8dd8b5; border-color: #24543f; }
    #statCard, #panel, #previewPanel { background: #121821; border: 1px solid #222d3b; border-radius: 12px; }
    #cardTitle { font-weight: 700; color: #edf1f7; }
    #panel { background: #111720; }
    #previewPanel { background: #101720; }
    #fieldLabel { color: #b9c3d1; font-size: 9pt; font-weight: 600; margin-top: 2px; }
    #input, QComboBox { background: #0b1119; border: 1px solid #2a3544; border-radius: 7px; padding: 8px 10px; color: #eef2f7; selection-background-color: #506b91; }
    #input:focus, QComboBox:focus { border: 1px solid #7894bb; }
    QComboBox::drop-down { border: 0; width: 25px; }
    QComboBox QAbstractItemView { background: #151d28; selection-background-color: #344b68; border: 1px solid #2a3544; }
    QPushButton { border-radius: 7px; padding: 10px 13px; font-weight: 650; }
    #primaryButton { background: #dce5f2; color: #101720; border: 1px solid #e8edf5; }
    #primaryButton:hover { background: #ffffff; }
    #secondaryButton { background: #202a37; color: #e3e9f1; border: 1px solid #354356; }
    #secondaryButton:hover { background: #293648; }
    #dangerButton { background: #2b2024; color: #e6b9c0; border: 1px solid #55333c; }
    #dangerButton:hover { background: #3a252c; }
    #divider { background: #283342; }
    #previewImage { background: #0a1017; color: #68768a; border: 1px dashed #344255; border-radius: 9px; font-size: 8pt; font-weight: 700; }
    #previewType { color: #9eabc0; font-size: 8pt; font-weight: 800; letter-spacing: 1.5px; }
    #previewTitle { color: #f4f6fa; font-size: 13pt; font-weight: 750; }
    #localTag { color: #9eb4d0; background: #1d2b3c; border-radius: 8px; padding: 4px 7px; font-size: 7pt; font-weight: 700; }
    #noteBox { background: #172230; border: 1px solid #2c4057; border-radius: 9px; }
    #noteTitle { color: #cbd8e8; font-weight: 700; }
    QCheckBox { color: #bdc7d5; spacing: 8px; }
    QCheckBox::indicator { width: 15px; height: 15px; }
    """)

def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setFont(QFont("Segoe UI", 10))
    apply_style(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

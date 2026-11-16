import json
import os
import sys
import time
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QFrame, QMessageBox,
    QComboBox, QScrollArea, QSplitter, QSizePolicy, QSpacerItem
)
from pypresence import Presence
from pypresence.exceptions import DiscordNotFound

APP_NAME = "Presence Studio"
APP_DIR = Path(os.getenv("APPDATA", str(Path.home()))) / "PresenceStudio"
CONFIG_FILE = APP_DIR / "settings.json"


def load_config():
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {"client_id": "", "presets": {}, "last": {}, **data}
    except Exception:
        pass
    return {"client_id": "", "presets": {}, "last": {}}


def save_config(data):
    APP_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class PresenceStudio(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(1080, 760)
        self.resize(1360, 900)
        self.config = load_config()
        self.rpc = None
        self.connected = False
        self.image_path = ""
        self._build_ui()
        self._load_last()
        self._refresh_presets()
        self._set_status("DISCONNECTED", False)
        self._update_preview()

    def _build_ui(self):
        self.setStyleSheet("""
            * { font-family: 'Segoe UI'; }
            QMainWindow, QWidget#Root { background: #0D0F13; color: #F3F4F6; }
            QFrame#TopBar, QFrame#Panel { background: #151920; border: 1px solid #272D37; border-radius: 16px; }
            QLabel#Brand { color: #F7F8FA; font-size: 21px; font-weight: 800; letter-spacing: 2px; }
            QLabel#Subtle { color: #929BA9; font-size: 12px; }
            QLabel#PageTitle { color: #F6F7F9; font-size: 25px; font-weight: 750; }
            QLabel#SectionTitle { color: #E9ECF1; font-size: 15px; font-weight: 700; }
            QLabel#FieldLabel { color: #C5CBD5; font-size: 12px; font-weight: 650; }
            QLabel#Hint { color: #8792A1; font-size: 11px; }
            QLineEdit, QComboBox { background: #0E1218; color: #F4F6F8; border: 1px solid #303846; border-radius: 10px; padding: 0 14px; min-height: 48px; font-size: 14px; selection-background-color: #6479E8; }
            QLineEdit:focus, QComboBox:focus { border: 1px solid #8294FF; background: #111722; }
            QLineEdit::placeholder { color: #697484; }
            QComboBox QAbstractItemView { background: #171D26; color: #F3F4F6; selection-background-color: #394B9C; border: 1px solid #303846; padding: 6px; }
            QPushButton { background: #202733; color: #E9EDF3; border: 1px solid #354052; border-radius: 10px; min-height: 44px; padding: 0 18px; font-size: 13px; font-weight: 650; }
            QPushButton:hover { background: #2A3444; border-color: #52617A; }
            QPushButton#Primary { background: #6479E8; color: white; border: 1px solid #7D8FFF; }
            QPushButton#Primary:hover { background: #7488F2; }
            QPushButton#Danger { background: #2B1D23; color: #F2C7D0; border: 1px solid #57333E; }
            QPushButton#Quiet { background: transparent; border: 1px solid #303846; }
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { background: #11151B; width: 10px; margin: 4px; border-radius: 5px; }
            QScrollBar::handle:vertical { background: #394354; min-height: 28px; border-radius: 5px; }
            QScrollBar::handle:vertical:hover { background: #596982; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QSplitter::handle { background: #0D0F13; width: 12px; }
        """)

        root = QWidget(); root.setObjectName("Root"); self.setCentralWidget(root)
        outer = QVBoxLayout(root); outer.setContentsMargins(26, 22, 26, 24); outer.setSpacing(18)

        top = QFrame(); top.setObjectName("TopBar")
        top_l = QHBoxLayout(top); top_l.setContentsMargins(22, 15, 22, 15)
        brand_col = QVBoxLayout(); brand_col.setSpacing(3)
        brand = QLabel("PRESENCE STUDIO"); brand.setObjectName("Brand")
        tagline = QLabel("A better way to build your Discord profile activity"); tagline.setObjectName("Subtle")
        brand_col.addWidget(brand); brand_col.addWidget(tagline); top_l.addLayout(brand_col)
        top_l.addStretch()
        self.status_pill = QLabel("●  DISCONNECTED")
        self.status_pill.setAlignment(Qt.AlignCenter)
        self.status_pill.setMinimumWidth(175)
        top_l.addWidget(self.status_pill)
        outer.addWidget(top)

        splitter = QSplitter(Qt.Horizontal); splitter.setChildrenCollapsible(False)
        outer.addWidget(splitter, 1)

        # Wide, scrollable editor column
        editor_scroll = QScrollArea(); editor_scroll.setWidgetResizable(True); editor_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        editor = QFrame(); editor.setObjectName("Panel")
        form = QVBoxLayout(editor); form.setContentsMargins(26, 24, 26, 26); form.setSpacing(18)
        title = QLabel("Create your activity"); title.setObjectName("PageTitle")
        intro = QLabel("Fill in the details below. Your changes are saved on this computer."); intro.setObjectName("Subtle")
        form.addWidget(title); form.addWidget(intro)
        form.addSpacing(5)

        form.addWidget(self._section("01", "Discord application"))
        form.addWidget(self._field_label("APPLICATION ID"))
        self.client_id = QLineEdit(); self.client_id.setPlaceholderText("Paste your Discord Application ID"); self.client_id.setClearButtonEnabled(True)
        form.addWidget(self.client_id)
        help_id = QLabel("Find this in Discord Developer Portal → Your Application → General Information."); help_id.setObjectName("Hint"); help_id.setWordWrap(True)
        form.addWidget(help_id)

        form.addWidget(self._section("02", "Activity information"))
        grid = QGridLayout(); grid.setHorizontalSpacing(16); grid.setVerticalSpacing(12)
        self.title_input = QLineEdit(); self.title_input.setPlaceholderText("e.g. Playing Rocket League")
        self.description_input = QLineEdit(); self.description_input.setPlaceholderText("e.g. Ranked matches")
        grid.addWidget(self._field_label("DETAILS / MAIN LINE"), 0, 0); grid.addWidget(self._field_label("STATE / SECOND LINE"), 0, 1)
        grid.addWidget(self.title_input, 1, 0); grid.addWidget(self.description_input, 1, 1)
        grid.setColumnStretch(0, 1); grid.setColumnStretch(1, 1)
        form.addLayout(grid)

        form.addWidget(self._section("03", "Activity artwork"))
        form.addWidget(self._field_label("DISCORD ASSET KEY"))
        self.asset_input = QLineEdit(); self.asset_input.setPlaceholderText("e.g. game_cover"); self.asset_input.setClearButtonEnabled(True)
        form.addWidget(self.asset_input)
        art_note = QLabel("Upload the image in Developer Portal → Rich Presence → Art Assets, then enter its exact asset name here.")
        art_note.setObjectName("Hint"); art_note.setWordWrap(True); form.addWidget(art_note)
        local_row = QHBoxLayout()
        self.image_path_label = QLabel("No local preview image selected"); self.image_path_label.setObjectName("Subtle"); self.image_path_label.setWordWrap(True)
        local_row.addWidget(self.image_path_label, 1)
        choose = QPushButton("Choose preview image"); choose.clicked.connect(self._choose_image); local_row.addWidget(choose)
        form.addLayout(local_row)
        local_note = QLabel("A local image is only for the preview in this app. It is not uploaded to Discord."); local_note.setObjectName("Hint"); form.addWidget(local_note)

        form.addWidget(self._section("04", "Optional profile button"))
        grid2 = QGridLayout(); grid2.setHorizontalSpacing(16); grid2.setVerticalSpacing(12)
        self.button_text = QLineEdit(); self.button_text.setPlaceholderText("e.g. Visit website")
        self.button_url = QLineEdit(); self.button_url.setPlaceholderText("https://example.com")
        grid2.addWidget(self._field_label("BUTTON LABEL"), 0, 0); grid2.addWidget(self._field_label("BUTTON URL"), 0, 1)
        grid2.addWidget(self.button_text, 1, 0); grid2.addWidget(self.button_url, 1, 1)
        grid2.setColumnStretch(0, 1); grid2.setColumnStretch(1, 1); form.addLayout(grid2)

        form.addWidget(self._section("05", "Your saved presets"))
        preset_row = QHBoxLayout(); self.preset_combo = QComboBox(); self.preset_combo.addItem("Select a saved preset")
        self.preset_combo.currentTextChanged.connect(self._load_preset); preset_row.addWidget(self.preset_combo, 1)
        save = QPushButton("Save current preset"); save.clicked.connect(self._save_preset); preset_row.addWidget(save)
        delete = QPushButton("Delete"); delete.setObjectName("Quiet"); delete.clicked.connect(self._delete_preset); preset_row.addWidget(delete)
        form.addLayout(preset_row)

        actions = QHBoxLayout(); actions.setSpacing(10)
        self.connect_btn = QPushButton("Connect Discord"); self.connect_btn.clicked.connect(self._connect); actions.addWidget(self.connect_btn)
        self.apply_btn = QPushButton("Start / Update Presence"); self.apply_btn.setObjectName("Primary"); self.apply_btn.clicked.connect(self._apply); actions.addWidget(self.apply_btn, 1)
        self.stop_btn = QPushButton("Stop Activity"); self.stop_btn.setObjectName("Danger"); self.stop_btn.clicked.connect(self._stop_presence); actions.addWidget(self.stop_btn)
        form.addSpacing(6); form.addLayout(actions)
        editor_scroll.setWidget(editor); splitter.addWidget(editor_scroll)

        # Preview column
        right = QFrame(); right.setObjectName("Panel")
        preview = QVBoxLayout(right); preview.setContentsMargins(22, 24, 22, 24); preview.setSpacing(16)
        ptitle = QLabel("Profile preview"); ptitle.setObjectName("PageTitle"); preview.addWidget(ptitle)
        psub = QLabel("A live approximation of how your activity may appear on Discord."); psub.setObjectName("Subtle"); psub.setWordWrap(True); preview.addWidget(psub)
        preview.addSpacing(20)
        discord = QFrame(); discord.setStyleSheet("QFrame{background:#23262D;border:1px solid #3A3F49;border-radius:16px;}")
        dc = QVBoxLayout(discord); dc.setContentsMargins(18, 18, 18, 18); dc.setSpacing(14)
        over = QLabel("PLAYING A GAME"); over.setStyleSheet("color:#B6BBC5;font-size:10px;font-weight:800;letter-spacing:1.5px;"); dc.addWidget(over)
        body = QHBoxLayout(); body.setSpacing(14)
        self.preview_image = QLabel("IMAGE"); self.preview_image.setFixedSize(104, 104); self.preview_image.setAlignment(Qt.AlignCenter)
        self.preview_image.setStyleSheet("background:#343A45;border:1px solid #4A5260;border-radius:12px;color:#929BA9;font-size:11px;font-weight:700;")
        body.addWidget(self.preview_image, 0, Qt.AlignTop)
        text_col = QVBoxLayout(); text_col.setSpacing(8)
        self.preview_title = QLabel("Activity title"); self.preview_title.setWordWrap(True); self.preview_title.setStyleSheet("color:#FFFFFF;font-size:16px;font-weight:750;")
        self.preview_description = QLabel("Activity state or description"); self.preview_description.setWordWrap(True); self.preview_description.setStyleSheet("color:#C3C8D1;font-size:13px;")
        elapsed = QLabel("00:00 elapsed"); elapsed.setStyleSheet("color:#929BA9;font-size:11px;")
        text_col.addWidget(self.preview_title); text_col.addWidget(self.preview_description); text_col.addWidget(elapsed); text_col.addStretch()
        body.addLayout(text_col, 1); dc.addLayout(body)
        self.preview_button = QLabel("No button configured"); self.preview_button.setAlignment(Qt.AlignCenter)
        self.preview_button.setStyleSheet("background:#3B414D;color:#F1F3F6;border-radius:9px;padding:12px;font-weight:700;"); dc.addWidget(self.preview_button)
        preview.addWidget(discord)
        preview.addSpacing(10)
        info = QFrame(); info.setStyleSheet("QFrame{background:#111720;border:1px solid #293444;border-radius:12px;}")
        il = QVBoxLayout(info); il.setContentsMargins(15, 15, 15, 15); il.setSpacing(7)
        inf_title = QLabel("BEFORE YOU START"); inf_title.setStyleSheet("color:#AEBBFF;font-size:11px;font-weight:800;letter-spacing:1px;")
        inf_body = QLabel("1. Open Discord Desktop.\n2. Create an app in the Developer Portal.\n3. Upload your artwork as a Rich Presence asset.\n4. Connect, then start your activity.")
        inf_body.setObjectName("Subtle"); inf_body.setWordWrap(True); inf_body.setStyleSheet("color:#AAB3C1;font-size:12px;line-height:1.5;")
        il.addWidget(inf_title); il.addWidget(inf_body); preview.addWidget(info)
        preview.addStretch()
        footer = QLabel("Presence Studio  •  Local settings only"); footer.setObjectName("Hint"); preview.addWidget(footer)
        splitter.addWidget(right); splitter.setSizes([820, 420]); splitter.setStretchFactor(0, 2); splitter.setStretchFactor(1, 1)

        for widget in [self.title_input, self.description_input, self.asset_input, self.button_text, self.button_url]:
            widget.textChanged.connect(self._update_preview)

    def _section(self, number, text):
        label = QLabel(f"{number}   {text}"); label.setObjectName("SectionTitle")
        label.setStyleSheet("color:#E7EAF0;font-size:15px;font-weight:750;padding-top:5px;border-bottom:1px solid #29313D;padding-bottom:9px;")
        return label

    def _field_label(self, text):
        label = QLabel(text); label.setObjectName("FieldLabel"); return label

    def _set_status(self, text, ok):
        if ok:
            style = "background:#172B24;color:#9BE0B5;border:1px solid #2D5943;border-radius:11px;padding:10px 14px;font-size:11px;font-weight:800;"
        else:
            style = "background:#242832;color:#B8C0CD;border:1px solid #3A4352;border-radius:11px;padding:10px 14px;font-size:11px;font-weight:800;"
        self.status_pill.setText("●  " + text); self.status_pill.setStyleSheet(style)

    def _choose_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose preview image", "", "Images (*.png *.jpg *.jpeg *.webp)")
        if path:
            self.image_path = path; self.image_path_label.setText(Path(path).name); self._update_preview()

    def _update_preview(self):
        self.preview_title.setText(self.title_input.text().strip() or "Activity title")
        self.preview_description.setText(self.description_input.text().strip() or "Activity state or description")
        self.preview_button.setText(self.button_text.text().strip() or "No button configured")
        if self.image_path and Path(self.image_path).exists():
            pix = QPixmap(self.image_path)
            if not pix.isNull():
                self.preview_image.setPixmap(pix.scaled(104, 104, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)); self.preview_image.setText("")
                return
        self.preview_image.setPixmap(QPixmap()); self.preview_image.setText("IMAGE")

    def _form_data(self):
        return {"client_id": self.client_id.text().strip(), "title": self.title_input.text().strip(),
                "description": self.description_input.text().strip(), "asset_key": self.asset_input.text().strip(),
                "button_text": self.button_text.text().strip(), "button_url": self.button_url.text().strip(),
                "image_path": self.image_path}

    def _apply_data(self, data):
        self.client_id.setText(data.get("client_id", "")); self.title_input.setText(data.get("title", ""))
        self.description_input.setText(data.get("description", "")); self.asset_input.setText(data.get("asset_key", ""))
        self.button_text.setText(data.get("button_text", "")); self.button_url.setText(data.get("button_url", ""))
        self.image_path = data.get("image_path", "")
        self.image_path_label.setText(Path(self.image_path).name if self.image_path else "No local preview image selected")
        self._update_preview()

    def _load_last(self): self._apply_data(self.config.get("last", {}))

    def _persist(self):
        self.config["last"] = self._form_data(); save_config(self.config)

    def _connect(self):
        client_id = self.client_id.text().strip()
        if not client_id.isdigit():
            QMessageBox.warning(self, "Application ID required", "Enter the numeric Application ID from the Discord Developer Portal."); return
        try:
            if self.rpc:
                try: self.rpc.close()
                except Exception: pass
            self.rpc = Presence(client_id); self.rpc.connect(); self.connected = True
            self.connect_btn.setText("Reconnect Discord"); self._set_status("CONNECTED TO DISCORD", True); self._persist()
        except DiscordNotFound:
            self.connected = False; self.rpc = None; self._set_status("DISCORD NOT FOUND", False)
            QMessageBox.warning(self, "Discord not found", "Open the Discord Desktop application, then try connecting again.")
        except Exception as exc:
            self.connected = False; self.rpc = None; self._set_status("CONNECTION FAILED", False)
            QMessageBox.critical(self, "Connection error", f"Could not connect to Discord.\n\n{exc}")

    def _apply(self):
        if not self.connected or not self.rpc:
            QMessageBox.information(self, "Connect first", "Connect to Discord before starting your activity."); return
        data = self._form_data()
        if not data["title"] and not data["description"]:
            QMessageBox.warning(self, "Activity details missing", "Enter a main line or a state before continuing."); return
        if data["button_url"] and not data["button_url"].startswith(("https://", "http://")):
            QMessageBox.warning(self, "Invalid URL", "The button URL must start with http:// or https://."); return
        kwargs = {"details": data["title"] or None, "state": data["description"] or None, "start": int(time.time())}
        if data["asset_key"]: kwargs["large_image"] = data["asset_key"]
        if data["button_text"] and data["button_url"]: kwargs["buttons"] = [{"label": data["button_text"][:32], "url": data["button_url"]}]
        try:
            self.rpc.update(**kwargs); self._persist(); self._set_status("ACTIVITY IS RUNNING", True)
            QMessageBox.information(self, "Activity started", "Your Discord Rich Presence has been updated. Keep Presence Studio running.")
        except Exception as exc:
            self._set_status("UPDATE FAILED", False); QMessageBox.critical(self, "Update failed", f"Discord did not accept the activity.\n\n{exc}")

    def _stop_presence(self):
        if not self.rpc or not self.connected:
            self._set_status("DISCONNECTED", False); return
        try:
            self.rpc.clear(); self._set_status("ACTIVITY STOPPED", False)
        except Exception as exc: QMessageBox.warning(self, "Could not stop activity", str(exc))

    def _save_preset(self):
        data = self._form_data()
        if not data["title"] and not data["description"]:
            QMessageBox.warning(self, "Empty preset", "Add activity details before saving a preset."); return
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "Save preset", "Preset name:")
        if not ok or not name.strip(): return
        self.config.setdefault("presets", {})[name.strip()] = data; self._persist(); save_config(self.config)
        self._refresh_presets(); self.preset_combo.setCurrentText(name.strip())

    def _refresh_presets(self):
        current = self.preset_combo.currentText() if hasattr(self, "preset_combo") else ""
        self.preset_combo.blockSignals(True); self.preset_combo.clear(); self.preset_combo.addItem("Select a saved preset")
        for name in sorted(self.config.get("presets", {}).keys()): self.preset_combo.addItem(name)
        if current: self.preset_combo.setCurrentText(current)
        self.preset_combo.blockSignals(False)

    def _load_preset(self, name):
        data = self.config.get("presets", {}).get(name)
        if data: self._apply_data(data)

    def _delete_preset(self):
        name = self.preset_combo.currentText()
        if name in self.config.get("presets", {}):
            del self.config["presets"][name]; save_config(self.config); self._refresh_presets()

    def closeEvent(self, event):
        self._persist()
        if self.rpc:
            try: self.rpc.close()
            except Exception: pass
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv); app.setApplicationName(APP_NAME); app.setFont(QFont("Segoe UI", 10))
    window = PresenceStudio(); window.show(); sys.exit(app.exec())

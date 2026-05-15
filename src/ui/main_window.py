import sys
import os
import string
import psutil
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QProgressBar, 
                             QPlainTextEdit, QFileDialog, QFrame, QCheckBox, QMessageBox, QGroupBox, QGridLayout)
from PyQt6.QtCore import Qt, QTimer, QThread
from PyQt6.QtGui import QIcon

from ..utils.session import load_settings, save_settings
from ..utils.analyzer import analyze_file
from ..utils.i18n import get_translator
from ..utils.paths import resource_path
from ..engine.recovery import RecoveryWorker
from .themes import get_qss
from .components import ModernCheckBox

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.theme = self.settings.get("theme", "dark")
        self.lang = self.settings.get("lang", "en")
        self.translator = get_translator(self.lang)
        self.init_ui()
        self._set_icon()
        self._init_timer()
        self.retranslate_ui()
        QTimer.singleShot(1000, self.prewarm_engine)

    def closeEvent(self, event):
        from ..engine.recovery import shutdown_executor
        shutdown_executor()
        event.accept()

    def _init_timer(self):
        self.res_timer = QTimer(self)
        self.res_timer.timeout.connect(self.on_poll_resources)
        self.res_timer.start(2000)

    def _set_icon(self):
        p = resource_path("icons/icons.png")
        if os.path.exists(p): self.setWindowIcon(QIcon(p))

    def init_ui(self):
        self.setWindowTitle("Document Unlocker PRO")
        self.setMinimumSize(850, 900)
        self.setStyleSheet(get_qss(self.theme, self.lang))
        
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(30)
        
        # Header - Modern & Clean
        header = QHBoxLayout()
        title_v = QVBoxLayout()
        title_v.setSpacing(5)
        self.title_lbl = QLabel("DOCUMENT UNLOCKER PRO")
        self.title_lbl.setObjectName("title")
        title_v.addWidget(self.title_lbl)
        self.sub_lbl = QLabel("")
        self.sub_lbl.setObjectName("subtitle")
        title_v.addWidget(self.sub_lbl)
        header.addLayout(title_v)
        header.addStretch()
        
        ctrl_h = QHBoxLayout()
        ctrl_h.setSpacing(15)
        self.lang_btn = QPushButton("")
        self.lang_btn.setFixedWidth(130)
        self.lang_btn.clicked.connect(self.toggle_lang)
        ctrl_h.addWidget(self.lang_btn)
        
        self.theme_btn = QPushButton("🌙" if self.theme == "light" else "☀️")
        self.theme_btn.setFixedWidth(60)
        self.theme_btn.clicked.connect(self.toggle_theme)
        ctrl_h.addWidget(self.theme_btn)
        header.addLayout(ctrl_h)
        main_layout.addLayout(header)
        
        # Main Card - Glassmorphism Style
        self.main_card = QFrame()
        self.main_card.setObjectName("card")
        card_layout = QVBoxLayout(self.main_card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(30)
        
        # File Drop Section
        file_v = QVBoxLayout()
        file_v.setSpacing(12)
        self.file_lbl = QLabel("SELECT PROTECTED DOCUMENT")
        self.file_lbl.setStyleSheet("font-weight: 700; color: #64748b; font-size: 11px; letter-spacing: 1px;")
        file_v.addWidget(self.file_lbl)
        
        file_h = QHBoxLayout()
        file_h.setSpacing(10)
        self.file_in = QLineEdit()
        self.file_in.textChanged.connect(self.on_file_changed)
        file_h.addWidget(self.file_in, 1)
        self.browse_btn = QPushButton("BROWSE")
        self.browse_btn.setFixedWidth(100)
        self.browse_btn.clicked.connect(self.on_browse)
        file_h.addWidget(self.browse_btn)
        file_v.addLayout(file_h)
        card_layout.addLayout(file_v)
        
        # Strategy Grid
        self.options_group = QGroupBox("RECOVERY CONFIGURATION")
        grid = QGridLayout(self.options_group)
        grid.setContentsMargins(20, 30, 20, 20)
        grid.setSpacing(20)
        
        self.dict_chk = ModernCheckBox("Dictionary Mode")
        self.dict_chk.setChecked(True)
        grid.addWidget(self.dict_chk, 0, 0)
        
        self.rules_chk = ModernCheckBox("Smart Rule Engine")
        self.rules_chk.setChecked(True)
        grid.addWidget(self.rules_chk, 0, 1)
        
        self.brute_chk = ModernCheckBox("Numeric Brute Force")
        self.brute_chk.setChecked(True)
        grid.addWidget(self.brute_chk, 1, 0)
        
        # Removed GPU Acceleration for hardware safety
        
        self.boost_chk = ModernCheckBox("Smart Boost Mode")
        grid.addWidget(self.boost_chk, 2, 0)
        
        card_layout.addWidget(self.options_group)
        
        # Primary Action
        self.unlock_btn = QPushButton("START RECOVERY")
        self.unlock_btn.setObjectName("accentBtn")
        self.unlock_btn.setMinimumHeight(80)
        self.unlock_btn.clicked.connect(self.on_unlock_now)
        card_layout.addWidget(self.unlock_btn)
        
        self.stop_btn = QPushButton("ABORT MISSION")
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.setMinimumHeight(80)
        self.stop_btn.setVisible(False)
        self.stop_btn.clicked.connect(self.on_stop)
        card_layout.addWidget(self.stop_btn)
        
        main_layout.addWidget(self.main_card)
        
        # Log Section - Integrated Look
        log_v = QVBoxLayout()
        log_v.setSpacing(10)
        self.log_lbl = QLabel("RECOVERY ENGINE TELEMETRY")
        self.log_lbl.setStyleSheet("font-weight: 700; color: #64748b; font-size: 11px; letter-spacing: 1px;")
        log_v.addWidget(self.log_lbl)
        
        self.log_area = QPlainTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setPlaceholderText("Engine standby...")
        log_v.addWidget(self.log_area, 1)
        main_layout.addLayout(log_v)
        
        # Footer Bar
        footer = QVBoxLayout()
        footer.setSpacing(15)
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        footer.addWidget(self.progress)
        
        status_h = QHBoxLayout()
        self.status_lbl = QLabel(" System Ready")
        self.status_lbl.setStyleSheet("color: #64748b; font-weight: 600;")
        status_h.addWidget(self.status_lbl)
        status_h.addStretch()
        self.res_lbl = QLabel("CPU: 0% | RAM: 0% ")
        self.res_lbl.setStyleSheet("color: #64748b; font-family: monospace;")
        status_h.addWidget(self.res_lbl)
        footer.addLayout(status_h)
        main_layout.addLayout(footer)

    def retranslate_ui(self):
        t = self.t
        self.title_lbl.setText(t("title"))
        self.sub_lbl.setText(f"{t('subtitle')}: CPU Optimized Cluster")
        
        flag = "🇺🇸" if self.lang == "en" else "🇰🇭"
        name = "English" if self.lang == "en" else "Khmer"
        self.lang_btn.setText(f"{flag} {name}")
        
        self.file_lbl.setText(t("dashboard.file_lbl"))
        self.file_in.setPlaceholderText(t("dashboard.placeholder"))
        self.browse_btn.setText(t("dashboard.browse"))
        
        self.options_group.setTitle("STRATEGY OPTIONS" if self.lang == "en" else "ជម្រើសយុទ្ធសាស្ត្រ")
        self.dict_chk.setText(t("dashboard.use_dict"))
        self.rules_chk.setText("Apply Smart Rules" if self.lang == "en" else "អនុវត្តវិធានឆ្លាតវៃ")
        self.brute_chk.setText("Full Brute Force" if self.lang == "en" else "វាយប្រហារដោយកម្លាំងបាយ")
        self.boost_chk.setText(t("dashboard.boost"))
        
        # GPU detection removed

        self.unlock_btn.setText("UNLOCK NOW" if self.lang == "en" else "ដោះសោឥឡូវនេះ")
        self.stop_btn.setText(t("dashboard.stop"))
        self.log_lbl.setText("ACTIVITY LOG" if self.lang == "en" else "កំណត់ត្រាសកម្មភាព")
        self.status_lbl.setText(t("status.ready"))

    def on_browse(self):
        filters = "Supported Documents (*.docx *.xlsx *.pptx *.pdf *.zip *.rar *.7z);;All Files (*)"
        fn, _ = QFileDialog.getOpenFileName(self, "Select Document", "", filters)
        if fn: self.file_in.setText(fn)

    def on_file_changed(self, text):
        if not text: return
        res = analyze_file(text)
        if res:
            self.log(f"Intelligence Report: {res['insight']}")

    def on_unlock_now(self):
        tf = self.file_in.text()
        if not tf or not os.path.exists(tf):
            QMessageBox.warning(self, "Error", self.t("status.error_file"))
            return
            
        self.log_area.clear()
        self.log("🚀 INITIALIZING ADVANCED RECOVERY SEQUENCE...")
        self.log(f"📦 TARGET: {os.path.basename(tf)}")
        
        settings = {
            "boost": self.boost_chk.isChecked(),
            "use_dict": self.dict_chk.isChecked(),
            "use_rules": self.rules_chk.isChecked(),
            "char_set": string.digits if self.brute_chk.isChecked() else None
        }
        
        self.status_lbl.setText(self.t("status.init"))
        self.worker = RecoveryWorker(tf, "smart", settings)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.log_signal.connect(self.log)
        self.worker.start()
        
        self.progress.setRange(0, 0)
        
        self.unlock_btn.setVisible(False)
        self.stop_btn.setVisible(True)

    def on_stop(self):
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.status_lbl.setText(self.t("status.stopping"))
            self.worker.stop()
            self.stop_btn.setEnabled(False)

    def on_progress(self, count, speed):
        self.status_lbl.setText(self.t("status.running", count=f"{count:,}", speed=f"{speed:,}"))
        if count > 0 and count % 500000 == 0:
            self.log(f"SYSTEM: Verified {count:,} candidates... [Efficiency: {speed:,} p/s]")

    def on_finished(self, status, res):
        self.unlock_btn.setVisible(True)
        self.stop_btn.setVisible(False)
        self.stop_btn.setEnabled(True)
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        
        if status == "Success":
            self.status_lbl.setText("DECRYPTION SUCCESSFUL")
            self.log(f"✨ UNLOCKED SUCCESSFULLY!")
            self.log(f"🔑 ACCESS KEY: {res}")
            QMessageBox.information(self, "Success", f"SUCCESS!\n\nPassword found: {res}")
        elif status == "Stopped":
            self.log("⚠ Sequence aborted by user.")
            self.status_lbl.setText("Aborted")
        else:
            self.log("❌ Exhausted all possible combinations.")
            self.status_lbl.setText("Failed")

    def log(self, message):
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_area.appendPlainText(f"[{ts}] {message}")
        self.log_area.verticalScrollBar().setValue(self.log_area.verticalScrollBar().maximum())

    def toggle_lang(self):
        self.lang = "km" if self.lang == "en" else "en"
        self.translator = get_translator(self.lang)
        self.settings["lang"] = self.lang
        save_settings(self.settings)
        self.setStyleSheet(get_qss(self.theme, self.lang))
        self.retranslate_ui()

    def toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        save_settings({"theme": self.theme, "lang": self.lang})
        self.setStyleSheet(get_qss(self.theme, self.lang))
        self.theme_btn.setText("🌙" if self.theme == "light" else "☀️")

    def on_poll_resources(self):
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        self.res_lbl.setText(f"CPU: {cpu}% | RAM: {ram}% ")

    def prewarm_engine(self):
        try:
            from ..engine.recovery import get_executor
            nw = os.cpu_count() or 4
            QThread.create(lambda: get_executor(int(nw * 1.5)))
        except: pass

    def t(self, key, **kwargs):
        return self.translator.t(key, **kwargs)

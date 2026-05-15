import sys
import os
import string
import psutil
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QProgressBar, 
                             QPlainTextEdit, QFileDialog, QFrame, QCheckBox, QMessageBox, QGroupBox, QGridLayout, QComboBox, QSpinBox)
from PyQt6.QtCore import Qt, QTimer, QThread
from PyQt6.QtGui import QIcon

from ..utils.session import load_settings, save_settings
from ..utils.analyzer import analyze_file
from ..utils.i18n import get_translator
from ..utils.paths import resource_path
from ..engine.recovery import RecoveryWorker
from .themes import get_qss
from .components import ModernCheckBox

from PyQt6.QtWidgets import QDialog, QFormLayout, QTabWidget

class ProfilerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Target Profiler Wizard")
        self.setFixedWidth(400)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.first_name = QLineEdit()
        self.last_name = QLineEdit()
        self.birth_year = QLineEdit()
        self.pet_name = QLineEdit()
        self.fav_team = QLineEdit()
        self.custom_keywords = QLineEdit()
        self.custom_keywords.setPlaceholderText("comma, separated, words")
        
        form.addRow("First Name:", self.first_name)
        form.addRow("Last Name:", self.last_name)
        form.addRow("Birth Year:", self.birth_year)
        form.addRow("Pet's Name:", self.pet_name)
        form.addRow("Favorite Team:", self.fav_team)
        form.addRow("Custom Keywords:", self.custom_keywords)
        
        layout.addLayout(form)
        
        self.error_lbl = QLabel("")
        self.error_lbl.setStyleSheet("color: #ef4444; font-weight: 600; margin-top: 5px;")
        layout.addWidget(self.error_lbl)
        
        btn_h = QHBoxLayout()
        self.gen_btn = QPushButton("Generate Dictionary")
        self.gen_btn.clicked.connect(self.on_generate)
        btn_h.addWidget(self.gen_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_h.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_h)
        
    def on_generate(self):
        if not self.get_words():
            self.error_lbl.setText("Please enter at least one keyword!")
        else:
            self.accept()
        
    def get_words(self):
        words = []
        for w in [self.first_name.text(), self.last_name.text(), self.pet_name.text(), self.fav_team.text()]:
            if w: words.append(w)
            
        custom = self.custom_keywords.text()
        if custom:
            words.extend([w.strip() for w in custom.split(",") if w.strip()])
            
        year = self.birth_year.text()
        
        results = set(words)
        for w in words:
            if year:
                results.add(w + year)
                results.add(w + year[2:] if len(year) == 4 else w)
            results.add(w.lower())
            results.add(w.capitalize())
            results.add(w + "123")
            results.add(w + "!")
            
        return list(results)

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
        self.theme_btn.setFixedWidth(80)
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
        # Create Tab Widget
        self.tabs = QTabWidget()
        
        # Tab 1: Strategy Option
        self.tab_strategy = QWidget()
        grid = QGridLayout(self.tab_strategy)
        grid.setContentsMargins(20, 20, 20, 20)
        grid.setSpacing(20)
        
        self.dict_chk = ModernCheckBox("Dictionary Mode")
        self.dict_chk.setChecked(True)
        grid.addWidget(self.dict_chk, 0, 0)
        
        self.rules_chk = ModernCheckBox("Smart Rule Engine")
        self.rules_chk.setChecked(True)
        grid.addWidget(self.rules_chk, 0, 1)
        
        self.brute_chk = ModernCheckBox("Brute Force Search")
        self.brute_chk.setChecked(True)
        grid.addWidget(self.brute_chk, 1, 0)
        
        self.complexity_combo = QComboBox()
        self.complexity_combo.setMinimumHeight(40)
        grid.addWidget(self.complexity_combo, 1, 1)
        
        self.boost_chk = ModernCheckBox("Smart Boost Mode")
        grid.addWidget(self.boost_chk, 2, 0)
        
        self.tabs.addTab(self.tab_strategy, "Strategy Option")
        
        # Tab 2: Advanced Option
        self.tab_advanced = QWidget()
        adv_layout = QGridLayout(self.tab_advanced)
        adv_layout.setContentsMargins(20, 20, 20, 20)
        adv_layout.setSpacing(10)
        
        self.min_lbl = QLabel("Min Length:")
        self.min_spin = QSpinBox()
        self.min_spin.setRange(1, 12)
        self.min_spin.setValue(1)
        adv_layout.addWidget(self.min_lbl, 0, 0)
        adv_layout.addWidget(self.min_spin, 0, 1)
        
        self.max_lbl = QLabel("Max Length:")
        self.max_spin = QSpinBox()
        self.max_spin.setRange(1, 12)
        self.max_spin.setValue(12)
        adv_layout.addWidget(self.max_lbl, 0, 2)
        adv_layout.addWidget(self.max_spin, 0, 3)
        
        self.charset_lbl = QLabel("Custom Charset:")
        self.charset_in = QLineEdit()
        self.charset_in.setPlaceholderText("e.g. abc123!@#")
        adv_layout.addWidget(self.charset_lbl, 1, 0)
        adv_layout.addWidget(self.charset_in, 1, 1, 1, 3)
        
        self.mask_lbl = QLabel("Mask Pattern:")
        self.mask_in = QLineEdit()
        self.mask_in.setPlaceholderText("e.g. ?u?l?d?d")
        adv_layout.addWidget(self.mask_lbl, 2, 0)
        adv_layout.addWidget(self.mask_in, 2, 1, 1, 3)
        
        self.resume_chk = ModernCheckBox("Resume Session")
        adv_layout.addWidget(self.resume_chk, 3, 0, 1, 2)
        
        self.profiler_btn = QPushButton("Target Profiler Wizard")
        self.profiler_btn.clicked.connect(self.on_open_profiler)
        adv_layout.addWidget(self.profiler_btn, 3, 2, 1, 2)
        
        self.tabs.addTab(self.tab_advanced, "Advanced Option")
        
        card_layout.addWidget(self.tabs)
        
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
        
        self.tabs.setTabText(0, "Strategy Option" if self.lang == "en" else "ជម្រើសយុទ្ធសាស្ត្រ")
        self.dict_chk.setText(t("dashboard.use_dict"))
        self.rules_chk.setText("Apply Smart Rules" if self.lang == "en" else "អនុវត្តវិធានឆ្លាតវៃ")
        self.brute_chk.setText(t("dashboard.start_brute"))
        self.complexity_combo.clear()
        self.complexity_combo.addItems(t("dashboard.complexities"))
        self.boost_chk.setText(t("dashboard.boost"))
        
        self.tabs.setTabText(1, "Advanced Option" if self.lang == "en" else "ជម្រើសកម្រិតខ្ពស់")
        self.min_lbl.setText(t("dashboard.min_len"))
        self.max_lbl.setText(t("dashboard.max_len"))
        self.charset_lbl.setText(t("dashboard.custom_cs"))
        self.mask_lbl.setText(t("dashboard.mask_pattern"))
        self.resume_chk.setText(t("dashboard.resume"))
        
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
        
        cs = None
        if self.brute_chk.isChecked():
            custom_cs = self.charset_in.text()
            if custom_cs:
                cs = custom_cs
            else:
                idx = self.complexity_combo.currentIndex()
                import string
                cs_map = [
                    string.digits,                                      # Numeric
                    string.ascii_lowercase,                             # Lowercase
                    string.ascii_uppercase,                             # Uppercase
                    string.ascii_letters + string.digits,               # Alphanumeric
                    string.ascii_letters + string.digits + string.punctuation # Extended
                ]
                if 0 <= idx < len(cs_map):
                    cs = cs_map[idx]
                else:
                    cs = string.digits

        settings = {
            "boost": self.boost_chk.isChecked(),
            "use_dict": self.dict_chk.isChecked(),
            "use_rules": self.rules_chk.isChecked(),
            "char_set": cs,
            "min_len": self.min_spin.value(),
            "max_len": self.max_spin.value(),
            "mask": self.mask_in.text(),
            "resume": self.resume_chk.isChecked()
        }
        
        mode = "smart"
        if settings["mask"]:
            mode = "mask"
        elif self.brute_chk.isChecked():
            idx = self.complexity_combo.currentIndex()
            if idx == 5:
                mode = "markov"
            elif idx == 6:
                mode = "keyboard"
            elif idx == 7:
                mode = "passphrase"
            elif idx == 8:
                mode = "hybrid"
            elif idx == 9:
                mode = "hashcat"
            
        self.status_lbl.setText(self.t("status.init"))
        self.worker = RecoveryWorker(tf, mode, settings)
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

    def on_open_profiler(self):
        dialog = ProfilerDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            words = dialog.get_words()
            if words:
                os.makedirs("dictionaries", exist_ok=True)
                file_path = "dictionaries/profiler_output.txt"
                with open(file_path, "w") as f:
                    f.write("\n".join(words))
                
                QMessageBox.information(self, "Success", f"Generated {len(words)} candidates and saved to dictionaries/profiler_output.txt.\nIt will be checked automatically in Dictionary Mode.")
                self.dict_chk.setChecked(True)

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

import sys
import os
import string
import itertools
import threading
import time
import subprocess
import psutil
import atexit
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QComboBox, QProgressBar, 
                             QTabWidget, QTextEdit, QPlainTextEdit, QFileDialog, QFrame, QCheckBox, QStatusBar, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, QThread
from PyQt6.QtGui import QIcon

from ..utils.session import load_settings, save_settings
from ..utils.analyzer import analyze_file
from ..utils.i18n import get_translator
from ..utils.paths import resource_path
from ..engine.recovery import RecoveryWorker, shutdown_executor
from .themes import get_qss
from .components import NeonGraph

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
        # Pre-warm hardware clusters
        QTimer.singleShot(1000, self.prewarm_engine)

    def closeEvent(self, event):
        from ..engine.recovery import shutdown_executor
        shutdown_executor()
        event.accept()

    def _init_timer(self):
        self.res_timer = QTimer(self)
        self.res_timer.timeout.connect(self.on_poll_resources)
        self.res_timer.start(2000) # Poll every 2 seconds

    def _set_icon(self):
        p = resource_path("icons/icons.png")
        if os.path.exists(p): self.setWindowIcon(QIcon(p))

    def init_ui(self):
        self.setWindowTitle("Document Unlocker PRO")
        self.resize(850, 900)
        self.setStyleSheet(get_qss(self.theme))
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Header
        header = QHBoxLayout()
        title_v = QVBoxLayout()
        lbl = QLabel("DOCUMENT UNLOCKER PRO")
        lbl.setObjectName("title")
        title_v.addWidget(lbl)
        self.sub_lbl = QLabel("")
        self.sub_lbl.setObjectName("subtitle")
        title_v.addWidget(self.sub_lbl)
        header.addLayout(title_v)
        header.addStretch()
        
        # Language & Theme Controls
        ctrl_h = QHBoxLayout()
        self.lang_btn = QPushButton("")
        self.lang_btn.setFixedWidth(100)
        self.lang_btn.clicked.connect(self.toggle_lang)
        ctrl_h.addWidget(self.lang_btn)
        
        self.theme_btn = QPushButton("🌙" if self.theme == "light" else "☀️")
        self.theme_btn.clicked.connect(self.toggle_theme)
        ctrl_h.addWidget(self.theme_btn)
        header.addLayout(ctrl_h)
        
        layout.addLayout(header)
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        self._setup_dashboard()
        self._setup_patterns()
        self._setup_rules()
        self._setup_dict()
        self._setup_docs()
        self._setup_about()
        
        # Footer
        footer = QFrame()
        fl = QVBoxLayout(footer)
        self.graph = NeonGraph(self, self.theme)
        fl.addWidget(self.graph)
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        fl.addWidget(self.progress)
        layout.addWidget(footer)

        # Status Bar
        self.setStatusBar(QStatusBar())
        self.status_lbl = QLabel(" Ready")
        self.statusBar().addWidget(self.status_lbl)
        self.res_lbl = QLabel("CPU: 0% | RAM: 0% ")
        self.statusBar().addPermanentWidget(self.res_lbl)

    def _setup_dashboard(self):
        tab = QWidget()
        self.tabs.addTab(tab, "") 
        l = QVBoxLayout(tab)
        l.setContentsMargins(20, 20, 20, 20)
        
        self.file_lbl = QLabel("")
        l.addWidget(self.file_lbl)
        fh = QHBoxLayout()
        self.file_in = QLineEdit()
        self.file_in.textChanged.connect(self.on_file_changed)
        fh.addWidget(self.file_in)
        self.browse_btn = QPushButton("")
        self.browse_btn.clicked.connect(self.on_browse)
        fh.addWidget(self.browse_btn)
        l.addLayout(fh)
        
        l.addSpacing(10)
        self.comp_lbl = QLabel("")
        l.addWidget(self.comp_lbl)
        self.complexity_combo = QComboBox()
        l.addWidget(self.complexity_combo)
        
        l.addSpacing(10)
        self.boost_chk = QCheckBox("")
        l.addWidget(self.boost_chk)
        
        self.dict_chk = QCheckBox("")
        l.addWidget(self.dict_chk)
        
        self.gpu_chk = QCheckBox("")
        l.addWidget(self.gpu_chk)
        
        # Log Area (Now Primary)
        l.addSpacing(10)
        self.log_area = QPlainTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setPlaceholderText("Engine Log Ready...")
        self.log_area.setStyleSheet("""
            QPlainTextEdit {
                background: #0f172a;
                color: #38bdf8;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                border: 1px solid #1e293b;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        l.addWidget(self.log_area, 1) 
        btn_h = QHBoxLayout()
        self.start_btn = QPushButton("")
        self.start_btn.setMinimumHeight(50)
        self.start_btn.clicked.connect(self.on_start)
        btn_h.addWidget(self.start_btn, 1)
        
        self.smart_btn = QPushButton("")
        self.smart_btn.setObjectName("accentBtn")
        self.smart_btn.setMinimumHeight(50)
        self.smart_btn.clicked.connect(self.on_smart_start)
        btn_h.addWidget(self.smart_btn, 1)
        
        self.stop_btn = QPushButton("")
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.setVisible(False)
        self.stop_btn.setMinimumHeight(50)
        self.stop_btn.clicked.connect(self.on_stop)
        btn_h.addWidget(self.stop_btn)
        l.addLayout(btn_h)

    def _setup_patterns(self):
        tab = QWidget()
        self.tabs.addTab(tab, "")
        l = QVBoxLayout(tab)
        l.setContentsMargins(20, 20, 20, 20)
        self.mask_title = QLabel("")
        l.addWidget(self.mask_title)
        self.mask_in = QLineEdit()
        l.addWidget(self.mask_in)
        
        self.mask_info = QFrame()
        self.mask_info.setObjectName("card")
        il = QVBoxLayout(self.mask_info)
        self.mask_legend_lbl = QLabel("")
        il.addWidget(self.mask_legend_lbl)
        self.mask_d_lbl = QLabel("")
        il.addWidget(self.mask_d_lbl)
        self.mask_l_lbl = QLabel("")
        il.addWidget(self.mask_l_lbl)
        self.mask_u_lbl = QLabel("")
        il.addWidget(self.mask_u_lbl)
        self.mask_s_lbl = QLabel("")
        il.addWidget(self.mask_s_lbl)
        self.mask_a_lbl = QLabel("")
        il.addWidget(self.mask_a_lbl)
        l.addWidget(self.mask_info)
        
        l.addStretch()
        self.mask_start_btn = QPushButton("")
        self.mask_start_btn.setObjectName("accentBtn")
        self.mask_start_btn.clicked.connect(self.on_start)
        l.addWidget(self.mask_start_btn)

    def _setup_rules(self):
        tab = QWidget()
        self.tabs.addTab(tab, "")
        l = QVBoxLayout(tab)
        l.setContentsMargins(20, 20, 20, 20)
        self.rule_lbl = QLabel("")
        l.addWidget(self.rule_lbl)
        self.rule_in = QLineEdit()
        l.addWidget(self.rule_in)
        
        self.rule_desc = QLabel("")
        self.rule_desc.setWordWrap(True)
        l.addWidget(self.rule_desc)
        
        l.addStretch()
        self.rule_start_btn = QPushButton("")
        self.rule_start_btn.setObjectName("accentBtn")
        self.rule_start_btn.clicked.connect(self.on_start)
        l.addWidget(self.rule_start_btn)
        
    def _setup_dict(self):
        tab = QWidget()
        self.tabs.addTab(tab, "")
        l = QVBoxLayout(tab)
        l.setContentsMargins(20, 20, 20, 20)
        
        self.dict_title = QLabel("")
        l.addWidget(self.dict_title)
        
        dh = QHBoxLayout()
        self.dict_combo = QComboBox()
        self.dict_combo.currentIndexChanged.connect(self.on_dict_selected)
        dh.addWidget(self.dict_combo, 1)
        
        self.dict_refresh_btn = QPushButton("🔄")
        self.dict_refresh_btn.setFixedWidth(40)
        self.dict_refresh_btn.clicked.connect(self.refresh_dicts)
        dh.addWidget(self.dict_refresh_btn)
        l.addLayout(dh)
        
        l.addSpacing(10)
        self.dict_preview_title = QLabel("")
        l.addWidget(self.dict_preview_title)
        self.dict_preview = QTextEdit()
        self.dict_preview.setReadOnly(True)
        self.dict_preview.setMaximumHeight(200)
        l.addWidget(self.dict_preview)
        
        self.dict_hybrid_chk = QCheckBox("")
        l.addWidget(self.dict_hybrid_chk)
        
        l.addStretch()
        self.dict_start_btn = QPushButton("")
        self.dict_start_btn.setObjectName("accentBtn")
        self.dict_start_btn.clicked.connect(self.on_start)
        l.addWidget(self.dict_start_btn)
        
        self.refresh_dicts()

    def refresh_dicts(self):
        self.dict_combo.clear()
        d_dir = "dictionaries"
        if not os.path.exists(d_dir): os.makedirs(d_dir)
        files = [f for f in os.listdir(d_dir) if f.endswith(".txt")]
        self.dict_combo.addItems(files)

    def on_dict_selected(self):
        fn = self.dict_combo.currentText()
        if not fn: return
        path = os.path.join("dictionaries", fn)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    head = [next(f).strip() for _ in range(10)]
                    self.dict_preview.setText("\n".join(head) + "\n...")
            except: self.dict_preview.setText("Error reading preview.")

    def _setup_docs(self):
        tab = QWidget()
        self.tabs.addTab(tab, "")
        l = QVBoxLayout(tab)
        self.docs_edit = QTextEdit()
        self.docs_edit.setReadOnly(True)
        l.addWidget(self.docs_edit)

    def _setup_about(self):
        tab = QWidget()
        self.tabs.addTab(tab, "")
        l = QVBoxLayout(tab)
        about_card = QFrame()
        about_card.setObjectName("card")
        al = QVBoxLayout(about_card)
        self.about_lbl1 = QLabel("<b>DOCUMENT UNLOCKER PRO</b>")
        al.addWidget(self.about_lbl1)
        self.about_lbl2 = QLabel("Version: 2.5.0 Professional Edition")
        al.addWidget(self.about_lbl2)
        self.about_lbl3 = QLabel("Engine: Hybrid C++/Python Multi-threaded")
        al.addWidget(self.about_lbl3)
        self.about_lbl4 = QLabel("Backend: OpenCL 2.0 / PyQt6 6.11")
        al.addWidget(self.about_lbl4)
        al.addSpacing(20)
        self.about_lbl5 = QLabel("<i>Designed for high-performance security auditing and password recovery.</i>")
        al.addWidget(self.about_lbl5)
        l.addWidget(about_card)
        l.addStretch()

    def prewarm_engine(self):
        # Starts the process pool in the background so it's ready instantly when user clicks Start
        try:
            from ..engine.recovery import get_executor
            import multiprocessing
            nw = os.cpu_count() or 4
            # Initialize with boost-level workers to be ready for anything
            QThread.create(lambda: get_executor(int(nw * 1.5)))
        except: pass

    def t(self, key, **kwargs):
        return self.translator.t(key, **kwargs)

    def toggle_lang(self):
        self.lang = "km" if self.lang == "en" else "en"
        self.translator = get_translator(self.lang)
        self.settings["lang"] = self.lang
        save_settings(self.settings)
        self.retranslate_ui()

    def retranslate_ui(self):
        t = self.t
        title_lbl = self.findChild(QLabel, "title")
        if title_lbl: title_lbl.setText(t("title"))
        gpu_info = self.get_gpu_info()
        self.sub_lbl.setText(f"{t('subtitle')}: {gpu_info}")
        
        # Update Flag on Toggle
        flag = "🇺🇸" if self.lang == "en" else "🇰🇭"
        name = "English" if self.lang == "en" else "Khmer"
        self.lang_btn.setText(f"{flag} {name}")
        
        # Tabs
        self.tabs.setTabText(0, t("tabs.dashboard"))
        self.tabs.setTabText(1, t("tabs.patterns"))
        self.tabs.setTabText(2, t("tabs.rules"))
        self.tabs.setTabText(3, t("tabs.dict"))
        self.tabs.setTabText(4, t("tabs.docs"))
        self.tabs.setTabText(5, t("tabs.about"))
        
        # Dashboard
        self.file_lbl.setText(t("dashboard.file_lbl"))
        self.file_in.setPlaceholderText(t("dashboard.placeholder"))
        self.browse_btn.setText(t("dashboard.browse"))
        self.comp_lbl.setText(t("dashboard.complexity_lbl"))
        
        prev_idx = self.complexity_combo.currentIndex()
        self.complexity_combo.clear()
        self.complexity_combo.addItems(t("dashboard.complexities"))
        if prev_idx >= 0: self.complexity_combo.setCurrentIndex(prev_idx)
        
        self.boost_chk.setText(t("dashboard.boost"))
        self.boost_chk.setToolTip(t("dashboard.boost_tip"))
        self.dict_chk.setText(t("dashboard.use_dict"))
        
        gpu_info = self.get_gpu_info()
        is_valid_gpu = gpu_info not in ["Software Only", "No GPU Detected", "No GPU"]
        if is_valid_gpu:
            self.gpu_chk.setText(f"{t('dashboard.use_gpu')} ({gpu_info})")
            self.gpu_chk.setEnabled(True)
            self.gpu_chk.setStyleSheet("")
        else:
            self.gpu_chk.setText(t("dashboard.no_gpu"))
            self.gpu_chk.setEnabled(False)
            self.gpu_chk.setStyleSheet("color: #64748b; font-style: italic;")
            
        self.start_btn.setText(t("dashboard.start"))
        self.smart_btn.setText(t("dashboard.smart_start"))
        self.stop_btn.setText(t("dashboard.stop"))
        
        # Patterns
        self.mask_title.setText(t("patterns.title"))
        self.mask_in.setPlaceholderText(t("patterns.placeholder"))
        self.mask_legend_lbl.setText(f"<b>{t('patterns.legend')}</b>")
        self.mask_d_lbl.setText(f"?d = {t('patterns.digits')}")
        self.mask_l_lbl.setText(f"?l = {t('patterns.lower')}")
        self.mask_u_lbl.setText(f"?u = {t('patterns.upper')}")
        self.mask_s_lbl.setText(f"?s = {t('patterns.symbols')}")
        self.mask_a_lbl.setText(f"?a = {t('patterns.all')}")
        self.mask_start_btn.setText(t("patterns.start"))
        
        # Rules
        self.rule_lbl.setText(t("rules.lbl"))
        self.rule_in.setPlaceholderText(t("rules.placeholder"))
        self.rule_desc.setText(t("rules.desc"))
        self.rule_start_btn.setText(t("rules.start"))
        
        # Dictionary
        self.dict_title.setText(t("dict.select_lbl"))
        self.dict_preview_title.setText(t("dict.preview_lbl"))
        self.dict_hybrid_chk.setText(t("dict.hybrid"))
        self.dict_start_btn.setText(t("dict.start"))
        
        self.docs_edit.setHtml(t("docs_content"))
        self.status_lbl.setText(t("status.ready"))

    def on_browse(self):
        filters = "Supported Documents (*.docx *.xlsx *.pptx *.pdf *.zip *.rar *.7z);;Office Files (*.docx *.xlsx *.pptx);;PDF Files (*.pdf);;Archives (*.zip *.rar *.7z);;All Files (*)"
        fn, _ = QFileDialog.getOpenFileName(self, "Select Document", "", filters)
        if fn: self.file_in.setText(fn)

    def on_file_changed(self, text):
        res = analyze_file(text)
        if res:
            self.log(f"File Selected: {os.path.basename(text)}")
            self.log(f"Intelligence: {res['insight']}")

    def toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        save_settings({"theme": self.theme, "lang": self.lang})
        self.setStyleSheet(get_qss(self.theme))
        self.theme_btn.setText("🌙" if self.theme == "light" else "☀️")
        self.graph.theme = self.theme
        self.graph.update()

    def on_start(self, mode=None):
        tf = self.file_in.text()
        if not tf or not os.path.exists(tf):
            QMessageBox.warning(self, "Error", self.t("status.error_file"))
            return
            
        self.log_area.clear()
        self.log(f"Initializing Recovery Engine...")
        self.log(f"Target: {os.path.basename(tf)}")
        
        current_tab = self.tabs.currentIndex()
        if not mode:
            mode = "brute"
        settings = {}
        
        if current_tab == 0: # Dashboard (Brute)
            mode = "brute"
            mapping = {
                0: string.digits,
                1: string.ascii_lowercase,
                2: string.ascii_uppercase,
                3: string.ascii_letters + string.digits,
                4: string.ascii_letters + string.digits + string.punctuation
            }
            settings["char_set"] = mapping.get(self.complexity_combo.currentIndex(), string.digits)
        elif current_tab == 1: # Patterns (Mask)
            mode = "mask"
            settings["mask"] = self.mask_in.text()
            if not settings["mask"]:
                return QMessageBox.warning(self, "Error", self.t("status.error_mask"))
        elif current_tab == 2: # Smart Rules
            mode = "rules"
            settings["keyword"] = self.rule_in.text()
            if not settings["keyword"]:
                return QMessageBox.warning(self, "Error", self.t("status.error_keyword"))
        elif current_tab == 3: # Dictionary
            mode = "dict"
            fn = self.dict_combo.currentText()
            if not fn:
                return QMessageBox.warning(self, "Error", self.t("dict.error_dict"))
            settings["dict_path"] = os.path.join("dictionaries", fn)
            settings["hybrid"] = self.dict_hybrid_chk.isChecked()

        settings["boost"] = self.boost_chk.isChecked()
        settings["use_dict"] = self.dict_chk.isChecked()
        settings["use_gpu"] = self.gpu_chk.isChecked()
        settings["gpu_info"] = self.get_gpu_info()
        self.start_btn.setEnabled(False)
        self.status_lbl.setText(self.t("status.init"))
        self.worker = RecoveryWorker(tf, mode, settings)
        if self.boost_chk.isChecked():
            if self.worker.isRunning():
                self.worker.setPriority(QThread.Priority.HighestPriority)
            
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.log_signal.connect(self.log)
        self.worker.start()
        
        self.start_btn.setVisible(False)
        self.smart_btn.setVisible(False)
        self.stop_btn.setVisible(True)
        self.stop_btn.setEnabled(True)

    def on_smart_start(self):
        self.on_start(mode="smart")

    def on_stop(self):
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.status_lbl.setText(self.t("status.stopping"))
            self.worker.stop()
            self.stop_btn.setEnabled(False)

    def on_poll_resources(self):
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        gpu = self.get_gpu_usage()
        
        gpu_str = f" | GPU: {gpu}%" if gpu is not None else ""
        self.res_lbl.setText(f"CPU: {cpu}%{gpu_str} | RAM: {ram}% ")

    def on_progress(self, count, speed):
        self.status_lbl.setText(self.t("status.running", count=f"{count:,}", speed=f"{speed:,}"))
        # Only log every 50,000 candidates to avoid UI lag on fast systems
        if count > 0 and count % 50000 == 0:
            self.log(f"Validated {count:,} candidates... Current Speed: {speed:,} p/s")
        self.progress.setRange(0, 0)
        self.graph.update_data(speed)

    def log(self, message):
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_area.appendPlainText(f"[{ts}] {message}")
        # Auto-scroll to bottom
        self.log_area.verticalScrollBar().setValue(self.log_area.verticalScrollBar().maximum())

    def on_finished(self, status, res):
        self.start_btn.setVisible(True)
        self.start_btn.setEnabled(True)
        self.smart_btn.setVisible(True)
        self.smart_btn.setEnabled(True)
        self.stop_btn.setVisible(False)
        self.stop_btn.setEnabled(True)
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        
        count = self.worker.tested_count if hasattr(self, 'worker') else 0
        
        if status == "Success":
            self.status_lbl.setText(self.t("status.success"))
            self.log(f"✅ SUCCESS: Password Recovered after {count:,} tests!")
            self.log(f"🔑 PASSWORD: {res}")
            QMessageBox.information(self, "Success", f"SUCCESS!\n\nPassword found: {res}\nTotal tested: {count:,}")
        elif status == "Stopped":
            self.log("🛑 Recovery process stopped by user.")
        else:
            self.log("❌ Recovery failed. Try a different complexity or pattern.")
            self.status_lbl.setText(self.t("status.failed"))

    def closeEvent(self, event):
        shutdown_executor()
        event.accept()

    def get_gpu_info(self):
        try:
            import pyopencl as cl
            all_devices = []
            for platform in cl.get_platforms():
                all_devices.extend(platform.get_devices())
            
            if not all_devices: return "No GPU Detected"
            
            # Prioritize Intel Arc/Dedicated GPUs
            preferred = None
            for dev in all_devices:
                name = dev.name.upper()
                if "ARC" in name or "XE " in name or "DEDICATED" in name:
                    preferred = dev.name.strip()
                    break
                if "INTEL" in name and not preferred:
                    preferred = dev.name.strip()
                elif ("NVIDIA" in name or "AMD" in name) and not preferred:
                    preferred = dev.name.strip()
            
            return preferred if preferred else all_devices[0].name.strip()
        except:
            return "Software Only"

    def get_gpu_usage(self):
        # Try NVIDIA
        try:
            res = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu', '--format=csv,noheader,nounits'], capture_output=True, text=True)
            if res.returncode == 0: return int(res.stdout.strip())
        except: pass

        # Try Intel Xe (Modern Arc/Dedicated)
        try:
            # Common path for Battlemage/Alchemist (Xe driver)
            p_act = "/sys/class/drm/card0/device/tile0/gt0/freq0/act_freq"
            p_max = "/sys/class/drm/card0/device/tile0/gt0/freq0/max_freq"
            if os.path.exists(p_act) and os.path.exists(p_max):
                with open(p_act, "r") as f1, open(p_max, "r") as f2:
                    act = int(f1.read().strip())
                    mx = int(f2.read().strip())
                    if mx > 0: return min(100, int((act / mx) * 100))
        except: pass

        # Try Intel/AMD via generic sysfs (Linux)
        for i in range(2):
            try:
                p = f"/sys/class/drm/card{i}/device/gpu_busy_percent"
                if os.path.exists(p):
                    with open(p, "r") as f:
                        return int(f.read().strip())
                
                # Legacy Intel
                p_cur = f"/sys/class/drm/card{i}/device/gt_cur_freq_mhz"
                p_max = f"/sys/class/drm/card{i}/device/gt_max_freq_mhz"
                if os.path.exists(p_cur) and os.path.exists(p_max):
                    with open(p_cur, "r") as f1, open(p_max, "r") as f2:
                        cur = int(f1.read().strip())
                        mx = int(f2.read().strip())
                        if mx > 0: return min(100, int((cur / mx) * 100))
            except: pass
        
        return None

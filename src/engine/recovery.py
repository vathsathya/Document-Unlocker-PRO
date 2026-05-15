import os
import time
import threading
import zipfile
import io
import subprocess
import shutil
import gc
import psutil
import itertools
import string
from concurrent.futures import ProcessPoolExecutor, as_completed
from PyQt6.QtCore import QThread, pyqtSignal
import msoffcrypto
import pikepdf
from ..utils.paths import resource_path

# Global persistent pool
_global_executor = None

def get_executor(max_workers):
    global _global_executor
    if _global_executor is None:
        try:
            _global_executor = ProcessPoolExecutor(max_workers=max_workers)
        except Exception as e:
            print(f"Multiprocessing error: {e}")
            return None
    return _global_executor

def shutdown_executor():
    global _global_executor
    if _global_executor is not None:
        try:
            _global_executor.shutdown(wait=False, cancel_futures=True)
            parent = psutil.Process()
            for child in parent.children(recursive=True):
                try: child.terminate()
                except: pass
        except: pass
        _global_executor = None
    gc.collect()

def check_password_office(msfile, password):
    try:
        msfile.load_key(password=password, verify_password=True)
        return password
    except (msoffcrypto.exceptions.InvalidKeyError, msoffcrypto.exceptions.DecryptionError):
        return None
    except Exception:
        return None

def check_password_pdf(pdf_path, password):
    try:
        with pikepdf.open(pdf_path, password=password) as pdf: 
            return password
    except:
        return None

def check_password_single(target_file, password, ext):
    try:
        if ext == '.zip':
            with zipfile.ZipFile(target_file) as zf:
                try:
                    zf.setpassword(password.encode('utf-8'))
                    # Test one file to verify password
                    if zf.testzip() is None: return password
                except:
                    # Fallback for different encodings
                    zf.setpassword(password.encode('cp437'))
                    if zf.testzip() is None: return password
        elif ext == '.rar':
            # unrar returns 0 on success
            res = subprocess.run(['unrar', 't', '-p' + password, target_file], capture_output=True, text=True)
            if res.returncode == 0: return password
        elif ext == '.7z':
            cmd = '7z' if shutil.which('7z') else '7zz'
            res = subprocess.run([cmd, 't', '-p' + password, target_file], capture_output=True, text=True)
            if res.returncode == 0: return password
    except: pass
    return None

def check_batch(target_file, passwords, ext, boost=False):
    # Smart Yield: Set lower priority so the engine doesn't compete with the UI/User
    try:
        p = psutil.Process()
        if os.name == 'nt': p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
        else: p.nice(10) 
    except: pass
        
    try:
        if ext in ['.docx', '.xlsx', '.pptx']:
            with open(target_file, "rb") as f:
                msfile = msoffcrypto.OfficeFile(f)
                for p in passwords:
                    if check_password_office(msfile, p): return p
        elif ext == '.pdf':
            with open(target_file, "rb") as f:
                pdf_data = f.read()
            for p in passwords:
                try:
                    with pikepdf.open(io.BytesIO(pdf_data), password=p) as pdf:
                        return p
                except: pass
        elif ext == '.zip':
            with zipfile.ZipFile(target_file) as zf:
                try:
                    # Test only the first file to quickly verify password
                    first_file = zf.namelist()[0]
                except: return None
                for p in passwords:
                    try:
                        zf.setpassword(p.encode('utf-8'))
                        with zf.open(first_file) as f: f.read(1)
                        return p
                    except:
                        try:
                            zf.setpassword(p.encode('cp437'))
                            with zf.open(first_file) as f: f.read(1)
                            return p
                        except: pass
        else:
            # Fallback for Rar and others
            for p in passwords:
                res = check_password_single(target_file, p, ext)
                if res: return res
    except Exception:
        return None 
    return None

class RecoveryWorker(QThread):
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(str, str)
    log_signal = pyqtSignal(str)
    
    def __init__(self, target_file, mode, settings):
        super().__init__()
        self.target_file = os.path.abspath(target_file)
        self.mode = mode
        self.settings = settings
        self.stop_event = threading.Event()
        self.tested_count = 0
        self.last_tested = 0
        self.last_time = time.time()

    def stop(self):
        self.stop_event.set()

    def _apply_smart_rules(self, word):
        variations = {word}
        # Expanded Leet Speak
        leet_map = str.maketrans({
            "a": "4", "A": "4", "e": "3", "E": "3", "i": "1", "I": "1",
            "o": "0", "O": "0", "s": "5", "S": "5", "t": "7", "T": "7",
            "g": "9", "G": "9", "b": "8", "B": "8"
        })
        variations.add(word.translate(leet_map))
        
        # Capitalization variations
        variations.add(word.capitalize())
        variations.add(word.upper())
        variations.add(word.lower())
        if len(word) > 1:
            variations.add(word[0].lower() + word[1:].upper())
        
        # Common Suffixes & Prefixes
        suffixes = ["!", "!!", "123", "1234", "01", "2026", "2025", "@", "#"]
        for s in suffixes:
            variations.add(f"{word}{s}")
            variations.add(f"{s}{word}")
            
        # Year Appending (Extended)
        current_year = 2026
        for y in range(current_year - 10, current_year + 3):
            variations.add(f"{word}{y}")
            variations.add(f"{word}@{y}")
            variations.add(f"{word}{str(y)[2:]}")
            
        # Structural
        variations.add(word + word)
        variations.add(word[::-1])
        
        return list(variations)

    def _try_all_dictionaries(self, ex, tf, ext, boost, start_time, use_rules=False):
        d_dirs = [resource_path("dictionaries"), "dictionaries"]
        for d_dir in d_dirs:
            if os.path.exists(d_dir):
                dicts = [os.path.join(d_dir, f) for f in os.listdir(d_dir) if f.endswith(".txt")]
                for dp in dicts:
                    if self.stop_event.is_set(): break
                    res = self._run_dict(ex, tf, dp, ext, boost, start_time, use_rules)
                    if res: return res
        return None

    def run(self):
        tf = self.target_file
        ext = os.path.splitext(tf)[1].lower()
        self.tested_count = 0
        self.progress.emit(0, 0)
        start_time = time.time()
        self.last_time = start_time
        boost = self.settings.get("boost", False)
        use_dict = self.settings.get("use_dict", False)
        
        # CPU Headroom Optimization: Ensure usage stays below 95% 
        # by leaving at least one core free for OS/UI tasks.
        cores = os.cpu_count() or 4
        if boost:
            nw = max(1, cores - 1)
        else:
            nw = max(1, int(cores * 0.6)) # ~60% usage for balanced mode
        
        ex = get_executor(nw)
        if not ex:
            self.log_signal.emit("CRITICAL ERROR: Engine initialization failed.")
            return self.finished.emit("Failed", "")
        
        if self.mode == "smart":
            use_rules = self.settings.get("use_rules", False)
            # Phase 1: Dictionary
            if use_dict:
                self.log_signal.emit("Phase 1: Dictionary Scan")
                res = self._try_all_dictionaries(ex, tf, ext, boost, start_time, use_rules=use_rules)
                if res: return self.finished.emit("Success", res)
            else:
                self.log_signal.emit("Phase 1: Dictionary Scan (Skipped)")
            
            # Phase 2: Numeric brute-force fallback
            cs = self.settings.get("char_set")
            if cs:
                self.log_signal.emit(f"Phase 2: Brute Force ({cs})")
                res = self._run_brute(ex, tf, cs, ext, boost, start_time, max_len=6)
                if res: return self.finished.emit("Success", res)
            else:
                self.log_signal.emit("Phase 2: Brute Force (Skipped)")

        elif self.mode == "mask":
            self.log_signal.emit(f"Unlocking with Mask: {self.settings.get('mask', '')}")
            mask = self.settings.get("mask", "")
            res = self._run_mask(ex, tf, mask, ext, boost, start_time)
            if res: return self.finished.emit("Success", res)
        elif self.mode == "dict":
            dict_path = self.settings.get("dict_path", "")
            use_rules = self.settings.get("use_rules", False)
            self.log_signal.emit(f"Unlocking with Dictionary: {os.path.basename(dict_path)}")
            res = self._run_dict(ex, tf, dict_path, ext, boost, start_time, use_rules=use_rules)
            if res: return self.finished.emit("Success", res)
        else:
            # Dashboard mode: Try dictionary first if requested
            if use_dict:
                use_rules = self.settings.get("use_rules", False)
                self.log_signal.emit("Option 1: Dictionary Scan")
                res = self._try_all_dictionaries(ex, tf, ext, boost, start_time, use_rules=use_rules)
                if res: return self.finished.emit("Success", res)
            
            self.log_signal.emit("Option 2: Brute Force Search")
            cs = self.settings.get("char_set")
            if cs:
                self.log_signal.emit("Option 2: Brute Force Search")
                res = self._run_brute(ex, tf, cs, ext, boost, start_time)
                if res: return self.finished.emit("Success", res)
            else:
                self.log_signal.emit("Option 2: Brute Force Search (Skipped)")
        
        if self.stop_event.is_set():
            self.finished.emit("Stopped", "")
        else:
            self.finished.emit("Failed", "")

    def _run_brute(self, ex, tf, cs, ext, boost, start_time, min_len=1, max_len=12):
        is_slow = ext in ['.docx', '.xlsx', '.pptx']
        base_batch = 500 if is_slow else 10000
        base_batch = 500 if ext in [".docx", ".xlsx", ".pptx"] else 10000; batch_size = base_batch * 2 if boost else base_batch * 2 if boost else base_batch
        
        for length in range(min_len, max_len + 1):
            batch = []
            for combo in itertools.product(cs, repeat=length):
                if self.stop_event.is_set(): return None
                batch.append("".join(combo))
                if len(batch) >= batch_size:
                    res = self.run_ex_check(ex, tf, batch, ext, boost, start_time)
                    if res: return res
                    batch = []
            if batch:
                res = self.run_ex_check(ex, tf, batch, ext, boost, start_time)
                if res: return res
        return None

    def _run_mask(self, ex, tf, mask, ext, boost, start_time):
        # Simple mask parser: ?d=digits, ?l=lowercase, ?u=uppercase, etc.
        sets = []
        i = 0
        while i < len(mask):
            if mask[i] == '?' and i+1 < len(mask):
                t = mask[i+1]
                if t == 'd': sets.append(string.digits)
                elif t == 'l': sets.append(string.ascii_lowercase)
                elif t == 'u': sets.append(string.ascii_uppercase)
                else: sets.append(mask[i:i+2])
                i += 2
            else:
                sets.append(mask[i])
                i += 1
        
        batch = []
        base_batch = 500 if ext in ['.docx', '.xlsx', '.pptx'] else 10000
        batch_size = base_batch * 2 if boost else base_batch
        for combo in itertools.product(*sets):
            if self.stop_event.is_set(): return None
            batch.append("".join(combo))
            if len(batch) >= batch_size:
                res = self.run_ex_check(ex, tf, batch, ext, boost, start_time)
                if res: return res
                batch = []
        if batch:
            res = self.run_ex_check(ex, tf, batch, ext, boost, start_time)
            if res: return res
        return None

    def _run_dict(self, ex, tf, dict_path, ext, boost, start_time, use_rules=False):
        if not os.path.exists(dict_path): return None
        batch = []
        base_batch = 500 if ext in ['.docx', '.xlsx', '.pptx'] else 10000
        batch_size = base_batch * 2 if boost else base_batch
        with open(dict_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if self.stop_event.is_set(): break
                word = line.strip()
                if use_rules:
                    batch.extend(self._apply_smart_rules(word))
                else:
                    batch.append(word)
                
                if len(batch) >= batch_size:
                    res = self.run_ex_check(ex, tf, batch, ext, boost, start_time)
                    if res: return res
                    batch = []
            if batch:
                res = self.run_ex_check(ex, tf, batch, ext, boost, start_time)
                if res: return res
        return None

    def run_ex_check(self, ex, tf, pl, ext, boost=False, start_time=None):
        future_to_size = {}
        chunk_size = max(10, len(pl) // (ex._max_workers * 2))
        for i in range(0, len(pl), chunk_size):
            if self.stop_event.is_set(): break
            ch = pl[i:i + chunk_size]
            fut = ex.submit(check_batch, tf, ch, ext, boost)
            future_to_size[fut] = len(ch)
            
        for f in as_completed(future_to_size):
            if self.stop_event.is_set(): return None
            try:
                r = f.result()
                if r:
                    self.stop_event.set()
                    return r
                self.tested_count += future_to_size[f]
                if start_time: self.update_progress(start_time)
            except: continue
        return None

    def update_progress(self, start_time):
        now = time.time()
        el_total = now - start_time
        el_delta = now - self.last_time
        if el_delta > 0.5:
            delta_tested = self.tested_count - self.last_tested
            sp = int(delta_tested / el_delta)
            self.last_tested = self.tested_count
            self.last_time = now
            self.progress.emit(self.tested_count, sp)

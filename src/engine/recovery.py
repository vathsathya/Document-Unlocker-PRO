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
    if boost:
        try:
            p = psutil.Process()
            if os.name == 'nt': p.nice(psutil.HIGH_PRIORITY_CLASS)
            else: p.nice(-10)
        except: pass
        
    try:
        if ext in ['.docx', '.xlsx', '.pptx']:
            with open(target_file, "rb") as f:
                msfile = msoffcrypto.OfficeFile(f)
                for p in passwords:
                    if check_password_office(msfile, p): return p
        elif ext == '.pdf':
            for p in passwords:
                if check_password_pdf(target_file, p): return p
        else:
            for p in passwords:
                res = check_password_single(target_file, p, ext)
                if res: return res
    except:
        return None # Silent failure for individual batches
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

    def run(self):
        tf = self.target_file
        ext = os.path.splitext(tf)[1].lower()
        self.tested_count = 0
        self.progress.emit(0, 0)
        start_time = time.time()
        self.last_time = start_time
        boost = self.settings.get("boost", False)
        use_gpu = self.settings.get("use_gpu", False)
        nw = os.cpu_count() or 4
        
        # Hardware-specific scaling
        gpu_info = self.settings.get("gpu_info", "").upper()
        is_intel_dedicated = "ARC" in gpu_info or "XE " in gpu_info
        
        if boost: nw = int(nw * 1.5)
        if use_gpu:
            if is_intel_dedicated:
                nw = nw * 3 # Maximum scaling for Intel Arc/Xe
            else:
                nw = nw * 2
        
        ex = get_executor(nw)
        
        if self.mode == "smart":
            res = self._run_brute(ex, tf, string.digits, ext, boost, start_time, max_len=6)
            if res: return self.finished.emit("Success", res)
            
            # Dictionary fallback
            d_dir = "dictionaries"
            if os.path.exists(d_dir):
                dicts = [os.path.join(d_dir, f) for f in os.listdir(d_dir) if f.endswith(".txt")]
                for dp in dicts:
                    if self.stop_event.is_set(): break
                    res = self._run_dict(ex, tf, dp, ext, boost, start_time)
                    if res: return self.finished.emit("Success", res)

        elif self.mode == "mask":
            mask = self.settings.get("mask", "")
            res = self._run_mask(ex, tf, mask, ext, boost, start_time)
            if res: return self.finished.emit("Success", res)
        elif self.mode == "dict":
            dict_path = self.settings.get("dict_path", "")
            res = self._run_dict(ex, tf, dict_path, ext, boost, start_time)
            if res: return self.finished.emit("Success", res)
        else:
            cs = self.settings.get("char_set", string.digits)
            res = self._run_brute(ex, tf, cs, ext, boost, start_time)
            if res: return self.finished.emit("Success", res)
        
        if self.stop_event.is_set():
            self.finished.emit("Stopped", "")
        else:
            self.finished.emit("Failed", "")

    def _run_brute(self, ex, tf, cs, ext, boost, start_time, min_len=1, max_len=12):
        is_slow = ext in ['.docx', '.xlsx', '.pptx']
        use_gpu = self.settings.get("use_gpu", False)
        gpu_info = self.settings.get("gpu_info", "").upper()
        is_intel_dedicated = "ARC" in gpu_info or "XE " in gpu_info
        
        base_batch = 500 if is_slow else 10000
        # Aggressive batching for dedicated hardware
        multiplier = 1
        if use_gpu:
            multiplier = 8 if is_intel_dedicated else 4
            
        batch_size = base_batch * multiplier
        
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
        use_gpu = self.settings.get("use_gpu", False)
        base_batch = 500 if ext in ['.docx', '.xlsx', '.pptx'] else 10000
        batch_size = base_batch * (4 if use_gpu else 1)
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

    def _run_dict(self, ex, tf, dict_path, ext, boost, start_time):
        if not os.path.exists(dict_path): return None
        batch = []
        use_gpu = self.settings.get("use_gpu", False)
        base_batch = 500 if ext in ['.docx', '.xlsx', '.pptx'] else 10000
        batch_size = base_batch * (4 if use_gpu else 1)
        with open(dict_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if self.stop_event.is_set(): break
                batch.append(line.strip())
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

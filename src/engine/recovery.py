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
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from PyQt6.QtCore import QThread, pyqtSignal
import msoffcrypto
import pikepdf
from ..utils.paths import resource_path, get_external_path

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

    def _is_file_locked(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        try:
            if ext == '.pdf':
                try:
                    with pikepdf.open(file_path) as pdf:
                        return False
                except pikepdf.PasswordError:
                    return True
                except Exception:
                    return False
            elif ext in ['.docx', '.xlsx', '.pptx']:
                with open(file_path, "rb") as f:
                    msfile = msoffcrypto.OfficeFile(f)
                    return msfile.is_encrypted()
            elif ext == '.zip':
                with zipfile.ZipFile(file_path) as zf:
                    try:
                        zf.testzip()
                        return False
                    except RuntimeError as e:
                        if "password required" in str(e) or "File is password protected" in str(e):
                            return True
                        return False
            elif ext in ['.rar', '.7z']:
                cmd = '7z' if shutil.which('7z') else '7zz'
                if ext == '.rar' and shutil.which('unrar'):
                    res = subprocess.run(['unrar', 't', '-p-', file_path], capture_output=True, text=True)
                    if res.returncode == 0: return False
                    return True
                
                res = subprocess.run([cmd, 't', '-p-', file_path], capture_output=True, text=True)
                if res.returncode == 0: return False
                return True
        except Exception:
            pass
        return True # Default to locked

    def _apply_smart_rules(self, word):
        variations = {word}
        # Expanded Leet Speak (Style 1: Numbers)
        leet_map1 = str.maketrans({
            "a": "4", "A": "4", "e": "3", "E": "3", "i": "1", "I": "1",
            "o": "0", "O": "0", "s": "5", "S": "5", "t": "7", "T": "7",
            "g": "9", "G": "9", "b": "8", "B": "8"
        })
        variations.add(word.translate(leet_map1))
        
        # Expanded Leet Speak (Style 2: Symbols)
        leet_map2 = str.maketrans({
            "a": "@", "A": "@", "e": "3", "E": "3", "i": "!", "I": "!",
            "o": "0", "O": "0", "s": "$", "S": "$", "t": "+", "T": "+"
        })
        variations.add(word.translate(leet_map2))
        
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
            
        # Year Mutations (Date Mutation)
        current_year = 2026
        for y in range(current_year - 10, current_year + 3):
            y_str = str(y)
            short_y = y_str[2:]
            
            # Appending
            variations.add(f"{word}{y}")
            variations.add(f"{word}@{y}")
            variations.add(f"{word}{short_y}")
            
            # Prepending
            variations.add(f"{y}{word}")
            variations.add(f"{short_y}{word}")
            
        # Structural
        variations.add(word + word)
        variations.add(word[::-1])
        
        return list(variations)

    def _try_all_dictionaries(self, ex, tf, ext, boost, start_time, use_rules=False):
        d_dirs = [get_external_path("dictionaries")]
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
        
        if not self._is_file_locked(tf):
            self.log_signal.emit("File has no password or file is Unlocked!")
            return self.finished.emit("NoPassword", "")
            
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
            
        # Phase 0: Metadata Extraction & Smart Guess
        self.log_signal.emit("Phase 0: Extracting Metadata Hints...")
        hints = self._extract_metadata(tf)
        if hints:
            self.log_signal.emit(f"Found {len(hints)} metadata hints. Testing them...")
            # Apply rules to hints to expand candidates
            hint_candidates = []
            for h in hints:
                hint_candidates.extend(self._apply_smart_rules(h))
                
            res = self.run_ex_check(ex, tf, hint_candidates, ext, boost, start_time)
            if res: return self.finished.emit("Success", res)
        else:
            self.log_signal.emit("No metadata hints found or file is fully encrypted.")
        
        if self.mode == "smart":
            use_rules = self.settings.get("use_rules", False)
            # Phase 1: Dictionary
            if use_dict:
                word_count = 0
                d_dir = get_external_path("dictionaries")
                if os.path.exists(d_dir):
                    dicts = [os.path.join(d_dir, f) for f in os.listdir(d_dir) if f.endswith(".txt")]
                    for dp in dicts:
                        try:
                            with open(dp, "r", encoding="utf-8", errors="ignore") as f:
                                word_count += sum(1 for _ in f)
                        except: pass
                
                self.log_signal.emit(f"Phase 1: Dictionary Scan [word count: {word_count}]")
                res = self._try_all_dictionaries(ex, tf, ext, boost, start_time, use_rules=use_rules)
                if res: return self.finished.emit("Success", res)
            else:
                self.log_signal.emit("Phase 1: Dictionary Scan (Skipped)")
            
            # Phase 2: Brute Force fallback
            cs = self.settings.get("char_set")
            if cs:
                self.log_signal.emit(f"Phase 2: Brute Force ({cs})")
                min_len = self.settings.get("min_len", 1)
                max_len = self.settings.get("max_len", 6)
                res = self._run_brute(ex, tf, cs, ext, boost, start_time, min_len=min_len, max_len=max_len)
                if res: return self.finished.emit("Success", res)
            else:
                self.log_signal.emit("Phase 2: Brute Force (Skipped)")
                
        elif self.mode == "markov":
            self.log_signal.emit("Unlocking with Markov AI (Human Guessing)...")
            res = self._run_markov(ex, tf, ext, boost, start_time)
            if res: return self.finished.emit("Success", res)
            
        elif self.mode == "keyboard":
            self.log_signal.emit("Unlocking with Keyboard Walk Patterns...")
            res = self._run_keyboard_walk(ex, tf, ext, boost, start_time)
            if res: return self.finished.emit("Success", res)

        elif self.mode == "mask":
            self.log_signal.emit(f"Unlocking with Mask: {self.settings.get('mask', '')}")
            mask = self.settings.get("mask", "")
            res = self._run_mask(ex, tf, mask, ext, boost, start_time)
            if res: return self.finished.emit("Success", res)
        elif self.mode == "passphrase":
            self.log_signal.emit("Unlocking with Passphrase Combinations...")
            res = self._run_passphrase(ex, tf, ext, boost, start_time)
            if res: return self.finished.emit("Success", res)
            
        elif self.mode == "hybrid":
            self.log_signal.emit("Unlocking with Hybrid Attack (Dict + Brute)...")
            res = self._run_hybrid(ex, tf, ext, boost, start_time)
            if res: return self.finished.emit("Success", res)
            
        elif self.mode == "hashcat":
            self.log_signal.emit("Unlocking with Hashcat Backend...")
            res = self._run_hashcat(ex, tf, ext, boost, start_time)
            if res: return self.finished.emit("Success", res)
            
        elif self.mode == "cluster":
            self.log_signal.emit("Unlocking with Distributed Cluster Mode...")
            res = self._run_cluster(ex, tf, ext, boost, start_time)
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
                min_len = self.settings.get("min_len", 1)
                max_len = self.settings.get("max_len", 12)
                res = self._run_brute(ex, tf, cs, ext, boost, start_time, min_len=min_len, max_len=max_len)
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
        batch_size = base_batch * 2 if boost else base_batch
        
        # Feature 5: Smart Ordering (Frequency sort)
        freq_order = "etaoinshrdlcumwfgypbvkjxqzETAOINSHRDLCUMWFGYPBVKJXQZ0123456789"
        cs = "".join(sorted(cs, key=lambda c: freq_order.find(c) if c in freq_order else 999))
        
        # Feature 3: Resume Session
        state_file = tf + ".state"
        saved_len = 1
        saved_idx = 0
        if self.settings.get("resume", False) and os.path.exists(state_file):
            try:
                with open(state_file, "r") as f:
                    state = json.load(f)
                    saved_len = state.get("length", 1)
                    saved_idx = state.get("index", 0)
                self.log_signal.emit(f"Resuming from length {saved_len}, index {saved_idx}")
            except: pass
            
        for length in range(min_len, max_len + 1):
            if length < saved_len: continue
            
            batch = []
            current_idx = 0
            
            # Use islice to skip items if resuming this length
            gen = itertools.product(cs, repeat=length)
            if length == saved_len and saved_idx > 0:
                gen = itertools.islice(gen, saved_idx, None)
                current_idx = saved_idx
                
            for combo in gen:
                if self.stop_event.is_set(): 
                    # Save state on stop
                    try:
                        with open(state_file, "w") as f:
                            json.dump({"length": length, "index": current_idx}, f)
                    except: pass
                    return None
                    
                batch.append("".join(combo))
                current_idx += 1
                
                if len(batch) >= batch_size:
                    res = self.run_ex_check(ex, tf, batch, ext, boost, start_time)
                    if res: 
                        # Success! Delete state file
                        if os.path.exists(state_file): os.remove(state_file)
                        return res
                    batch = []
                    
                    # Periodically save state even if not stopped
                    if current_idx % (batch_size * 10) == 0:
                        try:
                            with open(state_file, "w") as f:
                                json.dump({"length": length, "index": current_idx}, f)
                        except: pass
                        
            if batch:
                res = self.run_ex_check(ex, tf, batch, ext, boost, start_time)
                if res: 
                    if os.path.exists(state_file): os.remove(state_file)
                    return res
                
            # Reset saved_idx for next lengths
            saved_idx = 0
            
        # If we exhausted everything, delete state file
        if os.path.exists(state_file): os.remove(state_file)
        return None

    def _run_markov(self, ex, tf, ext, boost, start_time):
        # Simple 1st order Markov chain based on common bigrams
        bigrams = {
            't': 'heo', 'h': 'eai', 'e': 'rns', 'a': 'ntr',
            'i': 'nst', 'n': 'dge', 'o': 'nur', 's': 'the'
        }
        charset = "etaoinshrdlcumwfgypbvkjxqz" # Default fallback
        
        min_len = self.settings.get("min_len", 4)
        max_len = self.settings.get("max_len", 8)
        
        batch = []
        base_batch = 500 if ext in ['.docx', '.xlsx', '.pptx'] else 10000
        batch_size = base_batch * 2 if boost else base_batch
        
        def gen_markov(current_word, length):
            if len(current_word) == length:
                yield current_word
                return
                
            last_char = current_word[-1] if current_word else None
            choices = bigrams.get(last_char, charset) if last_char else charset
            
            for c in choices:
                yield from gen_markov(current_word + c, length)
                
        for length in range(min_len, max_len + 1):
            for pwd in gen_markov("", length):
                if self.stop_event.is_set(): return None
                batch.append(pwd)
                if len(batch) >= batch_size:
                    res = self.run_ex_check(ex, tf, batch, ext, boost, start_time)
                    if res: return res
                    batch = []
            if batch:
                res = self.run_ex_check(ex, tf, batch, ext, boost, start_time)
                if res: return res
                batch = []
                
        return None

    def _run_keyboard_walk(self, ex, tf, ext, boost, start_time):
        paths = [
            "qwertyuiop", "asdfghjkl", "zxcvbnm",
            "1234567890",
            "1qaz", "2wsx", "3edc", "4rfv", "5tgb", "6yhn", "7ujm", "8ik", "9ol", "0p"
        ]
        
        batch = []
        base_batch = 500 if ext in ['.docx', '.xlsx', '.pptx'] else 10000
        batch_size = base_batch * 2 if boost else base_batch
        
        for path in paths:
            for length in range(3, len(path) + 1):
                for i in range(len(path) - length + 1):
                    sub = path[i:i+length]
                    batch.append(sub)
                    batch.append(sub[::-1]) # Reverse
                    
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
            try:
                fut = ex.submit(check_batch, tf, ch, ext, boost)
                future_to_size[fut] = len(ch)
            except Exception as e:
                self.log_signal.emit(f"Process pool error: {e}")
                return None
            
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

    def _extract_metadata(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        terms = set()
        
        try:
            if ext == '.pdf':
                try:
                    with pikepdf.open(file_path) as pdf:
                        info = pdf.docinfo
                        for k, v in info.items():
                            val_str = str(v)
                            if val_str:
                                import re
                                words = re.split(r'\W+', val_str)
                                terms.update([w for w in words if len(w) > 2])
                except:
                    pass
            elif ext in ['.docx', '.xlsx', '.pptx']:
                pass
        except Exception as e:
            self.log_signal.emit(f"Metadata extraction failed: {e}")
            
        return list(terms)

    def _run_passphrase(self, ex, tf, ext, boost, start_time):
        words = []
        d_dirs = [get_external_path("dictionaries")]
        for d_dir in d_dirs:
            if os.path.exists(d_dir):
                dicts = [os.path.join(d_dir, f) for f in os.listdir(d_dir) if f.endswith(".txt")]
                if dicts:
                    with open(dicts[0], "r", encoding="utf-8", errors="ignore") as f:
                        words = [line.strip() for line in f if line.strip()]
                    break
        
        if not words:
            self.log_signal.emit("No dictionary found for passphrase attack.")
            return None
            
        if len(words) > 1000:
            words = words[:1000]
            
        batch = []
        batch_size = 1000 if ext in ['.docx', '.xlsx', '.pptx'] else 20000
        
        self.log_signal.emit(f"Passphrase mode: Using top {len(words)} words to generate combinations.")
        
        for w1 in words:
            for w2 in words:
                if self.stop_event.is_set(): return None
                batch.append(w1 + w2)
                batch.append(w1 + "-" + w2)
                batch.append(w1 + "_" + w2)
                
                if len(batch) >= batch_size:
                    res = self.run_ex_check(ex, tf, batch, ext, boost, start_time)
                    if res: return res
                    batch = []
                    
        if batch:
            res = self.run_ex_check(ex, tf, batch, ext, boost, start_time)
            if res: return res
            
        return None

    def _run_hybrid(self, ex, tf, ext, boost, start_time):
        words = []
        d_dirs = [get_external_path("dictionaries")]
        for d_dir in d_dirs:
            if os.path.exists(d_dir):
                dicts = [os.path.join(d_dir, f) for f in os.listdir(d_dir) if f.endswith(".txt")]
                if dicts:
                    with open(dicts[0], "r", encoding="utf-8", errors="ignore") as f:
                        words = [line.strip() for line in f if line.strip()]
                    break
        
        if not words:
            self.log_signal.emit("No dictionary found for hybrid attack.")
            return None
            
        if len(words) > 5000:
            words = words[:5000]
            
        cs = "0123456789"
        batch = []
        batch_size = 1000 if ext in ['.docx', '.xlsx', '.pptx'] else 20000
        
        self.log_signal.emit(f"Hybrid mode: Using top {len(words)} words + up to 3 digits.")
        
        for word in words:
            for i in range(1, 4):
                for p in itertools.product(cs, repeat=i):
                    if self.stop_event.is_set(): return None
                    batch.append(word + "".join(p))
                    if len(batch) >= batch_size:
                        res = self.run_ex_check(ex, tf, batch, ext, boost, start_time)
                        if res: return res
                        batch = []
                        
        if batch:
            res = self.run_ex_check(ex, tf, batch, ext, boost, start_time)
            if res: return res
            
        return None

    def _run_hashcat(self, ex, tf, ext, boost, start_time):
        self.log_signal.emit("Hashcat Backend Mode initiated.")
        self.log_signal.emit("Step 1: Determining Hashcat mode...")
        
        mode_map = {
            ".pdf": "10500 (PDF 1.4-1.6) or 10700 (PDF 1.7)",
            ".zip": "17200 (Legacy ZIP) or 13600 (WinZip AES)",
            ".docx": "9400 (Office 2010) or 9500 (Office 2013)",
            ".xlsx": "9400 (Office 2010) or 9500 (Office 2013)",
            ".pptx": "9400 (Office 2010) or 9500 (Office 2013)"
        }
        
        hc_mode = mode_map.get(ext, "Unknown")
        self.log_signal.emit(f"Suggested Hashcat Mode for {ext}: {hc_mode}")
        
        self.log_signal.emit("Step 2: Checking for Hashcat installation...")
        
        import shutil
        if shutil.which("hashcat"):
            self.log_signal.emit("Hashcat detected! You can run it directly.")
            self.log_signal.emit(f"Example command: hashcat -m {hc_mode.split(' ')[0]} hash.txt rockyou.txt")
        else:
            self.log_signal.emit("Hashcat NOT found on this system.")
            self.log_signal.emit("Please install Hashcat to use this high-speed mode.")
            
        return None

    def _run_cluster(self, ex, tf, ext, boost, start_time):
        self.log_signal.emit("Distributed Cluster Mode initiated.")
        self.log_signal.emit("Starting master node on port 9999...")
        self.log_signal.emit("Waiting for worker nodes to connect...")
        self.log_signal.emit("Feature skeleton active. Real network distribution requires further configuration.")
        return None

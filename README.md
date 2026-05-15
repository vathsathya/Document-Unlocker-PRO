# Document Unlocker PRO

A high-performance, cross-platform document password recovery tool built with Python 3 and PyQt6. Featuring an intelligent recovery engine with hybrid CPU/GPU acceleration.

## Features

- **Multi-Mode Recovery**:
  - **Smart Recovery**: Automatic chain attack starting with common dictionaries and moving to numeric brute-force.
  - **Brute Force**: Exhaustive search with multiple complexity levels (Numeric, Alphanumeric, Markov, Keyboard Walk, etc.).
  - **Mask Attack**: Custom pattern matching (e.g., `Pass?d?d?d` for a known prefix and 3 digits).
  - **Rule-Based Attack**: Hybrid rule engine applying leet speak, years, and capitalization variations to base keywords.
- **High Performance**: Pure Python engine with multi-core CPU support and hardware-accelerated GPU utilization via PyOpenCL.
- **Hardware Telemetry**: Real-time monitoring of speed (passwords per second) and resource utilization.
- **Localization**: Full interface support for **English** and **Khmer**.
- **Modern UI**: Sleek, responsive interface with Dark and Light mode support.
- **Security First**: 100% local processing with zero external data transmission.

## Technology Stack

- **UI Framework**: PyQt6
- **Acceleration**: PyOpenCL (GPU), Numba (JIT), ProcessPool (CPU)
- **Crypto & Formats**: `msoffcrypto-tool` (Office), `pikepdf` (PDF), `cryptography`
- **Core**: Python 3.14+

## Installation & Setup

### 1. Prerequisites
- **Python 3.14+**
- **Hardware Drivers**: For GPU acceleration, install OpenCL drivers:
  - **Linux**: `sudo apt install intel-opencl-icd` (Intel) or `nvidia-opencl-icd` (NVIDIA).
  - **Windows/macOS**: Usually included with standard GPU drivers.

### 2. Setup Commands

#### 🐧 Linux
```bash
git clone https://github.com/vathsathya/Document-Unlocker-PRO.git
cd Document-Unlocker-PRO
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

#### 🪟 Windows
```powershell
git clone https://github.com/vathsathya/Document-Unlocker-PRO.git
cd Document-Unlocker-PRO
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

#### 🍎 macOS
```bash
git clone https://github.com/vathsathya/Document-Unlocker-PRO.git
cd Document-Unlocker-PRO
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

## How to Use

### Dashboard (Default)
Select a protected document and click **Smart Recovery** for the most efficient automated attack. You can also manually configure the attack complexity and enable **Smart Boost** for maximum performance.

### Custom Masks
If you remember parts of the password, use the **Patterns** tab.
- `?d`: Digit (0-9)
- `?l`: Lowercase (a-z)
- `?u`: Uppercase (A-Z)
- `?s`: Symbols
- `?a`: All characters

### Smart Rules
Enter a base keyword or hint in the **Rules** tab to generate intelligent variations (e.g., adding numbers, replacing letters with numbers).

### Dictionary Attack
Load a custom wordlist in the **Dictionary** tab. Enable **Hybrid Mode** to apply smart rules to the dictionary words.

## License

MIT License

# Document Unlocker PRO

A high-performance, cross-platform document password recovery tool built with Python 3 and PyQt6.

## Features
- **High Performance**: Pure Python engine with multi-core CPU and hardware-accelerated GPU support (Intel Arc, NVIDIA, AMD).
- **Smart Recovery**: Intelligent pattern matching and dictionary-based attacks.
- **Wide Format Support**: Recover passwords for Office (.docx, .xlsx, .pptx), PDF, and Archives (.zip, .rar, .7z).
- **Modern UI**: Sleek, responsive interface with real-time hardware telemetry and dark mode support.
- **Security First**: 100% local processing with zero external data transmission.

## Technology Stack
- **Backend**: Python 3.14+
- **UI Framework**: PyQt6
- **Acceleration**: PyOpenCL (GPU), Numba (JIT), ProcessPool (CPU)
- **Crypto Libraries**: msoffcrypto-tool, pikepdf, cryptography

## Installation & Setup

### 1. Prerequisites
- **Python 3.14+**: Ensure Python is installed and added to your PATH.
- **Hardware Drivers**: For GPU acceleration, install the appropriate OpenCL drivers:
  - **Linux**: `sudo apt install intel-opencl-icd` (Intel) or `nvidia-opencl-icd` (NVIDIA).
  - **Windows/macOS**: Drivers are usually included with the standard GPU driver package.

### 2. Platform-Specific Setup

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

## Development & Build
To generate a standalone executable for your current platform:
```bash
python3 build.py
```
The resulting binary will be available in the `dist/` directory.

## License
MIT License

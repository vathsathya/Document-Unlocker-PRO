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

## Installation
1. Clone the repository.
2. Create a virtual environment: `python3 -m venv .venv`
3. Install dependencies: `./.venv/bin/pip install -r requirements.txt` (or run `build.py`)

## Development & Build
To build the standalone executable:
```bash
python3 build.py
```

## License
MIT License

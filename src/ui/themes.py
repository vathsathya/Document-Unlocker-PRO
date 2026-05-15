def get_qss(theme_name, lang="en"):
    themes = {
        "dark": {
            "bg": "#020617",
            "surface": "#0f172a",
            "surface_light": "#1e293b",
            "fg": "#f8fafc",
            "fg_dim": "#94a3b8",
            "accent": "#38bdf8",
            "accent_glow": "rgba(56, 189, 248, 0.15)",
            "border": "#334155",
            "error": "#ef4444"
        },
        "light": {
            "bg": "#f8fafc",
            "surface": "#ffffff",
            "surface_light": "#f1f5f9",
            "fg": "#0f172a",
            "fg_dim": "#64748b",
            "accent": "#0ea5e9",
            "accent_glow": "rgba(14, 165, 233, 0.1)",
            "border": "#e2e8f0",
            "error": "#dc2626"
        }
    }
    c = themes[theme_name]
    
    # Khmer fonts often appear smaller at the same point size
    # We increase the size and set specific Khmer font families
    is_km = lang == "km"
    font_family = "'Kantumruy Pro', 'Hanuman', 'Khmer OS Battambang', 'Segoe UI', system-ui, sans-serif" if is_km else "'Segoe UI', system-ui, -apple-system, sans-serif"
    
    fs_title = "36px" if is_km else "32px"
    fs_base = "16px" if is_km else "14px"
    fs_small = "15px" if is_km else "13px"
    fs_btn_accent = "18px" if is_km else "16px"
    
    return f"""
    QMainWindow, QWidget {{ 
        background-color: {c["bg"]}; 
        color: {c["fg"]}; 
        font-family: {font_family}; 
        font-size: {fs_base};
    }}
    
    QLabel#title {{ 
        font-size: {fs_title}; 
        font-weight: 800; 
        color: {c["accent"]}; 
        background: transparent;
    }}
    
    QLabel#subtitle {{ 
        color: {c["fg_dim"]}; 
        font-size: {fs_base}; 
        font-weight: 500; 
    }}
    
    QLabel#checkLabel {{
        font-size: {fs_small};
    }}
    
    QFrame#card {{ 
        background: {c["surface"]}; 
        border: 1px solid {c["border"]};
        border-radius: 16px; 
    }}
    
    QLineEdit {{ 
        background: {c["surface_light"]}; 
        border: 1px solid {c["border"]}; 
        padding: 14px; 
        border-radius: 10px; 
        font-size: {fs_base};
        color: {c["fg"]};
    }}
    QLineEdit:focus {{ 
        border: 1px solid {c["accent"]}; 
        background: {c["bg"]};
    }}
    
    QPushButton {{ 
        background: {c["surface_light"]}; 
        border: 1px solid {c["border"]}; 
        padding: 12px 24px; 
        border-radius: 10px; 
        font-weight: 600; 
        font-size: {fs_base};
    }}
    QPushButton:hover {{ 
        background: {c["border"]}; 
    }}
    
    QPushButton#accentBtn {{ 
        background: {c["accent"]}; 
        color: {c["bg"]}; 
        border: none; 
        font-weight: 800;
        font-size: {fs_btn_accent};
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    QPushButton#accentBtn:hover {{ 
        background: #7dd3fc;
    }}
    
    QPushButton#stopBtn {{ 
        background: {c["error"]}; 
        color: white; 
        border: none; 
    }}
    
    QGroupBox {{ 
        font-weight: 700; 
        color: {c["accent"]}; 
        border: 1px solid {c["border"]}; 
        border-radius: 12px; 
        margin-top: 20px; 
        padding-top: 25px;
    }}
    QGroupBox::title {{ 
        subcontrol-origin: margin; 
        left: 15px; 
        padding: 0 10px; 
    }}
    
    QPlainTextEdit {{ 
        background: {c["bg"]}; 
        border: 1px solid {c["border"]}; 
        border-radius: 12px; 
        padding: 12px; 
        font-family: 'Cascadia Code', 'Consolas', monospace;
        font-size: {fs_small};
        color: {c["accent"]};
    }}
    
    QProgressBar {{ 
        background: {c["surface_light"]}; 
        border: none; 
        border-radius: 3px; 
        height: 6px;
    }}
    QProgressBar::chunk {{ 
        background: {c["accent"]}; 
        border-radius: 3px;
    }}
    
    QScrollBar:vertical {{
        border: none;
        background: transparent;
        width: 8px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {c["border"]};
        min-height: 20px;
        border-radius: 4px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    """


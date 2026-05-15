def get_qss(theme_name, lang="en"):
    themes = {
        "dark": {
            "bg": "#09090b",
            "surface": "#121214",
            "surface_light": "#1a1a1e",
            "fg": "#fafafa",
            "fg_dim": "#a1a1aa",
            "accent": "#8b5cf6",
            "accent_glow": "rgba(139, 92, 246, 0.15)",
            "border": "#27272a",
            "error": "#ef4444",
            "gradient_start": "#8b5cf6",
            "gradient_end": "#06b6d4"
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
            "error": "#dc2626",
            "gradient_start": "#0ea5e9",
            "gradient_end": "#2563eb"
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
    QMainWindow {{ 
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {c["bg"]}, stop:1 {c["surface"]}); 
        color: {c["fg"]}; 
        font-family: {font_family}; 
        font-size: {fs_base};
    }}
    
    QDialog {{
        background: {c["bg"]};
        color: {c["fg"]}; 
        font-family: {font_family}; 
        font-size: {fs_base};
    }}
    
    QWidget {{
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
        color: {c["fg_dim"]};
    }}
    
    QFrame#advancedFrame {{
        background: {c["surface_light"]};
        border: 1px solid {c["border"]};
        border-radius: 0px;
        padding: 15px;
    }}
    
    QTabWidget::pane {{
        border: 1px solid {c["border"]};
        background: {c["surface"]};
        border-radius: 0px;
        top: -1px;
    }}
    
    QTabBar::tab {{
        background: {c["surface_light"]};
        border: 1px solid {c["border"]};
        border-bottom-color: transparent;
        border-radius: 0px;
        padding: 10px 20px;
        font-weight: 600;
        color: {c["fg_dim"]};
        margin-right: 2px;
    }}
    
    QTabBar::tab:hover {{
        background: {c["border"]};
        color: {c["fg"]};
    }}
    
    QTabBar::tab:selected {{
        background: {c["surface"]};
        border-color: {c["border"]};
        border-bottom: 3px solid {c["accent"]};
        color: {c["accent"]};
    }}
    
    QFrame#card {{ 
        background: {c["surface"]}; 
        border: 1px solid {c["border"]};
        border-radius: 0px; 
    }}
    
    QLineEdit, QSpinBox, QComboBox {{ 
        background: {c["surface_light"]}; 
        border: 1px solid {c["border"]}; 
        height: 48px;
        padding: 0 14px;
        border-radius: 0px; 
        font-size: {fs_base};
        color: {c["fg"]};
    }}
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{ 
        border: 1px solid {c["accent"]}; 
        background: {c["surface"]};
    }}
    
    QComboBox QAbstractItemView {{
        background: {c["surface"]};
        color: {c["fg"]};
        border: 1px solid {c["border"]};
        selection-background-color: {c["accent"]};
        selection-color: white;
    }}
    
    QPushButton {{ 
        background: {c["surface_light"]}; 
        border: 1px solid {c["border"]}; 
        height: 48px;
        padding: 0 24px;
        border-radius: 0px; 
        font-weight: 600; 
        font-size: {fs_base};
        color: {c["fg"]};
    }}
    QPushButton:hover {{ 
        background: {c["border"]}; 
    }}
    
    QPushButton#accentBtn {{ 
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {c["gradient_start"]}, stop:1 {c["gradient_end"]}); 
        color: white; 
        border: none; 
        border-radius: 0px; 
        font-weight: 800;
        font-size: {fs_btn_accent};
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    QPushButton#accentBtn:hover {{ 
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {c["gradient_end"]}, stop:1 {c["gradient_start"]}); 
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
        border-radius: 0px; 
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
        border-radius: 0px; 
        padding: 12px; 
        font-family: 'Cascadia Code', 'Consolas', monospace;
        font-size: {fs_small};
        color: {c["accent"]};
    }}
    
    QMenu {{
        background-color: {c["surface"]};
        color: {c["fg"]};
        border: 1px solid {c["border"]};
    }}
    QMenu::item {{
        background-color: transparent;
        padding: 6px 24px;
    }}
    QMenu::item:selected {{
        background-color: {c["accent"]};
        color: white;
    }}
    
    QProgressBar {{ 
        background: {c["surface_light"]}; 
        border: none; 
        border-radius: 0px; 
        height: 6px;
    }}
    QProgressBar::chunk {{ 
        background: {c["accent"]}; 
        border-radius: 0px;
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
        border-radius: 0px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    """


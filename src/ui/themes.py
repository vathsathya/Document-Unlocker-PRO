from PyQt6.QtGui import QColor

THEMES = {
    "dark": {
        "bg": "#0f172a",
        "fg": "#f8fafc",
        "accent": "#38bdf8",
        "accent_hover": "#0ea5e9",
        "surface": "#1e293b",
        "surface_light": "#334155",
        "border": "#475569"
    },
    "light": {
        "bg": "#f8fafc",
        "fg": "#0f172a",
        "accent": "#0ea5e9",
        "accent_hover": "#0284c7",
        "surface": "#ffffff",
        "surface_light": "#f1f5f9",
        "border": "#cbd5e1"
    }
}

def get_qss(theme_name):
    c = THEMES[theme_name]
    return f"""
    QMainWindow, QWidget {{ background-color: {c["bg"]}; color: {c["fg"]}; font-family: 'Inter', 'Roboto', 'Segoe UI', 'Arial', 'Khmer OS', sans-serif; }}
    QLabel#title {{ font-size: 24px; font-weight: 800; color: {c["accent"]}; }}
    QTabWidget::pane {{ border: 1px solid {c["border"]}; background: {c["bg"]}; }}
    QTabBar::tab {{ background: {c["surface"]}; padding: 12px 25px; margin-right: 2px; }}
    QTabBar::tab:selected {{ background: {c["bg"]}; border-bottom: 2px solid {c["accent"]}; color: {c["accent"]}; }}
    QLineEdit, QComboBox, QTextEdit, QSpinBox {{ background: {c["surface"]}; border: 1px solid {c["border"]}; padding: 10px; border-radius: 6px; }}
    QPushButton {{ background: {c["surface"]}; border: 1px solid {c["border"]}; padding: 12px; border-radius: 6px; font-weight: bold; }}
    QPushButton#accentBtn {{ background: {c["accent"]}; color: #000; border: none; }}
    QPushButton#accentBtn:hover {{ background: {c["accent_hover"]}; }}
    QFrame#card {{ background: {c["surface"]}; border-radius: 10px; padding: 15px; border: 1px solid {c["border"]}; }}
    
    QCheckBox {{ spacing: 8px; font-weight: 500; color: {c["fg"]}; }}
    QCheckBox::indicator {{ width: 20px; height: 20px; border-radius: 4px; border: 2px solid {c["border"]}; background: {c["surface"]}; }}
    QCheckBox::indicator:checked {{ background: {c["accent"]}; border-color: {c["accent"]}; }}
    QCheckBox::indicator:unchecked:hover {{ border-color: {c["accent"]}; }}
    """

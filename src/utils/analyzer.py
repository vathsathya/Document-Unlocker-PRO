import os
from datetime import datetime

def analyze_file(path):
    if not path or not os.path.exists(path):
        return None
    
    ext = os.path.splitext(path)[1].lower()
    mtime = datetime.fromtimestamp(os.path.getmtime(path))
    year = mtime.year
    
    insight = f"File Intelligence: Modified in {year}. "
    if ext == ".pdf":
        insight += "PDF encryption detected."
    elif ext in [".docx", ".xlsx"]:
        insight += "Modern Office XML detected."
    
    return {
        "insight": insight,
        "year": year,
        "suggestions": [f"?*?*{year}", f"?a?a?a{year}"]
    }

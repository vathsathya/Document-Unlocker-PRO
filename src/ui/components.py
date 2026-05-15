from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QLinearGradient
from .themes import THEMES

class NeonGraph(QWidget):
    def __init__(self, parent, theme):
        super().__init__(parent)
        self.theme = theme
        self.data = [0] * 60
        self.max_val = 100
        self.setFixedHeight(120)

    def update_data(self, val):
        self.data.append(val)
        self.data.pop(0)
        self.max_val = max(max(self.data), 10)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = THEMES[self.theme]
        w, h = self.width(), self.height()
        
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(c["surface"])))
        p.drawRoundedRect(0, 0, w, h, 10, 10)
        
        if w < 20: return
        step = w / (len(self.data) - 1)
        points = []
        for i, v in enumerate(self.data):
            x = i * step
            y = h - (v / self.max_val * (h * 0.7)) - 10
            points.append((x, y))
            
        grad = QLinearGradient(0, 0, 0, h)
        acc = QColor(c["accent"])
        grad.setColorAt(0, acc)
        grad.setColorAt(1, QColor(0,0,0,0))
        
        p.setBrush(QBrush(grad))
        p.setOpacity(0.4)
        p.drawPolygon([QPointF(x, y) for x, y in ([(0, h)] + points + [(w, h)])])
        
        p.setOpacity(1.0)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(acc, 2))
        for i in range(len(points)-1):
            p.drawLine(int(points[i][0]), int(points[i][1]), int(points[i+1][0]), int(points[i+1][1]))

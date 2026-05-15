from PyQt6.QtWidgets import QWidget, QCheckBox
from PyQt6.QtCore import Qt, QPointF, QPropertyAnimation, pyqtProperty, QRect, QEasingCurve
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QLinearGradient

class ToggleSwitch(QCheckBox):
    def __init__(self, parent=None, bg_color="#1e293b", circle_color="#94a3b8", active_color="#38bdf8", text=""):
        super().__init__(text, parent)
        self.setFixedSize(60, 28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._position = 4
        
        self.bg_color = bg_color
        self.circle_color = circle_color
        self.active_color = active_color

        self.animation = QPropertyAnimation(self, b"position")
        self.animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        self.animation.setDuration(150)
        
        self.stateChanged.connect(self.setup_animation)

    @pyqtProperty(float)
    def position(self):
        return self._position

    @position.setter
    def position(self, pos):
        self._position = pos
        self.update()

    def setup_animation(self, value):
        self.animation.stop()
        if value:
            self.animation.setEndValue(self.width() - 24)
        else:
            self.animation.setEndValue(4)
        self.animation.start()

    def hitButton(self, pos):
        return self.contentsRect().contains(pos)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        p.setPen(Qt.PenStyle.NoPen)
        if self.isChecked():
            p.setBrush(QColor(self.active_color))
        else:
            p.setBrush(QColor(self.bg_color))
        p.drawRoundedRect(0, 0, self.width(), self.height(), 14, 14)

        # Handle
        p.setBrush(QColor(self.circle_color if not self.isChecked() else "#ffffff"))
        p.drawEllipse(int(self._position), 4, 20, 20)
        p.end()

class ModernCheckBox(QWidget):
    """A wrapper to hold the toggle switch and label side-by-side"""
    def __init__(self, text, parent=None):
        super().__init__(parent)
        from PyQt6.QtWidgets import QHBoxLayout, QLabel
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)
        
        self.toggle = ToggleSwitch()
        self.label = QLabel(text)
        self.label.setObjectName("checkLabel")
        self.label.setStyleSheet("color: #94a3b8; font-weight: 500;")
        
        self.layout.addWidget(self.toggle)
        self.layout.addWidget(self.label)
        self.layout.addStretch()

    def setChecked(self, value):
        self.toggle.setChecked(value)

    def isChecked(self):
        return self.toggle.isChecked()

    def setText(self, text):
        self.label.setText(text)

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QDialog, QLabel, 
    QLineEdit, QPushButton, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QColor, QPainter, QLinearGradient, QPen

class CP_SVBox(QWidget):
    colorChanged = Signal(float, float)
    
    def __init__(self):
        super().__init__()
        self.setFixedSize(200, 200)
        self.hue = 0.0
        self.sat = 0.0
        self.val = 1.0
        self.setCursor(Qt.CrossCursor)
    
    def set_hue(self, h):
        self.hue = h
        self.update()
    
    def set_sv(self, s, v):
        self.sat = s
        self.val = v
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False) # Crisp edges
        
        # Base Hue
        base = QColor.fromHsvF(self.hue, 1.0, 1.0)
        painter.fillRect(self.rect(), base)
        
        # Saturation (White -> Transparent)
        grad_sat = QLinearGradient(0, 0, self.width(), 0)
        grad_sat.setColorAt(0, QColor(255, 255, 255))
        grad_sat.setColorAt(1, QColor(255, 255, 255, 0))
        painter.fillRect(self.rect(), grad_sat)
        
        # Value (Transparent -> Black)
        grad_val = QLinearGradient(0, 0, 0, self.height())
        grad_val.setColorAt(0, QColor(0, 0, 0, 0))
        grad_val.setColorAt(1, QColor(0, 0, 0))
        painter.fillRect(self.rect(), grad_val)
        
        # Handle - Simple Square or Crosshair
        x = self.sat * self.width()
        y = (1.0 - self.val) * self.height()
        
        painter.setPen(QPen(Qt.black, 1))
        painter.drawRect(int(x)-3, int(y)-3, 6, 6)
        painter.setPen(QPen(Qt.white, 1))
        painter.drawRect(int(x)-2, int(y)-2, 4, 4)
    
    def mousePressEvent(self, event):
        self._update_from_mouse(event.pos())
    
    def mouseMoveEvent(self, event):
        self._update_from_mouse(event.pos())
    
    def _update_from_mouse(self, pos):
        x = max(0, min(self.width(), pos.x()))
        y = max(0, min(self.height(), pos.y()))
        self.sat = x / self.width()
        self.val = 1.0 - (y / self.height())
        self.update()
        self.colorChanged.emit(self.sat, self.val)


class CP_HueSlider(QWidget):
    hueChanged = Signal(float)
    
    def __init__(self):
        super().__init__()
        self.setFixedSize(20, 200)
        self.hue = 0.0
    
    def set_hue(self, h):
        self.hue = h
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        
        # Rainbow gradient
        grad = QLinearGradient(0, 0, 0, self.height())
        colors = [
            (0.00, QColor(255, 0, 0)),
            (0.17, QColor(255, 255, 0)),
            (0.33, QColor(0, 255, 0)),
            (0.50, QColor(0, 255, 255)),
            (0.67, QColor(0, 0, 255)),
            (0.83, QColor(255, 0, 255)),
            (1.00, QColor(255, 0, 0))
        ]
        for pos, col in colors:
            grad.setColorAt(pos, col)
        
        painter.fillRect(self.rect(), grad)
        
        # Handle
        y = self.hue * self.height()
        painter.setPen(Qt.white)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(0, int(y)-2, self.width()-1, 4)
    
    def mousePressEvent(self, event):
        self._update_mouse(event.pos())
    
    def mouseMoveEvent(self, event):
        self._update_mouse(event.pos())
    
    def _update_mouse(self, pos):
        y = max(0, min(self.height(), pos.y()))
        self.hue = y / self.height()
        self.update()
        self.hueChanged.emit(self.hue)


class CP_AlphaSlider(QWidget):
    alphaChanged = Signal(int)
    
    def __init__(self):
        super().__init__()
        self.setFixedHeight(16)
        self.alpha = 255
        self.fill_color = QColor(255, 0, 0)
    
    def set_color(self, c):
        self.fill_color = QColor(c)
        self.fill_color.setAlpha(255)
        self.update()
    
    def set_alpha(self, a):
        self.alpha = int(a)
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        
        # Checkerboard
        check_size = 8
        cols = self.width() // check_size + 1
        rows = self.height() // check_size + 1
        for r in range(rows):
            for c in range(cols):
                color = QColor(100, 100, 100) if (r + c) % 2 == 0 else QColor(60, 60, 60)
                painter.fillRect(c * check_size, r * check_size, check_size, check_size, color)
        
        # Alpha Gradient
        grad = QLinearGradient(0, 0, self.width(), 0)
        c0 = QColor(self.fill_color)
        c0.setAlpha(0)
        c1 = QColor(self.fill_color)
        c1.setAlpha(255)
        grad.setColorAt(0, c0)
        grad.setColorAt(1, c1)
        painter.fillRect(self.rect(), grad)
        
        # Handle
        x = (self.alpha / 255.0) * self.width()
        painter.setPen(Qt.white)
        painter.drawRect(int(x)-2, 0, 4, self.height()-1)
    
    def mousePressEvent(self, event):
        self._update_mouse(event.pos())
    
    def mouseMoveEvent(self, event):
        self._update_mouse(event.pos())
    
    def _update_mouse(self, pos):
        x = max(0, min(self.width(), pos.x()))
        self.alpha = int((x / self.width()) * 255)
        self.update()
        self.alphaChanged.emit(self.alpha)


class ModernColorPicker(QDialog):
    def __init__(self, initial_color=QColor(255, 255, 255), parent=None):
        super().__init__(parent)
        self.setWindowTitle("Color")
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setFixedSize(360, 240) # Compact size
        
        # Style matches app.py
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a1a;
                border: 1px solid #333;
            }
            QLabel {
                color: #b0b0b0;
                font-family: 'Segoe UI', sans-serif;
                font-size: 11px;
                background: transparent;
            }
            QLineEdit {
                background-color: #252525;
                color: #e0e0e0;
                border: 1px solid #333;
                padding: 4px;
                font-family: monospace;
            }
            QLineEdit:focus {
                border: 1px solid #555;
            }
            QPushButton {
                background-color: #2a2a2a;
                color: #b0b0b0;
                border: 1px solid #333;
                padding: 4px 12px;
            }
            QPushButton:hover {
                background-color: #333;
            }
            QPushButton:pressed {
                background-color: #222;
            }
        """)
        
        self.initial_color = initial_color
        self.color = initial_color
        self.h, self.s, self.v, self.a = self.color.getHsvF()
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # LEFT: Pickers
        self.sv_box = CP_SVBox()
        self.sv_box.set_hue(self.h)
        self.sv_box.set_sv(self.s, self.v)
        self.sv_box.colorChanged.connect(self.on_sv_changed)
        layout.addWidget(self.sv_box)
        
        self.hue_slider = CP_HueSlider()
        self.hue_slider.set_hue(self.h)
        self.hue_slider.hueChanged.connect(self.on_hue_changed)
        layout.addWidget(self.hue_slider)
        
        # RIGHT: Controls
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)
        
        # Alpha
        right_layout.addWidget(QLabel("Alpha"))
        self.alpha_slider = CP_AlphaSlider()
        self.alpha_slider.set_color(self.color)
        self.alpha_slider.set_alpha(self.a * 255)
        self.alpha_slider.alphaChanged.connect(self.on_alpha_changed)
        right_layout.addWidget(self.alpha_slider)
        
        # Hex
        right_layout.addWidget(QLabel("Hex"))
        self.hex_input = QLineEdit(self.color.name())
        self.hex_input.setAlignment(Qt.AlignCenter)
        self.hex_input.returnPressed.connect(self.on_hex_entered)
        right_layout.addWidget(self.hex_input)
        
        right_layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(4)
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.setCursor(Qt.PointingHandCursor)
        self.ok_btn.clicked.connect(self.accept)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        right_layout.addLayout(btn_layout)
        
        layout.addLayout(right_layout)

    def on_sv_changed(self, s, v):
        self.s = s
        self.v = v
        self._update_color()
    
    def on_hue_changed(self, h):
        self.h = h
        self.sv_box.set_hue(h)
        self._update_color()
    
    def on_alpha_changed(self, val):
        self.a = val / 255.0
        self._update_color()
    
    def on_hex_entered(self):
        text = self.hex_input.text()
        if QColor.isValidColor(text):
            self.color = QColor(text)
            self.h, self.s, self.v, self.a = self.color.getHsvF()
            self._update_ui_from_color()
    
    def _update_color(self):
        self.color = QColor.fromHsvF(self.h, self.s, self.v, self.a)
        self.alpha_slider.set_color(self.color)
        if not self.hex_input.hasFocus():
            self.hex_input.setText(self.color.name())
            
    def _update_ui_from_color(self):
        self.sv_box.blockSignals(True)
        self.hue_slider.blockSignals(True)
        self.alpha_slider.blockSignals(True)
        
        self.sv_box.set_hue(self.h)
        self.sv_box.set_sv(self.s, self.v)
        self.hue_slider.set_hue(self.h)
        self.alpha_slider.set_alpha(self.a * 255)
        self.alpha_slider.set_color(self.color)
        
        self.sv_box.blockSignals(False)
        self.hue_slider.blockSignals(False)
        self.alpha_slider.blockSignals(False)

    def get_color(self):
        return self.color
    
    @staticmethod
    def get_color_dialog(initial_color, parent=None):
        dlg = ModernColorPicker(initial_color, parent)
        if dlg.exec() == QDialog.Accepted:
            return dlg.get_color()
        return None
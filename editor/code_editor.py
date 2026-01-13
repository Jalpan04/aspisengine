from PySide6.QtWidgets import QPlainTextEdit, QWidget, QVBoxLayout, QFileDialog
from PySide6.QtCore import Qt, QRect, QSize, Signal
from PySide6.QtGui import QColor, QPainter, QTextFormat, QFont
from editor.syntax import PythonHighlighter

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.code_editor.lineNumberAreaPaintEvent(event)

class CodeEditor(QPlainTextEdit):
    file_saved = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_path = None
        
        # Font setup
        font = QFont("Consolas", 11)
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)
        
        # Setup line numbers
        self.line_number_area = LineNumberArea(self)

        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.update_line_number_area_width(0)
        self.highlight_current_line()
        
        # Syntax Highlight
        self.highlighter = PythonHighlighter(self.document())
        
        # Style
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
            }
        """)

    def line_number_area_width(self):
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def highlight_current_line(self):
        pass # Optional: Highlight current line background

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#252526"))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor("#858585"))
                painter.drawText(0, top, self.line_number_area.width() - 2, self.fontMetrics().height(),
                                 Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def keyPressEvent(self, event):
        # Indentation support
        if event.key() == Qt.Key_Tab:
            self.insertPlainText("    ")
            return
            
        # Smart Auto-Indent
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # Get current line
            cursor = self.textCursor()
            block = cursor.block()
            text = block.text()
            
            # Calculate indent
            indent = ""
            for char in text:
                if char == ' ':
                    indent += " "
                elif char == '\t':
                    indent += "    " # Normalize tabs
                else:
                    break
            
            # Increase indent if line ends with :
            if text.rstrip().endswith(":"):
                indent += "    "
            
            # Insert newline + indent
            super().keyPressEvent(event) # Inserts newline
            self.insertPlainText(indent)
            return

        # Save Shortcut
        if event.key() == Qt.Key_S and event.modifiers() == Qt.ControlModifier:
            if self.file_path:
                self.save_file()
            return
            
        super().keyPressEvent(event)

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            delta = event.angleDelta().y()
            font = self.font()
            size = font.pointSize()
            
            if delta > 0:
                size += 1
            else:
                size -= 1
                
            size = max(6, min(36, size)) # Clamp
            font.setPointSize(size)
            self.setFont(font)
            event.accept()
            return
            
        super().wheelEvent(event)

    def load_file(self, path):
        self.file_path = path
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.setPlainText(f.read())
        except Exception as e:
            print(f"Error loading file: {e}")

    def save_file(self):
        if not self.file_path: return
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(self.toPlainText())
            print(f"Saved: {self.file_path}")
            self.file_saved.emit(self.file_path)
        except Exception as e:
            print(f"Error saving file: {e}")

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame,
    QFormLayout, QLineEdit, QHBoxLayout, QPushButton, QFileDialog,
    QCheckBox, QMenu, QSlider, QSizePolicy, QGridLayout, QComboBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDoubleValidator
from editor.editor_state import EditorState
from editor.script_parser import ScriptParser
from editor.undo_redo import AddComponentCommand, ChangeComponentCommand, RemoveComponentCommand
from editor.theme import Theme
import os

class FloatField(QLineEdit):
    """Compact float input field."""
    value_edited = Signal(float)      # Live updates (preview)
    value_committed = Signal(float, float)   # Final update (new, old)
    
    def __init__(self, value=0.0, min_val=None, max_val=None):
        super().__init__()
        self.setValidator(QDoubleValidator())
        self.min_val = min_val
        self.max_val = max_val
        self.setMinimumWidth(60)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setText(f"{value:.2f}")
        self.textChanged.connect(self._on_text_changed)
        self.editingFinished.connect(self._on_editing_finished)
        self._last_committed_value = value
        
        # Context Menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
    
    def show_context_menu(self, pos):
        from PySide6.QtWidgets import QMenu, QApplication
        menu = QMenu(self)
        reset_action = menu.addAction("Reset to 0")
        reset_action.triggered.connect(lambda: self._force_commit(0.0))
        
        # Copy/Paste support could be added here
        
        menu.exec(self.mapToGlobal(pos))
        
    def _force_commit(self, val):
        self.set_value(val)
        self._on_editing_finished() # Trigger commit signal

    def _on_text_changed(self, text):
        try:
            val = float(text)
            self.value_edited.emit(val)
        except ValueError:
            pass

    def _on_editing_finished(self):
        try:
            val = float(self.text())
            
            # Validation
            if self.min_val is not None: val = max(self.min_val, val)
            if self.max_val is not None: val = min(self.max_val, val)
            
            # Use set_value to format text
            self.set_value(val)
                
            if val != self._last_committed_value:
                old_val = self._last_committed_value
                self._last_committed_value = val
                self.value_committed.emit(val, old_val)
        except ValueError:
            pass

    def set_value(self, v):
        self.blockSignals(True)
        self.setText(f"{v:.2f}")
        self._last_committed_value = v
        self.blockSignals(False)


class Vec2Field(QWidget):
    """X/Y input pair."""
    value_edited = Signal(float, float)
    value_committed = Signal(float, float, float, float) # new_x, new_y, old_x, old_y
    
    def __init__(self, x=0.0, y=0.0, labels=("X", "Y")):
        super().__init__()
        self.last_x = x
        self.last_y = y
        self.block_updates = False
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # X
        x_label = QLabel(labels[0])
        x_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: {Theme.FONT_TINY};")
        x_label.setFixedWidth(12)
        self.x_field = FloatField(x)

        # Y
        y_label = QLabel(labels[1])
        y_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: {Theme.FONT_TINY};")
        y_label.setFixedWidth(12)
        self.y_field = FloatField(y)

        layout.addWidget(x_label)
        layout.addWidget(self.x_field)
        layout.addWidget(y_label)
        layout.addWidget(self.y_field)
        
        # Forward signals
        self.x_field.value_edited.connect(lambda v: self._emit_edit())
        self.y_field.value_edited.connect(lambda v: self._emit_edit())
        
        # We handle commit manually to capture state
        self.x_field.value_committed.connect(lambda n, o: self._emit_commit())
        self.y_field.value_committed.connect(lambda n, o: self._emit_commit())
    
    def _emit_edit(self):
        try:
            x = float(self.x_field.text())
            y = float(self.y_field.text())
            self.value_edited.emit(x, y)
        except ValueError:
            pass

    def set_value(self, value):
        self.blockSignals(True)
        self.x_field.setText(f"{value[0]:.2f}")
        self.y_edit = self.y_field # ensure we access the field correctly
        self.y_field.setText(f"{value[1]:.2f}")
        self.last_x, self.last_y = value
        self.blockSignals(False)

    def _emit_commit(self):
        if self.block_updates: return
        try:
            x = float(self.x_field.text())
            y = float(self.y_field.text())
            
            if x != self.last_x or y != self.last_y:
                old_x, old_y = self.last_x, self.last_y
                self.last_x = x
                self.last_y = y
                self.value_committed.emit(x, y, old_x, old_y)
        except ValueError:
            pass

    def set_value(self, x, y):
        self.block_updates = True
        self.x_field.set_value(x)
        self.y_field.set_value(y)
        self.last_x = x
        self.last_y = y
        self.block_updates = False


class SliderFloatField(QWidget):
    """A beautiful combined QSlider + QLineEdit field for highly intuitive float control."""
    value_edited = Signal(float)
    value_committed = Signal(float)
    
    def __init__(self, value, min_val, max_val, step=0.01):
        super().__init__()
        self.min_val = min_val
        self.max_val = max_val
        self.step = step
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # The QSlider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, int((max_val - min_val) / step))
        self.slider.setValue(int((value - min_val) / step))

        # The Line Edit
        self.edit = FloatField(value, min_val, max_val)
        self.edit.setMinimumWidth(50)
        self.edit.setMaximumWidth(70)
        self.edit.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        layout.addWidget(self.slider)
        layout.addWidget(self.edit)
        self.setLayout(layout)
        
        # Connections
        self.slider.valueChanged.connect(self._on_slider_changed)
        self.slider.sliderReleased.connect(self._on_slider_released)
        self.edit.value_edited.connect(self._on_edit_edited)
        self.edit.value_committed.connect(self._on_edit_committed)
        
    def _on_slider_changed(self, val):
        float_val = self.min_val + val * self.step
        self.edit.blockSignals(True)
        self.edit.setText(f"{float_val:.2f}")
        self.edit.blockSignals(False)
        self.value_edited.emit(float_val)
        
    def _on_slider_released(self):
        float_val = self.min_val + self.slider.value() * self.step
        self.value_committed.emit(float_val)
        
    def _on_edit_edited(self, float_val):
        slider_val = int((float_val - self.min_val) / self.step)
        self.slider.blockSignals(True)
        self.slider.setValue(slider_val)
        self.slider.blockSignals(False)
        self.value_edited.emit(float_val)
        
    def _on_edit_committed(self, float_val, old_val):
        slider_val = int((float_val - self.min_val) / self.step)
        self.slider.blockSignals(True)
        self.slider.setValue(slider_val)
        self.slider.blockSignals(False)
        self.value_committed.emit(float_val)

class ColorField(QPushButton):
    """Button that shows color and opens picker."""
    value_changed = Signal(list)  # [r, g, b, a]

    def __init__(self, color_tuple=(255, 255, 255, 255)):
        super().__init__()
        self.setMinimumWidth(60)
        self.setFixedHeight(20)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        color_tuple = tuple(color_tuple)
        if len(color_tuple) == 3:
            color_tuple = color_tuple + (255,)
        self.color = color_tuple
        self._update_style()
        self.clicked.connect(self._pick_color)

    def _update_style(self):
        r, g, b, a = self.color
        self.setStyleSheet(
            f"background-color: rgba({r},{g},{b},{a/255.0:.2f}); "
            f"border: 1px solid {Theme.BORDER_DEFAULT};"
        )

    def _pick_color(self):
        from PySide6.QtGui import QColor
        from editor.color_picker import ModernColorPicker
        
        r, g, b, a = self.color
        cur = QColor(r, g, b, a)
        
        c = ModernColorPicker.get_color_dialog(cur, self)
        if c and c.isValid():
            self.color = (c.red(), c.green(), c.blue(), c.alpha())
            self._update_style()
            self.value_changed.emit(list(self.color))

    def set_value(self, c):
        c = tuple(c)
        if len(c) == 3:
            c = c + (255,)
        self.color = c
        self._update_style()


class BitmaskGrid(QWidget):
    value_changed = Signal(int)  # Emits the new integer mask (or selected layer index if single_select)
    
    def __init__(self, value=1, single_select=False):
        super().__init__()
        self.single_select = single_select
        self.block_updates = False
        
        if self.single_select:
            try:
                val_int = int(value)
            except (ValueError, TypeError):
                val_int = 1
            if val_int < 1:
                val_int = 1
            elif val_int > 32:
                val_int = 32
            self.value = val_int
        else:
            self.value = int(value) & 0xFFFFFFFF
        
        main_layout = QGridLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(6)  # Group spacing between blocks of 8
        
        self.buttons = {}  # bit_index (0-31) -> QPushButton
        
        # 4 blocks representing 8 bits each (2x4 grid)
        blocks_data = [
            # Block 1 (bits 0-7)
            ([1, 2, 3, 4], [5, 6, 7, 8]),
            # Block 2 (bits 8-15)
            ([9, 10, 11, 12], [13, 14, 15, 16]),
            # Block 3 (bits 16-23)
            ([17, 18, 19, 20], [21, 22, 23, 24]),
            # Block 4 (bits 24-31)
            ([25, 26, 27, 28], [29, 30, 31, 32]),
        ]
        
        for block_idx, (top_row, bottom_row) in enumerate(blocks_data):
            block_widget = QWidget()
            block_layout = QGridLayout(block_widget)
            block_layout.setContentsMargins(0, 0, 0, 0)
            block_layout.setSpacing(1)  # Tiny 1px spacing inside block
            
            # Top row buttons
            for col, num in enumerate(top_row):
                bit_idx = num - 1
                btn = QPushButton(str(num))
                btn.setFixedSize(16, 16)
                btn.setCheckable(True)
                btn.setToolTip(f"Layer {num}")
                btn.setObjectName("BitButton")
                block_layout.addWidget(btn, 0, col)
                self.buttons[bit_idx] = btn
                btn.clicked.connect(lambda _, b=bit_idx: self._on_button_clicked(b))
                
            # Bottom row buttons
            for col, num in enumerate(bottom_row):
                bit_idx = num - 1
                btn = QPushButton(str(num))
                btn.setFixedSize(16, 16)
                btn.setCheckable(True)
                btn.setToolTip(f"Layer {num}")
                btn.setObjectName("BitButton")
                block_layout.addWidget(btn, 1, col)
                self.buttons[bit_idx] = btn
                btn.clicked.connect(lambda _, b=bit_idx: self._on_button_clicked(b))
                
            row_idx = block_idx // 2
            col_idx = block_idx % 2
            main_layout.addWidget(block_widget, row_idx, col_idx)
            
        self._update_styles()
        
    def _on_button_clicked(self, bit_idx):
        if self.block_updates: return
        
        num = bit_idx + 1
        if self.single_select:
            self.value = num
        else:
            bit_val = 1 << bit_idx
            if self.buttons[bit_idx].isChecked():
                self.value |= bit_val
            else:
                self.value &= ~bit_val
            
        self._update_styles()
        self.value_changed.emit(self.value)
        
    def _update_styles(self):
        for bit_idx, btn in self.buttons.items():
            num = bit_idx + 1
            if self.single_select:
                is_set = (self.value == num)
            else:
                is_set = bool(self.value & (1 << bit_idx))
            btn.blockSignals(True)
            btn.setChecked(is_set)
            btn.blockSignals(False)
            
            if is_set:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {Theme.ACCENT};
                        color: {Theme.BG_INPUT};
                        border: none;
                        font-size: 8px;
                        font-weight: bold;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #202020;
                        color: #666666;
                        border: 1px solid #181818;
                        font-size: 8px;
                    }}
                    QPushButton:hover {{
                        background-color: #333333;
                        color: #888888;
                    }}
                """)
                
    def set_value(self, val):
        self.block_updates = True
        if self.single_select:
            try:
                val_int = int(val)
            except (ValueError, TypeError):
                val_int = 1
            if val_int < 1:
                val_int = 1
            elif val_int > 32:
                val_int = 32
            self.value = val_int
        else:
            self.value = int(val) & 0xFFFFFFFF
        self._update_styles()
        self.block_updates = False


from PySide6.QtGui import QPainter, QPolygon, QBrush, QPen, QColor
from PySide6.QtCore import QPoint

class PlaybackButton(QPushButton):
    """A premium custom square button that draws vector icon shapes (Play, Pause, Prev, Next) with QPainter."""
    TYPE_PLAY = "play"
    TYPE_PAUSE = "pause"
    TYPE_PREV = "prev"
    TYPE_NEXT = "next"
    
    def __init__(self, btn_type, parent=None):
        super().__init__(parent)
        self.btn_type = btn_type
        self.setFixedSize(24, 24)
        self.setCursor(Qt.PointingHandCursor)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        is_hovered = self.underMouse()
        is_enabled = self.isEnabled()
        
        bg_color = QColor(Theme.BG_CARD)
        border_color = QColor(Theme.BORDER_DEFAULT)
        
        if not is_enabled:
            bg_color = QColor(Theme.BG_INPUT)
            icon_color = QColor(Theme.TEXT_MUTED)
        else:
            if self.btn_type == self.TYPE_PAUSE:
                bg_color = QColor(Theme.ACCENT)
                border_color = QColor(Theme.ACCENT)
                icon_color = QColor(Theme.BG_WINDOW)
                if is_hovered:
                    bg_color = QColor(Theme.ACCENT_HOVER)
                    border_color = QColor(Theme.ACCENT_HOVER)
            else:
                if is_hovered:
                    bg_color = QColor(Theme.BG_HOVER)
                    border_color = QColor(Theme.BORDER_FOCUS)
                icon_color = QColor(Theme.TEXT_HIGHLIGHT)
                
        painter.setBrush(bg_color)
        painter.setPen(QPen(border_color, 1))
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 2, 2)
        
        cx = rect.width() / 2
        cy = rect.height() / 2
        
        painter.setBrush(QBrush(icon_color))
        painter.setPen(Qt.NoPen)
        
        if self.btn_type == self.TYPE_PLAY:
            poly = QPolygon([
                QPoint(int(cx - 3), int(cy - 5)),
                QPoint(int(cx - 3), int(cy + 5)),
                QPoint(int(cx + 5), int(cy))
            ])
            painter.drawPolygon(poly)
            
        elif self.btn_type == self.TYPE_PAUSE:
            painter.drawRect(int(cx - 4), int(cy - 5), 3, 10)
            painter.drawRect(int(cx + 1), int(cy - 5), 3, 10)
            
        elif self.btn_type == self.TYPE_PREV:
            painter.drawRect(int(cx - 5), int(cy - 5), 2, 10)
            poly = QPolygon([
                QPoint(int(cx + 4), int(cy - 5)),
                QPoint(int(cx + 4), int(cy + 5)),
                QPoint(int(cx - 2), int(cy))
            ])
            painter.drawPolygon(poly)
            
        elif self.btn_type == self.TYPE_NEXT:
            painter.drawRect(int(cx + 3), int(cy - 5), 2, 10)
            poly = QPolygon([
                QPoint(int(cx - 4), int(cy - 5)),
                QPoint(int(cx - 4), int(cy + 5)),
                QPoint(int(cx + 2), int(cy))
            ])
            painter.drawPolygon(poly)


from editor.undo_redo import ChangeComponentCommand, AddComponentCommand, RemoveComponentCommand
from PySide6.QtWidgets import QInputDialog

class InspectorPanel(QWidget):
    request_open_script = Signal(str)
    request_open_animator = Signal()

    def __init__(self):
        super().__init__()
        self.setMinimumWidth(220)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.container = QWidget()
        self.content_layout = QVBoxLayout(self.container)
        self.content_layout.setContentsMargins(*Theme.MARGIN_STANDARD)
        self.content_layout.setSpacing(Theme.SPACING_STANDARD)
        self.content_layout.setAlignment(Qt.AlignTop)

        scroll.setWidget(self.container)
        main_layout.addWidget(scroll)
        
        self.show_placeholder("No selection")

        self.active_editors = {} # (comp_name, key) -> widget
        self.state = EditorState.instance()
        self.state.selection_changed.connect(self.on_selection_changed)
        self.state.scene_loaded.connect(self.refresh_values)
        self.state.scene_updated.connect(self.refresh_values)

    def _apply_color_preset(self, obj, col_field, color):
        col_field.set_value(color)
        self.update_component(obj, "LightSource", "color", list(color))

    def on_selection_changed(self, obj_id):
        self.clear_content() # Clears active_editors too
        
        if not obj_id:
            self.show_placeholder("No selection")
            return
        
        obj = self.state.get_selected_object()
        if not obj:
            self.show_placeholder("Object not found")
            return
        
        self.build_inspector(obj)

    def clear_content(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.active_editors.clear()

    def show_placeholder(self, text):
        placeholder = QLabel(text)
        placeholder.setStyleSheet(f"color: {Theme.TEXT_MUTED}; padding: 10px;")
        placeholder.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(placeholder)

    def refresh_values(self):
        """Updates active editors from current object state without rebuilding UI."""
        if not self.state.selected_object_id:
            return
            
        obj = self.state.get_selected_object()
        if not obj:
            return
            
        # Iterate over active editors and update their values
        for (comp_name, key), widget in self.active_editors.items():
            # Skip update if user is currently typing in this widget
            if widget.hasFocus():
                continue
                
            # For Vec2Field, check its children focus
            if isinstance(widget, Vec2Field):
                 if widget.x_field.hasFocus() or widget.y_field.hasFocus():
                     continue
            
            if comp_name in obj.get("components", {}):
                data = obj["components"][comp_name]
                if key in data:
                    val = data[key]
                    
                    # Update widget safely
                    if isinstance(widget, Vec2Field):
                        if isinstance(val, (list, tuple)) and len(val) >= 2:
                            widget.set_value(val[0], val[1])
                    elif isinstance(widget, FloatField):
                        widget.set_value(float(val))
                    elif isinstance(widget, ColorField):
                        widget.set_value(val)
                    elif isinstance(widget, BitmaskGrid):
                        widget.set_value(int(val))

    def create_header(self, text, obj, comp_name):
        """Creates a component section header with an optional remove button."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 8, 0, 2)
        layout.setSpacing(Theme.SPACING_STANDARD)

        label = QLabel(text)
        label.setStyleSheet(
            f"font-weight: bold; color: {Theme.TEXT_HIGHLIGHT}; "
            f"font-size: {Theme.FONT_REGULAR};"
        )
        layout.addWidget(label)
        layout.addStretch()

        if comp_name != "Transform":
            remove_btn = QPushButton("x")
            remove_btn.setFixedSize(16, 16)
            remove_btn.setStyleSheet(
                f"QPushButton {{ background: transparent; color: {Theme.TEXT_MUTED}; border: none; font-weight: bold; }}"
                f"QPushButton:hover {{ color: #ff4444; }}"
            )
            remove_btn.clicked.connect(lambda: self.remove_component(obj, comp_name))
            layout.addWidget(remove_btn)

        # Separator line
        frame = QFrame()
        frame.setFrameShape(QFrame.HLine)
        frame.setFrameShadow(QFrame.Plain)
        frame.setStyleSheet(f"background: {Theme.BORDER_DEFAULT};")
        frame.setFixedHeight(1)

        final_layout = QVBoxLayout()
        final_layout.setContentsMargins(0, 0, 0, 0)
        final_layout.setSpacing(0)
        final_layout.addWidget(container)
        final_layout.addWidget(frame)

        w = QWidget()
        w.setLayout(final_layout)

        # Right-click context menu
        w.setContextMenuPolicy(Qt.CustomContextMenu)
        w.customContextMenuRequested.connect(
            lambda pos: self.show_header_context_menu(pos, w, obj, comp_name)
        )

        return w

    def show_header_context_menu(self, pos, widget, obj, comp_name):
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        
        if comp_name != "Transform":
            delete_action = menu.addAction("Delete Component")
            delete_action.triggered.connect(lambda: self.remove_component(obj, comp_name))
        
        if not menu.isEmpty():
            menu.exec(widget.mapToGlobal(pos))

    def remove_component(self, obj, comp_name):
        cmd = RemoveComponentCommand(obj, comp_name)
        self.state.undo_stack.push(cmd)
        cmd.redo()
        # Refresh is handled by MainWindow loop usually, but here we force inspector refresh
        self.state.select_object(obj.get("id"))


    def build_inspector(self, obj):
        # Object name
        name_label = QLabel(obj.get("name", "Unnamed"))
        name_label.setStyleSheet(
            f"font-size: {Theme.FONT_HEADER}; font-weight: bold; "
            f"color: {Theme.TEXT_HIGHLIGHT}; padding: 5px 6px; "
            f"background: {Theme.BG_CARD};"
        )
        self.content_layout.addWidget(name_label)

        # ID
        id_label = QLabel(f"ID: {obj.get('id', 'N/A')[:8]}...")
        id_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: {Theme.FONT_TINY}; padding-left: 6px;")
        self.content_layout.addWidget(id_label)

        # Components
        components = obj.get("components", {})
        
        for comp_name, comp_data in components.items():
            if comp_name == "Transform":
                self.add_transform_editor(comp_data, obj)
            elif comp_name == "SpriteRenderer":
                self.add_sprite_editor(comp_data, obj)
            elif comp_name == "Script":
                self.add_script_editor(comp_data, obj)
            elif comp_name == "RigidBody":
                self.add_rigidbody_editor(comp_data, obj)
            elif comp_name == "BoxCollider":
                self.add_box_collider_editor(comp_data, obj)
            elif comp_name == "CircleCollider":
                self.add_circle_collider_editor(comp_data, obj)
            elif comp_name == "Camera":
                self.add_camera_editor(comp_data, obj)
            elif comp_name == "LightSource":
                self.add_light_source_editor(comp_data, obj)
            elif comp_name == "Background":
                self.add_background_editor(comp_data, obj)
            elif comp_name == "TextRenderer":
                self.add_text_renderer_editor(comp_data, obj)
            elif comp_name == "Animator" or comp_name == "Animation":
                self.add_animator_editor(comp_data, obj)

        # Determine available components
        available = []
        all_components = [
            "Transform", "SpriteRenderer", "Script", "RigidBody", 
            "BoxCollider", "CircleCollider", "Camera", "LightSource", "Background", "TextRenderer", "Animation"
        ]
        
        for c in all_components:
            # Map display name back to internal key for availability check
            internal = "Animator" if c == "Animation" else c
            if internal not in components:
                available.append(c)
        
        if not available:
            return
        
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(4, 8, 4, 4)
        
        add_btn = QPushButton("+ Add Component")
        add_btn.setFixedHeight(22)
        add_btn.clicked.connect(lambda: self.show_add_menu(obj, available, add_btn))
        btn_layout.addWidget(add_btn)
        btn_layout.addStretch()
        
        btn_widget = QWidget()
        btn_widget.setLayout(btn_layout)
        self.content_layout.addWidget(btn_widget)

    def add_background_editor(self, data, obj):
        if data is None: data = {}
        self.content_layout.addWidget(self.create_header("Background", obj, "Background"))

        form = QFormLayout()
        form.setContentsMargins(*Theme.MARGIN_STANDARD)
        form.setSpacing(Theme.SPACING_STANDARD)
        form.setLabelAlignment(Qt.AlignRight)

        # Sprite
        path_row = QHBoxLayout()
        current_path = data.get("sprite_path", "")
        path_label = QLabel(os.path.basename(current_path) if current_path else "(none)")
        path_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: {Theme.FONT_SMALL};")
        browse_btn = QPushButton("...")
        browse_btn.setFixedSize(24, 20)
        browse_btn.clicked.connect(lambda: self.pick_image_generic(obj, "Background", "sprite_path", path_label))
        
        path_row.addWidget(path_label)
        path_row.addWidget(browse_btn)
        form.addRow(QLabel("Image:"), path_row)

        # Color
        color = data.get("color", [255, 255, 255, 255])
        col_field = ColorField(tuple(color))
        col_field.value_changed.connect(lambda c: self.update_component(obj, "Background", "color", c))
        form.addRow(QLabel("Color:"), col_field)
        
        # Fixed
        fixed = data.get("fixed", True)
        fixed_check = QCheckBox()
        fixed_check.setChecked(fixed)
        fixed_check.stateChanged.connect(lambda s: self.update_component(obj, "Background", "fixed", s == 2))
        form.addRow(QLabel("Fixed (Camera):"), fixed_check)
        
        # Layer
        layer = data.get("layer", 1)
        layer_grid = BitmaskGrid(layer, single_select=True)
        layer_grid.value_changed.connect(lambda v: self.update_component(obj, "Background", "layer", v))
        form.addRow(QLabel("Layer:"), layer_grid)
        self.active_editors[("Background", "layer")] = layer_grid

        form_widget = QWidget()
        form_widget.setLayout(form)
        self.content_layout.addWidget(form_widget)

    def add_text_renderer_editor(self, data, obj):
        if data is None: data = {}
        self.content_layout.addWidget(self.create_header("TextRenderer", obj, "TextRenderer"))

        form = QFormLayout()
        form.setContentsMargins(*Theme.MARGIN_STANDARD)
        form.setSpacing(Theme.SPACING_STANDARD)
        form.setLabelAlignment(Qt.AlignRight)

        # Text Content
        text_val = data.get("text", "Text")
        text_edit = QLineEdit(text_val)
        text_edit.textChanged.connect(lambda v: self.preview_component(obj, "TextRenderer", "text", v))
        text_edit.editingFinished.connect(lambda: self.update_component(obj, "TextRenderer", "text", text_edit.text()))
        form.addRow(QLabel("Text:"), text_edit)

        # Font Size
        font_size = data.get("font_size", 24.0)
        size_field = FloatField(font_size, min_val=1.0)
        size_field.value_edited.connect(lambda v: self.preview_component(obj, "TextRenderer", "font_size", v))
        size_field.value_committed.connect(lambda v, old: self.update_component(obj, "TextRenderer", "font_size", v))
        form.addRow(QLabel("Font Size:"), size_field)

        # Color
        color = data.get("color", [255, 255, 255, 255])
        col_field = ColorField(tuple(color))
        col_field.value_changed.connect(lambda c: self.update_component(obj, "TextRenderer", "color", c))
        form.addRow(QLabel("Color:"), col_field)

        # Layer
        layer = data.get("layer", 1)
        layer_grid = BitmaskGrid(layer, single_select=True)
        layer_grid.value_changed.connect(lambda v: self.update_component(obj, "TextRenderer", "layer", v))
        form.addRow(QLabel("Layer:"), layer_grid)
        self.active_editors[("TextRenderer", "layer")] = layer_grid

        form_widget = QWidget()
        form_widget.setLayout(form)
        self.content_layout.addWidget(form_widget)

    def add_animator_editor(self, data, obj):
        if data is None: data = {}
        self.content_layout.addWidget(self.create_header("Animation", obj, "Animator"))

        form = QFormLayout()
        form.setContentsMargins(*Theme.MARGIN_STANDARD)
        form.setSpacing(Theme.SPACING_STANDARD)
        form.setLabelAlignment(Qt.AlignRight)

        # Sprite Sheet
        path_row = QHBoxLayout()
        current_path = data.get("sprite_sheet", "")
        path_label = QLabel(os.path.basename(current_path) if current_path else "(none)")
        path_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: {Theme.FONT_SMALL};")
        browse_btn = QPushButton("...")
        browse_btn.setFixedSize(24, 20)
        browse_btn.clicked.connect(lambda: self.pick_image_generic(obj, "Animator", "sprite_sheet", path_label))
        path_row.addWidget(path_label)
        path_row.addWidget(browse_btn)
        form.addRow(QLabel("Sprite Sheet:"), path_row)

        # Frame Width
        fw_val = data.get("frame_width", 32)
        fw_field = FloatField(fw_val, min_val=1)
        fw_field.value_committed.connect(lambda v, old: self.update_component(obj, "Animator", "frame_width", int(v)))
        form.addRow(QLabel("Frame Width:"), fw_field)
        self.active_editors[("Animator", "frame_width")] = fw_field

        # Frame Height
        fh_val = data.get("frame_height", 32)
        fh_field = FloatField(fh_val, min_val=1)
        fh_field.value_committed.connect(lambda v, old: self.update_component(obj, "Animator", "frame_height", int(v)))
        form.addRow(QLabel("Frame Height:"), fh_field)
        self.active_editors[("Animator", "frame_height")] = fh_field

        # Play / Pause & Frame Stepping Controls
        control_row = QHBoxLayout()
        control_row.setContentsMargins(0, 0, 0, 0)
        control_row.setSpacing(4)
        
        is_playing = data.get("playing", True)
        play_btn = PlaybackButton(PlaybackButton.TYPE_PAUSE if is_playing else PlaybackButton.TYPE_PLAY)
        prev_btn = PlaybackButton(PlaybackButton.TYPE_PREV)
        next_btn = PlaybackButton(PlaybackButton.TYPE_NEXT)
        
        prev_btn.setToolTip("Previous Frame")
        next_btn.setToolTip("Next Frame")
        
        prev_btn.setEnabled(not is_playing)
        next_btn.setEnabled(not is_playing)
        
        def toggle_play():
            nonlocal is_playing
            is_playing = not is_playing
            self.update_component(obj, "Animator", "playing", is_playing)
            play_btn.btn_type = PlaybackButton.TYPE_PAUSE if is_playing else PlaybackButton.TYPE_PLAY
            prev_btn.setEnabled(not is_playing)
            next_btn.setEnabled(not is_playing)
            play_btn.update()
            prev_btn.update()
            next_btn.update()
            self.state.scene_updated.emit()
            
        def get_frames_count():
            curr_state = data.get("current_state", "")
            if not curr_state: return 1
            anim_info = data.get("animations", {}).get(curr_state, {})
            return len(anim_info.get("frames", [0]))

        def step_prev():
            live = obj.get("components", {}).get("Animator", {})
            curr_idx = live.get("frame_idx", 0)
            count = get_frames_count()
            new_idx = (curr_idx - 1) % count if count > 0 else 0
            obj["components"]["Animator"]["frame_idx"] = new_idx
            self.state.scene_updated.emit()

        def step_next():
            live = obj.get("components", {}).get("Animator", {})
            curr_idx = live.get("frame_idx", 0)
            count = get_frames_count()
            new_idx = (curr_idx + 1) % count if count > 0 else 0
            obj["components"]["Animator"]["frame_idx"] = new_idx
            self.state.scene_updated.emit()
            
        play_btn.clicked.connect(toggle_play)
        prev_btn.clicked.connect(step_prev)
        next_btn.clicked.connect(step_next)
        
        control_row.addWidget(prev_btn)
        control_row.addWidget(play_btn)
        control_row.addWidget(next_btn)
        control_row.addStretch()
        
        control_widget = QWidget()
        control_widget.setLayout(control_row)
        form.addRow(QLabel("Animation:"), control_widget)

        # Form widget assembly
        form_widget = QWidget()
        form_widget.setLayout(form)
        self.content_layout.addWidget(form_widget)

    def pick_image_generic(self, obj, comp_name, key, label_widget):
        current_val = obj.get("components", {}).get(comp_name, {}).get(key, "")
        
        if current_val:
            # Show Options
            menu = QMenu(self)
            replace_action = menu.addAction("Replace")
            delete_action = menu.addAction("Delete")
            
            # Position menu at mouse cursor or button?
            # We don't have button reference easily, use cursor
            from PySide6.QtGui import QCursor
            action = menu.exec(QCursor.pos())
            
            if action == delete_action:
                if comp_name in obj.get("components", {}):
                     obj["components"][comp_name][key] = ""
                label_widget.setText("None")
                self.state.scene_loaded.emit()
                return
            elif action == replace_action:
                pass # Proceed to picker
            else:
                return # Cancelled
        
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", 
            os.path.join(self.state.project_root, "assets", "sprites"),
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if path:
            import shutil
            try:
                rel_path = os.path.relpath(path, self.state.project_root)
                if rel_path.startswith("..") or os.path.isabs(rel_path): raise ValueError()
            except ValueError:
                dest_dir = os.path.join(self.state.project_root, "assets", "sprites")
                os.makedirs(dest_dir, exist_ok=True)
                filename = os.path.basename(path)
                dest_path = os.path.join(dest_dir, filename)
                shutil.copy2(path, dest_path)
                rel_path = os.path.relpath(dest_path, self.state.project_root)
            
            if comp_name not in obj.get("components", {}): obj["components"][comp_name] = {}
            obj["components"][comp_name][key] = rel_path
            label_widget.setText(os.path.basename(rel_path))
            self.state.scene_loaded.emit()

    def add_transform_editor(self, data, obj):
        self.content_layout.addWidget(self.create_header("Transform", obj, "Transform"))

        form = QFormLayout()
        form.setContentsMargins(*Theme.MARGIN_STANDARD)
        form.setSpacing(Theme.SPACING_STANDARD)
        form.setLabelAlignment(Qt.AlignRight)

        # Position
        pos = data.get("position", [0, 0])
        pos_field = Vec2Field(pos[0], pos[1])
        pos_field.value_edited.connect(lambda x, y: self.preview_transform(obj, "position", (x, y)))
        pos_field.value_committed.connect(lambda nx, ny, ox, oy: self.commit_transform(obj, "position", (nx, ny), (ox, oy)))
        form.addRow(QLabel("Position:"), pos_field)
        self.active_editors[("Transform", "position")] = pos_field

        # Rotation
        rot = data.get("rotation", 0)
        rot_field = FloatField(rot)
        rot_field.value_edited.connect(lambda v: self.preview_transform(obj, "rotation", v))
        rot_field.value_committed.connect(lambda n, o: self.commit_transform(obj, "rotation", n, o))
        form.addRow(QLabel("Rotation:"), rot_field)
        self.active_editors[("Transform", "rotation")] = rot_field

        # Scale
        scale = data.get("scale", [1, 1])
        scale_field = Vec2Field(scale[0], scale[1])
        scale_field.value_edited.connect(lambda x, y: self.preview_transform(obj, "scale", (x, y)))
        scale_field.value_committed.connect(lambda nx, ny, ox, oy: self.commit_transform(obj, "scale", (nx, ny), (ox, oy)))
        form.addRow(QLabel("Scale:"), scale_field)
        self.active_editors[("Transform", "scale")] = scale_field

        form_widget = QWidget()
        form_widget.setLayout(form)
        self.content_layout.addWidget(form_widget)

    def preview_transform(self, obj, key, value):
        val = list(value) if isinstance(value, tuple) else value
        self.preview_component(obj, "Transform", key, val)

    def commit_transform(self, obj, key, value, old_value=None):
        val = list(value) if isinstance(value, tuple) else value
        old = list(old_value) if isinstance(old_value, tuple) else old_value
        self.update_component(obj, "Transform", key, val, old_value=old)

    def add_component_section(self, name, data, obj):
        self.content_layout.addWidget(self.create_header(name, obj, name))

        form = QFormLayout()
        form.setContentsMargins(*Theme.MARGIN_STANDARD)
        form.setSpacing(Theme.SPACING_STANDARD)
        form.setLabelAlignment(Qt.AlignRight)

        if isinstance(data, dict):
            for key, value in data.items():
                key_label = QLabel(f"{key}:")
                key_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: {Theme.FONT_SMALL};")

                val_label = QLabel(str(value))
                val_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: {Theme.FONT_SMALL};")
                val_label.setWordWrap(True)

                form.addRow(key_label, val_label)

        form_widget = QWidget()
        form_widget.setLayout(form)
        self.content_layout.addWidget(form_widget)

    def add_sprite_editor(self, data, obj):
        self.content_layout.addWidget(self.create_header("SpriteRenderer", obj, "SpriteRenderer"))

        form = QFormLayout()
        form.setContentsMargins(*Theme.MARGIN_STANDARD)
        form.setSpacing(Theme.SPACING_STANDARD)
        form.setLabelAlignment(Qt.AlignRight)

        # Sprite path
        path_row = QHBoxLayout()
        path_row.setSpacing(Theme.SPACING_STANDARD)

        current_path = data.get("sprite_path", "")
        anim_data = obj.get("components", {}).get("Animator", {})
        anim_sheet = anim_data.get("sprite_sheet", "")
        
        display_text = "(none)"
        if current_path:
            display_text = os.path.basename(current_path)
        elif anim_sheet:
            display_text = f"{os.path.basename(anim_sheet)} (Animator)"
            
        path_label = QLabel(display_text)
        path_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: {Theme.FONT_SMALL};")

        browse_btn = QPushButton("...")
        browse_btn.setFixedSize(24, 20)
        browse_btn.clicked.connect(lambda: self.pick_image_generic(obj, "SpriteRenderer", "sprite_path", path_label))

        path_row.addWidget(path_label)
        path_row.addWidget(browse_btn)
        path_row.addStretch()

        path_widget = QWidget()
        path_widget.setLayout(path_row)
        form.addRow(QLabel("Sprite:"), path_widget)

        # Layer
        layer = data.get("layer", 1)
        layer_grid = BitmaskGrid(layer, single_select=True)
        layer_grid.value_changed.connect(lambda v: self.update_component(obj, "SpriteRenderer", "layer", v))
        form.addRow(QLabel("Layer:"), layer_grid)
        self.active_editors[("SpriteRenderer", "layer")] = layer_grid

        # Visible
        visible = data.get("visible", True)
        visible_check = QCheckBox()
        visible_check.setChecked(visible)
        visible_check.stateChanged.connect(lambda s: self.update_sprite(obj, "visible", s == 2))
        form.addRow(QLabel("Visible:"), visible_check)

        # Tint
        tint = data.get("tint", [255, 255, 255, 255])
        col_field = ColorField(tuple(tint))
        col_field.value_changed.connect(lambda c: self.update_component(obj, "SpriteRenderer", "tint", c))
        form.addRow(QLabel("Tint:"), col_field)

        form_widget = QWidget()
        form_widget.setLayout(form)
        self.content_layout.addWidget(form_widget)

    def update_sprite(self, obj, key, value):
        if "SpriteRenderer" not in obj.get("components", {}):
            obj["components"]["SpriteRenderer"] = {}
        obj["components"]["SpriteRenderer"][key] = value
        self.state.scene_loaded.emit()

    def add_script_editor(self, data, obj):
        self.content_layout.addWidget(self.create_header("Script", obj, "Script"))

        form = QFormLayout()
        form.setContentsMargins(*Theme.MARGIN_STANDARD)
        form.setSpacing(Theme.SPACING_STANDARD)
        
        # Script path row
        current_path = data.get("script_path", "")
        
        path_widget = QWidget()
        path_layout = QHBoxLayout(path_widget)
        path_layout.setContentsMargins(0, 0, 0, 0)
        path_layout.setSpacing(4)
        
        path_label = QLabel(os.path.basename(current_path) if current_path else "(none)")
        path_label.setStyleSheet(
            f"color: {Theme.TEXT_SECONDARY}; background: {Theme.BG_INPUT}; "
            f"padding: 2px 4px;"
        )
        path_label.setFixedHeight(22)

        browse_btn = QPushButton("...")
        browse_btn.setFixedSize(24, 22)
        browse_btn.clicked.connect(lambda: self.show_script_menu(obj, path_label, browse_btn, current_path))
        
        path_layout.addWidget(path_label)
        path_layout.addWidget(browse_btn)
        
        form.addRow("Script:", path_widget)

        # Properties
        if current_path:
            full_path = os.path.join(self.state.project_root, current_path)
            defaults = ScriptParser.parse_properties(full_path)
            
            # Merge stored properties
            stored_props = data.get("properties", {})
            
            # Ensure all defaults are present in stored_props if not set
            # But we don't necessarily save them back unless changed
            
            for key, default_val in defaults.items():
                current_val = stored_props.get(key, default_val)
                
                # Check type
                if isinstance(default_val, (int, float)):
                    field = FloatField(float(current_val))
                    field.value_edited.connect(lambda v, k=key: self.preview_script_property(obj, k, v))
                    field.value_committed.connect(lambda v, k=key: self.update_script_property(obj, k, v))
                    form.addRow(f"{key}:", field)
                elif isinstance(default_val, bool):
                    check = QCheckBox()
                    check.setChecked(bool(current_val))
                    # Note: QCheckBox doesn't separate edited/committed clearly, so we just update
                    check.stateChanged.connect(lambda s, k=key: self.update_script_property(obj, k, s == 2))
                    form.addRow(f"{key}:", check)
                # TODO: String, Color support?
        
        form_widget = QWidget()
        form_widget.setLayout(form)
        self.content_layout.addWidget(form_widget)

    def preview_script_property(self, obj, key, value):
        if "Script" in obj.get("components", {}):
            if "properties" not in obj["components"]["Script"]:
                obj["components"]["Script"]["properties"] = {}
            obj["components"]["Script"]["properties"][key] = value
            # self.state.scene_loaded.emit() # Optional: heavy reload?

    def update_script_property(self, obj, key, value):
        if "Script" in obj.get("components", {}):
            if "properties" not in obj["components"]["Script"]:
                obj["components"]["Script"]["properties"] = {}
            
            current = obj["components"]["Script"]["properties"].get(key)
            if current != value:
                # We need a specific Command or reuse ChangeComponentCommand
                # Reusing ChangeComponentCommand is tricky because the path is deeper (components -> Script -> properties -> key)
                # Simplified: Direct update for now, or add specific command later
                obj["components"]["Script"]["properties"][key] = value
                
                # To support undo properly, we should really update ChangeComponentCommand to support nested keys or make a generic SetPropertyCommand
                # For now, let's just trigger scene load emit to save state
                self.state.scene_loaded.emit()
    
    def show_script_menu(self, obj, label_widget, btn_widget, current_path):
        from PySide6.QtWidgets import QMenu, QApplication
        menu = QMenu(self)
        
        # New
        act_new = menu.addAction("New Script...")
        act_new.triggered.connect(lambda: self.create_new_script(obj, label_widget))
        
        # Import
        act_import = menu.addAction("Import Script...")
        act_import.triggered.connect(lambda: self.pick_script(obj, label_widget))
        
        menu.addSeparator()
        
        # Edit
        act_edit = menu.addAction("Edit Script")
        if not current_path:
            act_edit.setEnabled(False)
        else:
            act_edit.triggered.connect(lambda: self.request_open_script.emit(current_path))
            
        # Show Menu
        menu.exec(btn_widget.mapToGlobal(QApplication.style().visualRect(Qt.LeftToRight, btn_widget.rect(), btn_widget.rect()).bottomLeft()))

    def create_new_script(self, obj, label_widget):
        name, ok = QInputDialog.getText(self, "New Script", "Script Name (without .py):")
        if ok and name:
            filename = f"{name}.py"
            dest_dir = os.path.join(self.state.project_root, "scripts")
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, filename)
            
            if os.path.exists(dest_path):
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Error", "File already exists!")
                return
                
            # Create Template
            template = (
                "from runtime.api import Script\n\n"
                f"class {name}(Script):\n"
                "    def start(self):\n"
                "        pass\n\n"
                "    def update(self, dt):\n"
                "        pass\n"
            )
            
            try:
                with open(dest_path, 'w') as f:
                    f.write(template)
                
                rel_path = os.path.relpath(dest_path, self.state.project_root)
                
                if "Script" not in obj.get("components", {}): obj["components"]["Script"] = {}
                obj["components"]["Script"]["script_path"] = rel_path
                obj["components"]["Script"]["properties"] = {} # clear old props
                
                self.state.scene_loaded.emit()
                label_widget.setText(filename)
                
                # Open it
                self.request_open_script.emit(rel_path)
                
            except Exception as e:
                print(f"Failed to create script: {e}")

    def pick_script(self, obj, label_widget):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Script", 
            os.path.join(self.state.project_root, "scripts"),
            "Python Scripts (*.py)"
        )
        if path:
            # Check if file is inside project
            try:
                rel_path = os.path.relpath(path, self.state.project_root)
                if rel_path.startswith("..") or os.path.isabs(rel_path):
                    raise ValueError("Outside project")
            except ValueError:
                # File is outside project - copy it to scripts
                import shutil
                dest_dir = os.path.join(self.state.project_root, "scripts")
                os.makedirs(dest_dir, exist_ok=True)
                
                filename = os.path.basename(path)
                dest_path = os.path.join(dest_dir, filename)
                
                # Handle duplicates
                if os.path.basename(path) != filename and os.path.exists(dest_path):
                     pass 
                
                shutil.copy2(path, dest_path)
                rel_path = os.path.relpath(dest_path, self.state.project_root)
            
            if "Script" not in obj.get("components", {}):
                obj["components"]["Script"] = {}
            obj["components"]["Script"]["script_path"] = rel_path
            self.state.scene_loaded.emit()
            label_widget.setText(os.path.basename(rel_path))

    def add_component_button(self, obj):
        components = obj.get("components", {})
        available = []
        
        if "SpriteRenderer" not in components:
            available.append("SpriteRenderer")
        if "BoxCollider" not in components:
            available.append("BoxCollider")
        if "CircleCollider" not in components:
            available.append("CircleCollider")
        if "RigidBody" not in components:
            available.append("RigidBody")
        if "Script" not in components:
            available.append("Script")
        if "Camera" not in components:
            available.append("Camera")
        if "LightSource" not in components:
            available.append("LightSource")
        
        if not available:
            return
        
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(4, 8, 4, 4)
        
        add_btn = QPushButton("+ Add Component")
        add_btn.setFixedHeight(22)
        add_btn.clicked.connect(lambda: self.show_add_menu(obj, available, add_btn))
        btn_layout.addWidget(add_btn)
        btn_layout.addStretch()
        
        btn_widget = QWidget()
        btn_widget.setLayout(btn_layout)
        self.content_layout.addWidget(btn_widget)

    def add_camera_editor(self, data, obj):
        if data is None: data = {}
        self.content_layout.addWidget(self.create_header("Camera", obj, "Camera"))

        form = QFormLayout()
        form.setContentsMargins(8, 4, 4, 4)
        form.setSpacing(2)
        form.setLabelAlignment(Qt.AlignRight)
        
        # Size
        width = data.get("width", 800.0)
        height = data.get("height", 600.0)
        size_field = Vec2Field(width, height, labels=("W", "H"))
        size_field.value_edited.connect(lambda w, h: [self.preview_component(obj, "Camera", "width", w), self.preview_component(obj, "Camera", "height", h)])
        size_field.value_committed.connect(lambda w, h: [self.update_component(obj, "Camera", "width", w), self.update_component(obj, "Camera", "height", h)])
        form.addRow(QLabel("Size:"), size_field)


        
        # Is Main
        is_main = data.get("is_main", True)
        main_check = QCheckBox()
        main_check.setChecked(is_main)
        main_check.stateChanged.connect(lambda s: self.update_component(obj, "Camera", "is_main", s == 2))
        form.addRow(QLabel("Main Camera:"), main_check)

        form_widget = QWidget()
        form_widget.setLayout(form)
        self.content_layout.addWidget(form_widget)

    def add_rigidbody_editor(self, data, obj):
        if data is None: data = {}
        self.content_layout.addWidget(self.create_header("RigidBody", obj, "RigidBody"))

        form = QFormLayout()
        form.setContentsMargins(*Theme.MARGIN_STANDARD)
        form.setSpacing(Theme.SPACING_STANDARD)
        form.setLabelAlignment(Qt.AlignRight)

        # Mass
        mass = data.get("mass", 1.0)
        mass_field = FloatField(mass, min_val=0.001)
        mass_field.value_edited.connect(lambda v: self.preview_component(obj, "RigidBody", "mass", v))
        mass_field.value_committed.connect(lambda v: self.update_component(obj, "RigidBody", "mass", v))
        form.addRow(QLabel("Mass:"), mass_field)
        self.active_editors[("RigidBody", "mass")] = mass_field

        # Drag
        drag = data.get("drag", 0.0)
        drag_field = FloatField(drag, min_val=0.0)
        drag_field.value_edited.connect(lambda v: self.preview_component(obj, "RigidBody", "drag", v))
        drag_field.value_committed.connect(lambda v: self.update_component(obj, "RigidBody", "drag", v))
        form.addRow(QLabel("Drag:"), drag_field)
        self.active_editors[("RigidBody", "drag")] = drag_field

        # Use Gravity
        use_gravity = data.get("use_gravity", True)
        gravity_check = QCheckBox()
        gravity_check.setChecked(use_gravity)
        gravity_check.stateChanged.connect(lambda s: self.update_component(obj, "RigidBody", "use_gravity", s == 2))
        form.addRow(QLabel("Use Gravity:"), gravity_check)

        # Restitution
        restitution = data.get("restitution", 0.5)
        rest_field = FloatField(restitution)
        rest_field.value_edited.connect(lambda v: self.preview_component(obj, "RigidBody", "restitution", v))
        rest_field.value_committed.connect(lambda v: self.update_component(obj, "RigidBody", "restitution", v))
        form.addRow(QLabel("Restitution:"), rest_field)

        form_widget = QWidget()
        form_widget.setLayout(form)
        self.content_layout.addWidget(form_widget)

    def add_box_collider_editor(self, data, obj):
        if data is None: data = {}
        self.content_layout.addWidget(self.create_header("BoxCollider", obj, "BoxCollider"))

        form = QFormLayout()
        form.setContentsMargins(*Theme.MARGIN_STANDARD)
        form.setSpacing(Theme.SPACING_STANDARD)
        form.setLabelAlignment(Qt.AlignRight)

        # Size
        size = data.get("size", [50.0, 50.0])
        size_field = Vec2Field(size[0], size[1], labels=("W", "H"))
        size_field.value_edited.connect(lambda w, h: self.preview_component(obj, "BoxCollider", "size", [w, h]))
        size_field.value_committed.connect(lambda w, h: self.update_component(obj, "BoxCollider", "size", [w, h]))
        form.addRow(QLabel("Size:"), size_field)
        self.active_editors[("BoxCollider", "size")] = size_field

        # Offset
        offset = data.get("offset", [0.0, 0.0])
        offset_field = Vec2Field(offset[0], offset[1])
        offset_field.value_edited.connect(lambda x, y: self.preview_component(obj, "BoxCollider", "offset", [x, y]))
        offset_field.value_committed.connect(lambda x, y: self.update_component(obj, "BoxCollider", "offset", [x, y]))
        form.addRow(QLabel("Offset:"), offset_field)
        self.active_editors[("BoxCollider", "offset")] = offset_field

        # Is Trigger
        is_trigger = data.get("is_trigger", False)
        trigger_check = QCheckBox()
        trigger_check.setChecked(is_trigger)
        trigger_check.stateChanged.connect(lambda s: self.update_component(obj, "BoxCollider", "is_trigger", s == 2))
        form.addRow(QLabel("Is Trigger:"), trigger_check)

        # Collision Layer
        cat = data.get("category_bitmask", 1)
        cat_grid = BitmaskGrid(cat)
        cat_grid.value_changed.connect(lambda v: self.update_component(obj, "BoxCollider", "category_bitmask", v))
        form.addRow(QLabel("Collision Layer:"), cat_grid)

        # Sync Button
        if "SpriteRenderer" in obj.get("components", {}):
            sync_btn = QPushButton("Snap to Visual Size")
            sync_btn.setFixedHeight(22)
            sync_btn.clicked.connect(lambda: self.sync_collider_size(obj))
            form.addRow("", sync_btn)

        form_widget = QWidget()
        form_widget.setLayout(form)
        self.content_layout.addWidget(form_widget)

    def sync_collider_size(self, obj):
        # 1. Get Scale
        scale = [1.0, 1.0]
        if "Transform" in obj.get("components", {}):
            scale = obj["components"]["Transform"].get("scale", [1.0, 1.0])
            
        # 2. Get Base Size (Sprite or Default)
        sprite_data = obj["components"].get("SpriteRenderer", {})
        path = sprite_data.get("sprite_path", "")
        
        base_w, base_h = 50.0, 50.0 # Default fallback
        
        if path:
            full_path = os.path.join(self.state.project_root, path)
            if os.path.exists(full_path):
                from PySide6.QtGui import QImage
                img = QImage(full_path)
                if not img.isNull():
                    base_w = float(img.width())
                    base_h = float(img.height())

        # 3. Calculate Final Size (Base * Scale)
        final_w = base_w * abs(scale[0])
        final_h = base_h * abs(scale[1])
        
        self.update_component(obj, "BoxCollider", "size", [final_w, final_h])
        
    def preview_component(self, obj, comp_name, key, value):
        """Updates the component data directly without undo history (for live preview)."""
        if comp_name in obj.get("components", {}):
            obj["components"][comp_name][key] = value
            self.state.scene_updated.emit()

    def update_component(self, obj, comp_name, key, value, old_value=None):
        if comp_name in obj.get("components", {}):
            current = obj["components"][comp_name].get(key)
            
            # If old_value is provided, we skip the equality check because current might already == value (preview)
            if old_value is None and current == value:
                return

            cmd = ChangeComponentCommand(obj, comp_name, key, value)
            if old_value is not None:
                 cmd.old_value = old_value
                 
            self.state.undo_stack.push(cmd)
            # cmd.redo() # Redo is implicit if we trust 'value' is what we want. 
            # BUT: redo() sets obj[...] = value. If obj is already value, it does nothing harmful.
            cmd.redo()
            
            self.state.scene_updated.emit()

    def show_add_menu(self, obj, available, button):
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        for comp in available:
            action = menu.addAction(comp)
            action.triggered.connect(lambda checked, c=comp: self.add_component(obj, c))
        menu.exec(button.mapToGlobal(button.rect().bottomLeft()))

    def add_component(self, obj, comp_name):
        # Map display names to internal component keys
        display_to_internal = {"Animation": "Animator"}
        comp_name = display_to_internal.get(comp_name, comp_name)
        defaults = {
            "SpriteRenderer": {"sprite_path": "", "layer": 1, "visible": True, "tint": [255, 255, 255, 255]},
            "BoxCollider": {"size": [50.0, 50.0], "offset": [0.0, 0.0], "is_trigger": False, "category_bitmask": 1, "collision_mask": 4294967295},
            "CircleCollider": {"radius": 25.0, "offset": [0.0, 0.0], "is_trigger": False, "category_bitmask": 1, "collision_mask": 4294967295},
            "RigidBody": {"mass": 1.0, "drag": 0.0, "use_gravity": True, "restitution": 0.5, "velocity": [0.0, 0.0]},
            "Script": {"script_path": ""},
            "Camera": {"width": 800.0, "height": 600.0, "zoom": 1.0, "is_main": True},
            "LightSource": {"color": [255, 255, 255, 255], "intensity": 1.0, "radius": 200.0, "type": "point", "cast_shadows": True},
            "Background": {"sprite_path": "", "color": [255, 255, 255, 255], "loop_x": False, "loop_y": False, "scroll_speed": [0.0, 0.0], "fixed": True, "layer": 1},
            "TextRenderer": {"text": "Text", "font_size": 24.0, "color": [255, 255, 255, 255], "layer": 1},
            "Animator": {"sprite_sheet": "", "frame_width": 32, "frame_height": 32, "current_state": "", "animations": {}, "parameters": {}, "transitions": []}
        }
        if comp_name in defaults:
            cmd = AddComponentCommand(obj, comp_name, defaults[comp_name])
            self.state.undo_stack.push(cmd)
            cmd.redo()
            self.state.select_object(obj.get("id"))  # Refresh inspector


    def add_circle_collider_editor(self, data, obj):
        if data is None: data = {}
        self.content_layout.addWidget(self.create_header("CircleCollider", obj, "CircleCollider"))

        form = QFormLayout()
        form.setContentsMargins(*Theme.MARGIN_STANDARD)
        form.setSpacing(Theme.SPACING_STANDARD)
        form.setLabelAlignment(Qt.AlignRight)

        # Radius
        radius = data.get("radius", 25.0)
        radius_field = FloatField(radius)
        radius_field.value_edited.connect(lambda v: self.preview_component(obj, "CircleCollider", "radius", v))
        radius_field.value_committed.connect(lambda v: self.update_component(obj, "CircleCollider", "radius", v))
        form.addRow(QLabel("Radius:"), radius_field)

        # Offset
        offset = data.get("offset", [0.0, 0.0])
        offset_field = Vec2Field(offset[0], offset[1])
        offset_field.value_edited.connect(lambda x, y: self.preview_component(obj, "CircleCollider", "offset", [x, y]))
        offset_field.value_committed.connect(lambda x, y: self.update_component(obj, "CircleCollider", "offset", [x, y]))
        form.addRow(QLabel("Offset:"), offset_field)

        # Is Trigger
        is_trigger = data.get("is_trigger", False)
        trigger_check = QCheckBox()
        trigger_check.setChecked(is_trigger)
        trigger_check.stateChanged.connect(lambda s: self.update_component(obj, "CircleCollider", "is_trigger", s == 2))
        form.addRow(QLabel("Is Trigger:"), trigger_check)

        # Category
        cat = data.get("category_bitmask", 1)
        cat_grid = BitmaskGrid(cat)
        cat_grid.value_changed.connect(lambda v: self.update_component(obj, "CircleCollider", "category_bitmask", v))
        form.addRow(QLabel("Collision Layer:"), cat_grid)

        form_widget = QWidget()
        form_widget.setLayout(form)
        self.content_layout.addWidget(form_widget)

    def add_camera_editor(self, data, obj):
        if data is None: data = {}
        self.content_layout.addWidget(self.create_header("Camera", obj, "Camera"))

        form = QFormLayout()
        form.setContentsMargins(*Theme.MARGIN_STANDARD)
        form.setSpacing(Theme.SPACING_STANDARD)
        form.setLabelAlignment(Qt.AlignRight)

        # Size
        width = data.get("width", 800.0)
        height = data.get("height", 600.0)
        size_field = Vec2Field(width, height, labels=("W", "H"))
        size_field.value_edited.connect(
            lambda w, h: [
                self.preview_component(obj, "Camera", "width", w),
                self.preview_component(obj, "Camera", "height", h)
            ]
        )
        size_field.value_committed.connect(
            lambda w, h: [
                self.update_component(obj, "Camera", "width", w),
                self.update_component(obj, "Camera", "height", h)
            ]
        )
        form.addRow(QLabel("Size:"), size_field)

        # Is Main
        is_main = data.get("is_main", True)
        main_check = QCheckBox()
        main_check.setChecked(is_main)
        main_check.stateChanged.connect(lambda s: self.update_component(obj, "Camera", "is_main", s == 2))
        form.addRow(QLabel("Main Camera:"), main_check)

        form_widget = QWidget()
        form_widget.setLayout(form)
        self.content_layout.addWidget(form_widget)

    def add_light_source_editor(self, data, obj):
        if data is None: data = {}
        self.content_layout.addWidget(self.create_header("LightSource", obj, "LightSource"))

        form = QFormLayout()
        form.setContentsMargins(*Theme.MARGIN_STANDARD)
        form.setSpacing(Theme.SPACING_STANDARD)
        form.setLabelAlignment(Qt.AlignRight)

        # Color
        color = data.get("color", [255, 255, 255, 255])
        col_field = ColorField(tuple(color))
        col_field.value_changed.connect(lambda c: self.update_component(obj, "LightSource", "color", c))
        form.addRow(QLabel("Color:"), col_field)

        # Intensity (Uncapped field)
        intensity = data.get("intensity", 1.0)
        int_field = FloatField(intensity, min_val=0.0)
        int_field.value_edited.connect(lambda v: self.preview_component(obj, "LightSource", "intensity", v))
        int_field.value_committed.connect(lambda v, old: self.update_component(obj, "LightSource", "intensity", v))
        form.addRow(QLabel("Intensity:"), int_field)

        # Radius (Slider: 5.0 to 1000.0)
        radius = data.get("radius", 200.0)
        rad_slider = SliderFloatField(radius, 5.0, 1000.0, 1.0)
        rad_slider.value_edited.connect(lambda v: self.preview_component(obj, "LightSource", "radius", v))
        rad_slider.value_committed.connect(lambda v: self.update_component(obj, "LightSource", "radius", v))
        form.addRow(QLabel("Radius:"), rad_slider)

        # Cast Shadows
        cast_shadows = data.get("cast_shadows", True)
        shadow_check = QCheckBox()
        shadow_check.setChecked(cast_shadows)
        shadow_check.stateChanged.connect(lambda s: self.update_component(obj, "LightSource", "cast_shadows", s == 2))
        form.addRow(QLabel("Cast Shadows:"), shadow_check)

        form_widget = QWidget()
        form_widget.setLayout(form)
        self.content_layout.addWidget(form_widget)

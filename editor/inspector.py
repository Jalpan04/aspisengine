from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame, 
    QFormLayout, QLineEdit, QHBoxLayout, QPushButton, QFileDialog, QCheckBox, QMenu
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDoubleValidator
from editor.editor_state import EditorState
from editor.script_parser import ScriptParser
from editor.undo_redo import AddComponentCommand, ChangeComponentCommand, RemoveComponentCommand
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
        self.setFixedWidth(60)
        self.setStyleSheet("""
            QLineEdit {
                background: #252525;
                border: 1px solid #333333;
                color: #b0b0b0;
                padding: 2px 4px;
                font-size: 10px;
            }
            QLineEdit:focus {
                border: 1px solid #555555;
            }
        """)
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
        x_label.setStyleSheet("color: #666666; font-size: 9px;")
        x_label.setFixedWidth(12)
        self.x_field = FloatField(x)
        
        # Y
        y_label = QLabel(labels[1])
        y_label.setStyleSheet("color: #666666; font-size: 9px;")
        y_label.setFixedWidth(12)
        self.y_field = FloatField(y)
        
        layout.addWidget(x_label)
        layout.addWidget(self.x_field)
        layout.addWidget(y_label)
        layout.addWidget(self.y_field)
        layout.addStretch()
        
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


class ColorField(QPushButton):
    """Button that shows color and opens picker."""
    value_changed = Signal(list) # [r, g, b, a]

    def __init__(self, color_tuple=(255, 255, 255, 255)):
        super().__init__()
        self.setFixedWidth(60)
        self.setFixedHeight(18)
        self.color = color_tuple
        self._update_style()
        self.clicked.connect(self._pick_color)

    def _update_style(self):
        r, g, b, a = self.color
        self.setStyleSheet(f"background-color: rgba({r},{g},{b},{a/255.0:.2f}); border: 1px solid #555;")

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
        self.color = tuple(c)
        self._update_style()


from editor.undo_redo import ChangeComponentCommand, AddComponentCommand, RemoveComponentCommand
from PySide6.QtWidgets import QInputDialog

class InspectorPanel(QWidget):
    request_open_script = Signal(str)

    def __init__(self):
        super().__init__()
        self.setMinimumWidth(220)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        self.container = QWidget()
        self.content_layout = QVBoxLayout(self.container)
        self.content_layout.setContentsMargins(6, 6, 6, 6)
        self.content_layout.setSpacing(4)
        self.content_layout.setAlignment(Qt.AlignTop)
        
        scroll.setWidget(self.container)
        main_layout.addWidget(scroll)
        
        self.show_placeholder("No selection")

        self.active_editors = {} # (comp_name, key) -> widget
        self.state = EditorState.instance()
        self.state.selection_changed.connect(self.on_selection_changed)
        self.state.scene_loaded.connect(self.refresh_values)
        self.state.scene_updated.connect(self.refresh_values)

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
        placeholder.setStyleSheet("color: #555555; padding: 10px;")
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
                    # Add more types as needed

    def create_header(self, text, obj, comp_name):
        """Creates a header with a remove button (unless it's Transform)."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 6, 0, 2)
        layout.setSpacing(4)

        label = QLabel(text)
        label.setStyleSheet("font-weight: bold; color: #cccccc; font-size: 11px;")
        layout.addWidget(label)
        layout.addStretch()

        if comp_name != "Transform":
            remove_btn = QPushButton("x")
            remove_btn.setFixedSize(16, 16)
            remove_btn.setStyleSheet("""
                QPushButton { background: transparent; color: #666; border: none; font-weight: bold; }
                QPushButton:hover { color: #ff4444; }
            """)
            remove_btn.clicked.connect(lambda: self.remove_component(obj, comp_name))
            layout.addWidget(remove_btn)

        # Separator line
        frame = QFrame()
        frame.setFrameShape(QFrame.HLine)
        frame.setFrameShadow(QFrame.Plain)
        frame.setStyleSheet("background: #333333;")
        frame.setFixedHeight(1)
        
        final_layout = QVBoxLayout()
        final_layout.setContentsMargins(0,0,0,0)
        final_layout.setSpacing(0)
        final_layout.addWidget(container)
        final_layout.addWidget(frame)
        
        w = QWidget()
        w.setLayout(final_layout)
        
        # Right click context menu
        w.setContextMenuPolicy(Qt.CustomContextMenu)
        w.customContextMenuRequested.connect(lambda pos: self.show_header_context_menu(pos, w, obj, comp_name))
        
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
        name_label.setStyleSheet("""
            font-size: 12px;
            font-weight: bold;
            color: #cccccc;
            padding: 4px;
            background: #252525;
        """)
        self.content_layout.addWidget(name_label)

        # ID
        id_label = QLabel(f"ID: {obj.get('id', 'N/A')[:8]}...")
        id_label.setStyleSheet("color: #444444; font-size: 9px; padding-left: 4px;")
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

        # Determine available components
        available = []
        all_components = [
            "Transform", "SpriteRenderer", "Script", "RigidBody", 
            "BoxCollider", "CircleCollider", "Camera", "LightSource", "Background", "TextRenderer"
        ]
        
        for c in all_components:
            if c not in components:
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

    def add_background_editor(self, data, obj):
        if data is None: data = {}
        self.content_layout.addWidget(self.create_header("Background", obj, "Background"))

        form = QFormLayout()
        form.setContentsMargins(8, 4, 4, 4)
        form.setSpacing(2)
        form.setLabelAlignment(Qt.AlignRight)

        # Sprite
        path_row = QHBoxLayout()
        current_path = data.get("sprite_path", "")
        path_label = QLabel(os.path.basename(current_path) if current_path else "(none)")
        path_label.setStyleSheet("color: #999999; font-size: 10px;")
        browse_btn = QPushButton("...")
        browse_btn.setFixedSize(24, 18)
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
        layer = data.get("layer", -100)
        layer_field = FloatField(layer)
        layer_field.value_committed.connect(lambda v: self.update_component(obj, "Background", "layer", int(v)))
        form.addRow(QLabel("Layer:"), layer_field)

        form_widget = QWidget()
        form_widget.setLayout(form)
        self.content_layout.addWidget(form_widget)
    
    def pick_image_generic(self, obj, comp_name, key, label_widget):
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
        layer = data.get("layer", -100)
        layer_field = FloatField(layer)
        layer_field.value_committed.connect(lambda v: self.update_component(obj, "Background", "layer", int(v)))
        form.addRow(QLabel("Layer:"), layer_field)

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
        form.setContentsMargins(8, 4, 4, 4)
        form.setSpacing(4)
        form.setLabelAlignment(Qt.AlignRight)

        # Position
        pos = data.get("position", [0, 0])
        pos_field = Vec2Field(pos[0], pos[1])
        pos_field.value_edited.connect(lambda x, y: self.preview_transform(obj, "position", (x, y)))
        pos_field.value_committed.connect(lambda nx, ny, ox, oy: self.commit_transform(obj, "position", (nx, ny), (ox, oy)))
        
        pos_label = QLabel("Position:")
        pos_label.setStyleSheet("color: #666666; font-size: 10px;")
        form.addRow(pos_label, pos_field)
        self.active_editors[("Transform", "position")] = pos_field

        # Rotation
        rot = data.get("rotation", 0)
        rot_field = FloatField(rot)
        rot_field.value_edited.connect(lambda v: self.preview_transform(obj, "rotation", v))
        rot_field.value_committed.connect(lambda n, o: self.commit_transform(obj, "rotation", n, o))
        
        rot_label = QLabel("Rotation:")
        rot_label.setStyleSheet("color: #666666; font-size: 10px;")
        form.addRow(rot_label, rot_field)
        self.active_editors[("Transform", "rotation")] = rot_field

        # Scale
        scale = data.get("scale", [1, 1])
        scale_field = Vec2Field(scale[0], scale[1])
        scale_field.value_edited.connect(lambda x, y: self.preview_transform(obj, "scale", (x, y)))
        scale_field.value_committed.connect(lambda nx, ny, ox, oy: self.commit_transform(obj, "scale", (nx, ny), (ox, oy)))
        
        scale_label = QLabel("Scale:")
        scale_label.setStyleSheet("color: #666666; font-size: 10px;")
        form.addRow(scale_label, scale_field)
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
        form.setContentsMargins(8, 4, 4, 4)
        form.setSpacing(2)
        form.setLabelAlignment(Qt.AlignRight)

        if isinstance(data, dict):
            for key, value in data.items():
                key_label = QLabel(f"{key}:")
                key_label.setStyleSheet("color: #666666; font-size: 10px;")
                
                val_label = QLabel(str(value))
                val_label.setStyleSheet("color: #999999; font-size: 10px;")
                val_label.setWordWrap(True)
                
                form.addRow(key_label, val_label)
        
        form_widget = QWidget()
        form_widget.setLayout(form)
        self.content_layout.addWidget(form_widget)

    def add_sprite_editor(self, data, obj):
        self.content_layout.addWidget(self.create_header("SpriteRenderer", obj, "SpriteRenderer"))

        form = QFormLayout()
        form.setContentsMargins(8, 4, 4, 4)
        form.setSpacing(4)
        form.setLabelAlignment(Qt.AlignRight)

        # Sprite path
        path_row = QHBoxLayout()
        path_row.setSpacing(4)
        
        current_path = data.get("sprite_path", "")
        path_label = QLabel(os.path.basename(current_path) if current_path else "(none)")
        path_label.setStyleSheet("color: #999999; font-size: 10px;")
        path_label.setFixedWidth(100)
        
        browse_btn = QPushButton("...")
        browse_btn.setFixedSize(24, 18)
        # Use generic picker
        browse_btn.clicked.connect(lambda: self.pick_image_generic(obj, "SpriteRenderer", "sprite_path", path_label))
        
        path_row.addWidget(path_label)
        path_row.addWidget(browse_btn)
        path_row.addStretch()
        
        path_widget = QWidget()
        path_widget.setLayout(path_row)
        
        sprite_label = QLabel("Sprite:")
        sprite_label.setStyleSheet("color: #666666; font-size: 10px;")
        form.addRow(sprite_label, path_widget)

        # Layer
        layer = data.get("layer", 0)
        layer_field = FloatField(layer)
        layer_field.setFixedWidth(40)
        layer_field.value_edited.connect(lambda v: self.preview_component(obj, "SpriteRenderer", "layer", int(v)))
        layer_field.value_committed.connect(lambda v: self.update_component(obj, "SpriteRenderer", "layer", int(v)))
        
        layer_label = QLabel("Layer:")
        layer_label.setStyleSheet("color: #666666; font-size: 10px;")
        form.addRow(layer_label, layer_field)

        # Visible
        visible = data.get("visible", True)
        visible_check = QCheckBox()
        visible_check.setChecked(visible)
        visible_check.stateChanged.connect(lambda s: self.update_sprite(obj, "visible", s == 2))
        
        visible_label = QLabel("Visible:")
        visible_label.setStyleSheet("color: #666666; font-size: 10px;")
        form.addRow(visible_label, visible_check)

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
        form.setContentsMargins(8, 4, 4, 4)
        form.setSpacing(2)
        
        # Script path row
        current_path = data.get("script_path", "")
        
        path_widget = QWidget()
        path_layout = QHBoxLayout(path_widget)
        path_layout.setContentsMargins(0, 0, 0, 0)
        path_layout.setSpacing(4)
        
        path_label = QLabel(os.path.basename(current_path) if current_path else "(none)")
        path_label.setStyleSheet("color: #aaaaaa; background: #222222; border-radius: 2px; padding: 2px 4px;")
        path_label.setFixedHeight(22)
        
        browse_btn = QPushButton("...")
        browse_btn.setFixedSize(24, 22)
        browse_btn.setStyleSheet("background: #333333; color: white; border: none;")
        # browse_btn.clicked.connect(lambda: self.pick_script(obj, path_label)) # Old
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
        form.setContentsMargins(8, 4, 4, 4)
        form.setSpacing(2)
        form.setLabelAlignment(Qt.AlignRight)

        # Mass
        mass = data.get("mass", 1.0)
        mass_field = FloatField(mass, min_val=0.001) # Prevent zero mass
        mass_field.value_edited.connect(lambda v: self.preview_component(obj, "RigidBody", "mass", v))
        mass_field.value_committed.connect(lambda v: self.update_component(obj, "RigidBody", "mass", v))
        
        mass_label = QLabel("Mass:")
        mass_label.setStyleSheet("color: #666666; font-size: 10px;")
        form.addRow(mass_label, mass_field)
        self.active_editors[("RigidBody", "mass")] = mass_field

        # Drag
        drag = data.get("drag", 0.0)
        drag_field = FloatField(drag, min_val=0.0)
        drag_field.value_edited.connect(lambda v: self.preview_component(obj, "RigidBody", "drag", v))
        drag_field.value_committed.connect(lambda v: self.update_component(obj, "RigidBody", "drag", v))
        
        drag_label = QLabel("Drag:")
        drag_label.setStyleSheet("color: #666666; font-size: 10px;")
        form.addRow(drag_label, drag_field)
        self.active_editors[("RigidBody", "drag")] = drag_field

        # Use Gravity
        use_gravity = data.get("use_gravity", True)
        gravity_check = QCheckBox()
        gravity_check.setChecked(use_gravity)
        gravity_check.stateChanged.connect(lambda s: self.update_component(obj, "RigidBody", "use_gravity", s == 2))
        
        gravity_label = QLabel("Use Gravity:")
        gravity_label.setStyleSheet("color: #666666; font-size: 10px;")
        form.addRow(gravity_label, gravity_check)

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
        form.setContentsMargins(8, 4, 4, 4)
        form.setSpacing(2)
        form.setLabelAlignment(Qt.AlignRight)

        # Size
        size = data.get("size", [50.0, 50.0])
        size_field = Vec2Field(size[0], size[1], labels=("W", "H"))
        size_field.value_edited.connect(lambda w, h: self.preview_component(obj, "BoxCollider", "size", [w, h]))
        size_field.value_committed.connect(lambda w, h: self.update_component(obj, "BoxCollider", "size", [w, h]))
        
        size_label = QLabel("Size:")
        size_label.setStyleSheet("color: #666666; font-size: 10px;")
        form.addRow(size_label, size_field)
        self.active_editors[("BoxCollider", "size")] = size_field

        # Offset
        offset = data.get("offset", [0.0, 0.0])
        offset_field = Vec2Field(offset[0], offset[1])
        offset_field.value_edited.connect(lambda x, y: self.preview_component(obj, "BoxCollider", "offset", [x, y]))
        offset_field.value_committed.connect(lambda x, y: self.update_component(obj, "BoxCollider", "offset", [x, y]))
        
        offset_label = QLabel("Offset:")
        offset_label.setStyleSheet("color: #666666; font-size: 10px;")
        form.addRow(offset_label, offset_field)
        self.active_editors[("BoxCollider", "offset")] = offset_field

        # Is Trigger
        is_trigger = data.get("is_trigger", False)
        trigger_check = QCheckBox()
        trigger_check.setChecked(is_trigger)
        trigger_check.stateChanged.connect(lambda s: self.update_component(obj, "BoxCollider", "is_trigger", s == 2))
        
        trigger_label = QLabel("Is Trigger:")
        trigger_label.setStyleSheet("color: #666666; font-size: 10px;")
        form.addRow(trigger_label, trigger_check)

        # Sync Button
        if "SpriteRenderer" in obj.get("components", {}):
            sync_btn = QPushButton("Snap to Visual Size")
            sync_btn.setFixedHeight(20)
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
        defaults = {
            "SpriteRenderer": {"sprite_path": "", "layer": 0, "visible": True, "tint": [255, 255, 255, 255]},
            "BoxCollider": {"size": [50.0, 50.0], "offset": [0.0, 0.0], "is_trigger": False},
            "CircleCollider": {"radius": 25.0, "offset": [0.0, 0.0], "is_trigger": False},
            "RigidBody": {"mass": 1.0, "drag": 0.0, "use_gravity": True, "restitution": 0.5, "velocity": [0.0, 0.0]},
            "Script": {"script_path": ""},
            "Camera": {"width": 800.0, "height": 600.0, "zoom": 1.0, "is_main": True},
            "LightSource": {"color": [255, 255, 255, 255], "intensity": 1.0, "radius": 200.0, "type": "point"}
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
        form.setContentsMargins(8, 4, 4, 4)
        form.setSpacing(2)
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
        cat_field = FloatField(cat) # Using FloatField as IntField for simplicity MVP
        cat_field.value_committed.connect(lambda v: self.update_component(obj, "CircleCollider", "category_bitmask", int(v)))
        form.addRow(QLabel("Category (Bitmask):"), cat_field)

        # Mask
        mask = data.get("collision_mask", 0xFFFFFFFF)
        mask_field = FloatField(mask)
        mask_field.value_committed.connect(lambda v: self.update_component(obj, "CircleCollider", "collision_mask", int(v)))
        form.addRow(QLabel("Mask (Bitmask):"), mask_field)

        form_widget = QWidget()
        form_widget.setLayout(form)
        self.content_layout.addWidget(form_widget)

    def add_box_collider_editor(self, data, obj):
        if data is None: data = {}
        self.content_layout.addWidget(self.create_header("BoxCollider", obj, "BoxCollider"))

        form = QFormLayout()
        form.setContentsMargins(8, 4, 4, 4)
        form.setSpacing(2)
        form.setLabelAlignment(Qt.AlignRight)

        # Size
        size = data.get("size", [50.0, 50.0])
        size_field = Vec2Field(size[0], size[1], labels=("W", "H"))
        size_field.value_committed.connect(lambda w, h, ow, oh: self.update_component(obj, "BoxCollider", "size", [w, h]))
        form.addRow(QLabel("Size:"), size_field)

        # Offset
        offset = data.get("offset", [0.0, 0.0])
        offset_field = Vec2Field(offset[0], offset[1])
        offset_field.value_committed.connect(lambda x, y, ox, oy: self.update_component(obj, "BoxCollider", "offset", [x, y]))
        form.addRow(QLabel("Offset:"), offset_field)

        # Is Trigger
        is_trigger = data.get("is_trigger", False)
        trigger_check = QCheckBox()
        trigger_check.setChecked(is_trigger)
        trigger_check.stateChanged.connect(lambda s: self.update_component(obj, "BoxCollider", "is_trigger", s == 2))
        form.addRow(QLabel("Is Trigger:"), trigger_check)
        
        # Category
        cat = data.get("category_bitmask", 1)
        cat_field = FloatField(cat) 
        cat_field.value_committed.connect(lambda v: self.update_component(obj, "BoxCollider", "category_bitmask", int(v)))
        form.addRow(QLabel("Category (Bitmask):"), cat_field)

        # Mask
        mask = data.get("collision_mask", 0xFFFFFFFF)
        mask_field = FloatField(mask)
        mask_field.value_committed.connect(lambda v: self.update_component(obj, "BoxCollider", "collision_mask", int(v)))
        form.addRow(QLabel("Mask (Bitmask):"), mask_field)

        form_widget = QWidget()
        form_widget.setLayout(form)
        self.content_layout.addWidget(form_widget)
        if data is None: data = {}
        self.content_layout.addWidget(self.create_header("LightSource", obj, "LightSource"))

        form = QFormLayout()
        form.setContentsMargins(8, 4, 4, 4)
        form.setSpacing(2)
        form.setLabelAlignment(Qt.AlignRight)

        # Color
        color = data.get("color", [255, 255, 255, 255])
        col_field = ColorField(tuple(color))
        col_field.value_changed.connect(lambda c: self.update_component(obj, "LightSource", "color", c))
        form.addRow(QLabel("Color:"), col_field)

        # Intensity
        intensity = data.get("intensity", 1.0)
        int_field = FloatField(intensity)
        int_field.value_edited.connect(lambda v: self.preview_component(obj, "LightSource", "intensity", v))
        int_field.value_committed.connect(lambda v: self.update_component(obj, "LightSource", "intensity", v))
        form.addRow(QLabel("Intensity:"), int_field)

        # Radius
        radius = data.get("radius", 200.0)
        rad_field = FloatField(radius)
        rad_field.value_edited.connect(lambda v: self.preview_component(obj, "LightSource", "radius", v))
        rad_field.value_committed.connect(lambda v: self.update_component(obj, "LightSource", "radius", v))
        form.addRow(QLabel("Radius:"), rad_field)

        form_widget = QWidget()
        form_widget.setLayout(form)
        self.content_layout.addWidget(form_widget)

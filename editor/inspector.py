from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame, 
    QFormLayout, QLineEdit, QHBoxLayout, QPushButton, QFileDialog, QCheckBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDoubleValidator
from editor.editor_state import EditorState
import os

class FloatField(QLineEdit):
    """Compact float input field."""
    value_changed = Signal(float)
    
    def __init__(self, value=0.0):
        super().__init__()
        self.setValidator(QDoubleValidator())
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
        self.setText(str(value))
        self.editingFinished.connect(self._emit_value)
    
    def _emit_value(self):
        try:
            self.value_changed.emit(float(self.text()))
        except ValueError:
            pass

    def set_value(self, v):
        self.blockSignals(True)
        self.setText(f"{v:.2f}")
        self.blockSignals(False)


class Vec2Field(QWidget):
    """X/Y input pair."""
    value_changed = Signal(float, float)
    
    def __init__(self, x=0.0, y=0.0, labels=("X", "Y")):
        super().__init__()
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
        
        self.x_field.value_changed.connect(lambda v: self._emit())
        self.y_field.value_changed.connect(lambda v: self._emit())
    
    def _emit(self):
        try:
            x = float(self.x_field.text())
            y = float(self.y_field.text())
            self.value_changed.emit(x, y)
        except ValueError:
            pass

    def set_value(self, x, y):
        self.x_field.set_value(x)
        self.y_field.set_value(y)


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
        from PySide6.QtWidgets import QColorDialog
        from PySide6.QtGui import QColor
        r, g, b, a = self.color
        cur = QColor(r, g, b, a)
        
        c = QColorDialog.getColor(cur, self, "Pick Tint", QColorDialog.ShowAlphaChannel)
        if c.isValid():
            self.color = (c.red(), c.green(), c.blue(), c.alpha())
            self._update_style()
            self.value_changed.emit(list(self.color))

    def set_value(self, c):
        self.color = tuple(c)
        self._update_style()


class InspectorPanel(QWidget):
    # ... existing init ...

    # ... existing add_transform ...

    def add_sprite_renderer_editor(self, data, obj):
        header = QLabel("SpriteRenderer")
        header.setStyleSheet("font-weight: bold; color: #777777; padding: 6px 4px 2px 4px; border-top: 1px solid #333333;")
        self.content_layout.addWidget(header)

        form = QFormLayout()
        form.setContentsMargins(8, 4, 4, 4)
        form.setSpacing(2)
        form.setLabelAlignment(Qt.AlignRight)

        # Path Row
        path_layout = QHBoxLayout()
        path_edit = QLineEdit(data.get("sprite_path", ""))
        path_edit.setReadOnly(True)
        path_edit.setStyleSheet("color: #888; background: #222; border: 1px solid #333;")
        
        browse_btn = QPushButton("...")
        browse_btn.setFixedWidth(24)
        browse_btn.clicked.connect(lambda: self.pick_sprite(obj))

        path_layout.addWidget(path_edit)
        path_layout.addWidget(browse_btn)
        
        form.addRow(QLabel("Path:"), path_layout)

        # Layer
        layer = data.get("layer", 0)
        layer_field = FloatField(layer) # Reuse float field for int for now, or make IntField
        layer_field.value_changed.connect(lambda v: self.update_component(obj, "SpriteRenderer", "layer", int(v)))
        form.addRow(QLabel("Layer:"), layer_field)

        # Visible
        visible = data.get("visible", True)
        vis_check = QCheckBox()
        vis_check.setChecked(visible)
        vis_check.stateChanged.connect(lambda s: self.update_component(obj, "SpriteRenderer", "visible", s == 2))
        form.addRow(QLabel("Visible:"), vis_check)

        # Tint
        tint = data.get("tint", [255, 255, 255, 255])
        col_field = ColorField(tuple(tint))
        col_field.value_changed.connect(lambda c: self.update_component(obj, "SpriteRenderer", "tint", c))
        form.addRow(QLabel("Tint:"), col_field)

        form_widget = QWidget()
        form_widget.setLayout(form)
        self.content_layout.addWidget(form_widget)
    
    def add_box_collider_editor(self, data, obj):
        if data is None: data = {}
        header = QLabel("BoxCollider")
        header.setStyleSheet("font-weight: bold; color: #777777; padding: 6px 4px 2px 4px; border-top: 1px solid #333333;")
        self.content_layout.addWidget(header)

        form = QFormLayout()
        form.setContentsMargins(8, 4, 4, 4)
        form.setSpacing(2)
        form.setLabelAlignment(Qt.AlignRight)

        # Size
        size = data.get("size", [50.0, 50.0])
        size_field = Vec2Field(size[0], size[1], labels=("W", "H"))
        size_field.value_changed.connect(lambda w, h: self.update_component(obj, "BoxCollider", "size", [w, h]))
        
        size_label = QLabel("Size:")
        size_label.setStyleSheet("color: #666666; font-size: 10px;")
        form.addRow(size_label, size_field)

        # Sync Button
        sync_btn = QPushButton("Sync Valid Size")
        sync_btn.setToolTip("Sets collider size to match the sprite's current world size")
        sync_btn.clicked.connect(lambda: self.sync_collider_size(obj))
        form.addRow(QLabel(""), sync_btn)

        # Offset
        offset = data.get("offset", [0.0, 0.0])
        
        # ... rest of offset ... 

    def sync_collider_size(self, obj):
        # Calculate size from sprite
        comps = obj.get("components", {})
        spr = comps.get("SpriteRenderer")
        head_transform = comps.get("Transform")
        
        if not spr or not spr.get("sprite_path"):
            return
            
        path = os.path.join(EditorState.instance().project_root, spr["sprite_path"])
        if not os.path.exists(path):
            return
            
        from PySide6.QtGui import QPixmap
        pix = QPixmap(path)
        if pix.isNull():
            return
            
        w, h = pix.width(), pix.height()
        
        # Apply Scale
        sx, sy = head_transform.get("scale", [1.0, 1.0])
        final_w = w * abs(sx)
        final_h = h * abs(sy)
        
        # Update Collider
        self.update_component(obj, "BoxCollider", "size", [final_w, final_h])
        # Refresh UI happens automatically via update_component logic? 
        # Wait, update_component rebuilds inspector? No. 
        # But modify component triggers re-build usually if selection changes?
        # Actually inspector 'update_component' just sets data. 
        # I should probably triggering a rebuild or manually updating the field.
        # For now, forcing a rebuild is easiest.
        self.build_inspector(obj)
        
        self.container = QWidget()
        self.content_layout = QVBoxLayout(self.container)
        self.content_layout.setContentsMargins(6, 6, 6, 6)
        self.content_layout.setSpacing(4)
        self.content_layout.setAlignment(Qt.AlignTop)
        
        scroll.setWidget(self.container)
        main_layout.addWidget(scroll)
        
        self.show_placeholder("No selection")

        self.state = EditorState.instance()
        self.state.selection_changed.connect(self.on_selection_changed)

    def on_selection_changed(self, obj_id):
        self.clear_content()
        
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

    def show_placeholder(self, text):
        placeholder = QLabel(text)
        placeholder.setStyleSheet("color: #555555; padding: 10px;")
        placeholder.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(placeholder)

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

            else:
                self.add_component_section(comp_name, comp_data)

        # Add Component button
        self.add_component_button(obj)

        self.content_layout.addStretch()

    def add_transform_editor(self, data, obj):
        header = QLabel("Transform")
        header.setStyleSheet("""
            font-weight: bold;
            color: #777777;
            padding: 6px 4px 2px 4px;
            border-bottom: 1px solid #333333;
            margin-top: 6px;
            font-size: 10px;
        """)
        self.content_layout.addWidget(header)

        form = QFormLayout()
        form.setContentsMargins(8, 4, 4, 4)
        form.setSpacing(4)
        form.setLabelAlignment(Qt.AlignRight)

        # Position
        pos = data.get("position", [0, 0])
        pos_field = Vec2Field(pos[0], pos[1])
        pos_field.value_changed.connect(lambda x, y: self.update_transform(obj, "position", (x, y)))
        
        pos_label = QLabel("Position:")
        pos_label.setStyleSheet("color: #666666; font-size: 10px;")
        form.addRow(pos_label, pos_field)

        # Rotation
        rot = data.get("rotation", 0)
        rot_field = FloatField(rot)
        rot_field.value_changed.connect(lambda v: self.update_transform(obj, "rotation", v))
        
        rot_label = QLabel("Rotation:")
        rot_label.setStyleSheet("color: #666666; font-size: 10px;")
        form.addRow(rot_label, rot_field)

        # Scale
        scale = data.get("scale", [1, 1])
        scale_field = Vec2Field(scale[0], scale[1])
        scale_field.value_changed.connect(lambda x, y: self.update_transform(obj, "scale", (x, y)))
        
        scale_label = QLabel("Scale:")
        scale_label.setStyleSheet("color: #666666; font-size: 10px;")
        form.addRow(scale_label, scale_field)

        form_widget = QWidget()
        form_widget.setLayout(form)
        self.content_layout.addWidget(form_widget)

    def update_transform(self, obj, key, value):
        if "Transform" in obj.get("components", {}):
            if isinstance(value, tuple):
                obj["components"]["Transform"][key] = list(value)
            else:
                obj["components"]["Transform"][key] = value
            # Emit signal for canvas refresh
            self.state.scene_loaded.emit()

    def add_component_section(self, name, data):
        header = QLabel(name)
        header.setStyleSheet("""
            font-weight: bold;
            color: #777777;
            padding: 6px 4px 2px 4px;
            border-bottom: 1px solid #333333;
            margin-top: 6px;
            font-size: 10px;
        """)
        self.content_layout.addWidget(header)

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
        header = QLabel("SpriteRenderer")
        header.setStyleSheet("""
            font-weight: bold;
            color: #777777;
            padding: 6px 4px 2px 4px;
            border-bottom: 1px solid #333333;
            margin-top: 6px;
            font-size: 10px;
        """)
        self.content_layout.addWidget(header)

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
        browse_btn.setFixedWidth(24)
        browse_btn.clicked.connect(lambda: self.pick_sprite(obj, path_label))
        
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
        layer_field.value_changed.connect(lambda v: self.update_sprite(obj, "layer", int(v)))
        
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

        form_widget = QWidget()
        form_widget.setLayout(form)
        self.content_layout.addWidget(form_widget)

    def pick_sprite(self, obj, label_widget):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Sprite", 
            os.path.join(self.state.project_root, "assets", "sprites"),
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if path:
            # Check if file is inside project
            try:
                rel_path = os.path.relpath(path, self.state.project_root)
                # Check if it escapes the project (starts with ..)
                if rel_path.startswith("..") or os.path.isabs(rel_path):
                    raise ValueError("Outside project")
            except ValueError:
                # File is outside project - copy it to assets/sprites
                import shutil
                dest_dir = os.path.join(self.state.project_root, "assets", "sprites")
                os.makedirs(dest_dir, exist_ok=True)
                
                filename = os.path.basename(path)
                dest_path = os.path.join(dest_dir, filename)
                
                # Handle duplicates
                counter = 1
                base, ext = os.path.splitext(filename)
                while os.path.exists(dest_path):
                    dest_path = os.path.join(dest_dir, f"{base}_{counter}{ext}")
                    counter += 1
                
                shutil.copy2(path, dest_path)
                rel_path = os.path.relpath(dest_path, self.state.project_root)
            
            self.update_sprite(obj, "sprite_path", rel_path)
            label_widget.setText(os.path.basename(rel_path))

    def update_sprite(self, obj, key, value):
        if "SpriteRenderer" not in obj.get("components", {}):
            obj["components"]["SpriteRenderer"] = {}
        obj["components"]["SpriteRenderer"][key] = value
        self.state.scene_loaded.emit()

    def add_script_editor(self, data, obj):
        header = QLabel("Script")
        header.setStyleSheet("""
            font-weight: bold;
            color: #777777;
            padding: 6px 4px 2px 4px;
            border-top: 1px solid #333333;
        """)
        self.content_layout.addWidget(header)

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
        browse_btn.clicked.connect(lambda: self.pick_script(obj, path_label))
        
        path_layout.addWidget(path_label)
        path_layout.addWidget(browse_btn)
        
        form.addRow("Script:", path_widget)
        
        form_widget = QWidget()
        form_widget.setLayout(form)
        self.content_layout.addWidget(form_widget)

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
        if "RigidBody" not in components:
            available.append("RigidBody")
        if "Script" not in components:
            available.append("Script")
        if "Camera" not in components:
            available.append("Camera")
        
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
        header = QLabel("Camera")
        header.setStyleSheet("font-weight: bold; color: #777777; padding: 6px 4px 2px 4px; border-top: 1px solid #333333;")
        self.content_layout.addWidget(header)

        form = QFormLayout()
        form.setContentsMargins(8, 4, 4, 4)
        form.setSpacing(2)
        form.setLabelAlignment(Qt.AlignRight)
        
        # Size
        width = data.get("width", 800.0)
        height = data.get("height", 600.0)
        size_field = Vec2Field(width, height, labels=("W", "H"))
        size_field.value_changed.connect(lambda w, h: [self.update_component(obj, "Camera", "width", w), self.update_component(obj, "Camera", "height", h)])
        form.addRow(QLabel("Size:"), size_field)

        # Zoom
        zoom = data.get("zoom", 1.0)
        zoom_field = FloatField(zoom)
        zoom_field.value_changed.connect(lambda v: self.update_component(obj, "Camera", "zoom", v))
        form.addRow(QLabel("Zoom:"), zoom_field)
        
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
        header = QLabel("RigidBody")
        header.setStyleSheet("font-weight: bold; color: #777777; padding: 6px 4px 2px 4px; border-top: 1px solid #333333;")
        self.content_layout.addWidget(header)

        form = QFormLayout()
        form.setContentsMargins(8, 4, 4, 4)
        form.setSpacing(2)
        form.setLabelAlignment(Qt.AlignRight)

        # Mass
        mass = data.get("mass", 1.0)
        mass_field = FloatField(mass)
        mass_field.value_changed.connect(lambda v: self.update_component(obj, "RigidBody", "mass", v))
        
        mass_label = QLabel("Mass:")
        mass_label.setStyleSheet("color: #666666; font-size: 10px;")
        form.addRow(mass_label, mass_field)

        # Drag
        drag = data.get("drag", 0.0)
        drag_field = FloatField(drag)
        drag_field.value_changed.connect(lambda v: self.update_component(obj, "RigidBody", "drag", v))
        
        drag_label = QLabel("Drag:")
        drag_label.setStyleSheet("color: #666666; font-size: 10px;")
        form.addRow(drag_label, drag_field)

        # Restitution
        restitution = data.get("restitution", 0.5)
        res_field = FloatField(restitution)
        res_field.value_changed.connect(lambda v: self.update_component(obj, "RigidBody", "restitution", v))
        
        res_label = QLabel("Bounciness:")
        res_label.setStyleSheet("color: #666666; font-size: 10px;")
        form.addRow(res_label, res_field)

        # Use Gravity
        use_gravity = data.get("use_gravity", True)
        gravity_check = QCheckBox()
        gravity_check.setChecked(use_gravity)
        gravity_check.stateChanged.connect(lambda s: self.update_component(obj, "RigidBody", "use_gravity", s == 2))
        
        gravity_label = QLabel("Use Gravity:")
        gravity_label.setStyleSheet("color: #666666; font-size: 10px;")
        form.addRow(gravity_label, gravity_check)

        form_widget = QWidget()
        form_widget.setLayout(form)
        self.content_layout.addWidget(form_widget)

    def add_box_collider_editor(self, data, obj):
        if data is None: data = {}
        header = QLabel("BoxCollider")
        header.setStyleSheet("font-weight: bold; color: #777777; padding: 6px 4px 2px 4px; border-top: 1px solid #333333;")
        self.content_layout.addWidget(header)

        form = QFormLayout()
        form.setContentsMargins(8, 4, 4, 4)
        form.setSpacing(2)
        form.setLabelAlignment(Qt.AlignRight)

        # Size
        size = data.get("size", [50.0, 50.0])
        size_field = Vec2Field(size[0], size[1], labels=("W", "H"))
        size_field.value_changed.connect(lambda w, h: self.update_component(obj, "BoxCollider", "size", [w, h]))
        
        size_label = QLabel("Size:")
        size_label.setStyleSheet("color: #666666; font-size: 10px;")
        form.addRow(size_label, size_field)

        # Offset
        offset = data.get("offset", [0.0, 0.0])
        offset_field = Vec2Field(offset[0], offset[1])
        offset_field.value_changed.connect(lambda x, y: self.update_component(obj, "BoxCollider", "offset", [x, y]))
        
        offset_label = QLabel("Offset:")
        offset_label.setStyleSheet("color: #666666; font-size: 10px;")
        form.addRow(offset_label, offset_field)

        # Is Trigger
        is_trigger = data.get("is_trigger", False)
        trigger_check = QCheckBox()
        trigger_check.setChecked(is_trigger)
        trigger_check.stateChanged.connect(lambda s: self.update_component(obj, "BoxCollider", "is_trigger", s == 2))
        
        trigger_label = QLabel("Is Trigger:")
        trigger_label.setStyleSheet("color: #666666; font-size: 10px;")
        form.addRow(trigger_label, trigger_check)

        form_widget = QWidget()
        form_widget.setLayout(form)
        self.content_layout.addWidget(form_widget)

    def update_component(self, obj, comp_name, key, value):
        if comp_name in obj.get("components", {}):
            obj["components"][comp_name][key] = value
            self.state.scene_loaded.emit()

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
            "RigidBody": {"mass": 1.0, "drag": 0.0, "use_gravity": True, "restitution": 0.5, "velocity": [0.0, 0.0]},
            "Script": {"script_path": ""},
            "Camera": {"width": 800.0, "height": 600.0, "zoom": 1.0, "is_main": True}
        }
        if comp_name in defaults:
            obj["components"][comp_name] = defaults[comp_name]
            self.state.select_object(obj.get("id"))  # Refresh inspector

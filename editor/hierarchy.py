from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem, 
    QPushButton, QHBoxLayout, QInputDialog, QMessageBox, QMenu
)
from PySide6.QtCore import Qt
from editor.editor_state import EditorState
from shared.scene_schema import GameObject
from editor.undo_redo import CreateObjectCommand, DeleteObjectCommand, RenameObjectCommand
from dataclasses import asdict

class HierarchyPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumWidth(160)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Compact toolbar
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(4, 4, 4, 4)
        toolbar.setSpacing(4)
        
        add_btn = QPushButton("+ Add")
        add_btn.setFixedHeight(20)
        add_btn.clicked.connect(self.show_add_menu_button)
        toolbar.addWidget(add_btn)
        toolbar.addStretch()
        
        toolbar_widget = QWidget()
        toolbar_widget.setLayout(toolbar)
        layout.addWidget(toolbar_widget)

        # Tree
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(12)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        self.tree.currentItemChanged.connect(self.on_selection_changed)
        layout.addWidget(self.tree)

        # Connect signals
        self.state = EditorState.instance()
        self.state.scene_loaded.connect(self.refresh)

    def refresh(self):
        self.tree.clear()
        scene = self.state.current_scene
        if not scene:
            return

        for obj in scene.objects:
            item = QTreeWidgetItem(self.tree)
            name = obj.get("name", "Unnamed")
            active = obj.get("active", True)
            
            if active:
                item.setText(0, name)
            else:
                item.setText(0, f"[x] {name}")
                item.setForeground(0, Qt.gray)
            
            item.setData(0, Qt.UserRole, obj.get("id"))
    
    def refresh_tree(self):
        self.refresh()
    
    def on_selection_changed(self, current, previous):
        if current:
            obj_id = current.data(0, Qt.UserRole)
            if self.state.selected_object_id != obj_id:
                self.state.select_object(obj_id)
        else:
            self.state.select_object(None)

    def show_context_menu(self, position):
        item = self.tree.itemAt(position)
        
        menu = QMenu(self)
        
        if item:
            rename_action = menu.addAction("Rename")
            rename_action.triggered.connect(lambda: self.rename_object(item))
            
            delete_action = menu.addAction("Delete")
            delete_action.triggered.connect(lambda: self.delete_object(item))
            
            menu.addSeparator()
            
            save_prefab_action = menu.addAction("Save as Prefab")
            save_prefab_action.triggered.connect(lambda: self.save_prefab(item))
        else:
            add_menu = menu.addMenu("Add Object")
            self.populate_add_menu(add_menu)
        
        menu.exec(self.tree.viewport().mapToGlobal(position))

    def show_add_menu_button(self):
        menu = QMenu(self)
        self.populate_add_menu(menu)
        menu.exec(self.sender().mapToGlobal(self.sender().rect().bottomLeft()))

    def populate_add_menu(self, menu):
        menu.addAction("Empty Object", lambda: self.add_new_object("GameObject"))
        menu.addAction("Camera", lambda: self.add_new_object("Camera", {"Camera": {}}))
        menu.addAction("Light", lambda: self.add_new_object("Light", {"LightSource": {}}))
        menu.addAction("Circle", lambda: self.add_new_object("Circle", {"CircleCollider": {}}))
        menu.addAction("Square", lambda: self.add_new_object("Square", {"SpriteRenderer": {}, "BoxCollider": {}}))

    def rename_object(self, item):
        obj_id = item.data(0, Qt.UserRole)
        obj = self.state.get_object_by_id(obj_id)
        if not obj:
            return
            
        old_name = obj.get("name", "GameObject")
        new_name, ok = QInputDialog.getText(self, "Rename Object", "New Name:", text=old_name)
        
        if ok and new_name:
            cmd = RenameObjectCommand(obj, new_name)
            self.state.undo_stack.push(cmd)
            cmd.redo()
            self.window().refresh_ui()

    def delete_object(self, item):
        obj_id = item.data(0, Qt.UserRole)
        scene = self.state.current_scene
        
        # Find index
        index = -1
        for i, o in enumerate(scene.objects):
            if o.get("id") == obj_id:
                index = i
                break
        
        if index != -1:
            cmd = DeleteObjectCommand(scene, index)
            self.state.undo_stack.push(cmd)
            cmd.redo()
            self.window().refresh_ui()

    def save_prefab(self, item):
        obj_id = item.data(0, Qt.UserRole)
        obj = self.state.get_object_by_id(obj_id)
        if not obj:
            return
            
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        import json
        import os
        
        # Default filename = object name
        safe_name = "".join(c for c in obj.get("name", "prefab") if c.isalnum() or c in (' ', '_', '-')).strip()
        
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Prefab",
            os.path.join(self.state.project_root, "assets", f"{safe_name}.prefab"),
            "Prefab Files (*.prefab)"
        )
        
        if path:
            print(f"Attempting to save prefab to: {path}")
            try:
                with open(path, 'w') as f:
                    json.dump(obj, f, indent=2)
                print(f"Saved prefab to {path}")
                
                # Notify asset browser to refresh
                self.state.scene_loaded.emit() 
                
            except Exception as e:
                print(f"Error saving prefab: {e}")
                QMessageBox.critical(self, "Error", f"Failed to save prefab:\n{e}")

    def add_new_object(self, name="New Object", components=None):
        scene = self.state.current_scene
        if not scene:
            return
        
        new_obj = GameObject.create(name)
        if components:
            from shared.component_defs import Camera, LightSource, CircleCollider, SpriteRenderer, BoxCollider, COMPONENT_MAP
            # Helper to get defaults
            defaults = {
                "Camera": {"width": 1280, "height": 720, "zoom": 1.0, "is_main": False},
                "LightSource": {"color": [255, 255, 255, 255], "intensity": 1.0, "radius": 200.0, "type": "point"},
                "CircleCollider": {"radius": 25.0, "offset": [0.0, 0.0], "is_trigger": False},
                "SpriteRenderer": {"sprite_path": "", "layer": 0, "visible": True, "tint": [255, 255, 255, 255]},
                "BoxCollider": {"size": [50.0, 50.0], "offset": [0.0, 0.0], "is_trigger": False}
            }
            
            for comp_name, comp_data in components.items():
                # Merge defaults
                data = defaults.get(comp_name, {}).copy()
                data.update(comp_data)
                new_obj.components[comp_name] = data

        # Try to spawn at canvas center
        from editor.canvas import SceneCanvas
        # Find canvas widget through parent
        main_window = self.window()
        if main_window:
            canvas = main_window.findChild(SceneCanvas)
            if canvas:
                cx, cy = canvas.get_canvas_center()
                new_obj.components["Transform"]["position"] = [cx, cy]
        
        obj_dict = asdict(new_obj)
        cmd = CreateObjectCommand(scene, obj_dict)
        self.state.undo_stack.push(cmd)
        cmd.redo()
        
        if hasattr(main_window, "refresh_ui"):
             main_window.refresh_ui()
        else:
             self.refresh()
        
        # Select the new object
        self.state.select_object(new_obj.id)

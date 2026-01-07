from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem, 
    QPushButton, QHBoxLayout
)
from PySide6.QtCore import Qt
from editor.editor_state import EditorState
from shared.scene_schema import GameObject
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
        add_btn.clicked.connect(self.add_new_object)
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
    
    def on_selection_changed(self, current, previous):
        if current:
            obj_id = current.data(0, Qt.UserRole)
            if self.state.selected_object_id != obj_id:
                self.state.select_object(obj_id)
        else:
            self.state.select_object(None)

    def show_context_menu(self, position):
        item = self.tree.itemAt(position)
        if not item:
            return
        
        from PySide6.QtWidgets import QMenu, QInputDialog, QMessageBox
        
        # Imports locally to avoid circular dep if needed, or top-level is fine
        from editor.undo_redo import CreateObjectCommand, DeleteObjectCommand, RenameObjectCommand

        menu = QMenu(self)
        
        rename_action = menu.addAction("Rename")
        rename_action.triggered.connect(lambda: self.rename_object(item))
        
        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(lambda: self.delete_object(item))
        
        menu.addSeparator()
        
        save_prefab_action = menu.addAction("Save as Prefab")
        save_prefab_action.triggered.connect(lambda: self.save_prefab(item))
        
        menu.exec(self.tree.viewport().mapToGlobal(position))

    def rename_object(self, item):
        obj_id = item.data(0, Qt.UserRole)
        obj = self.state.get_object_by_id(obj_id)
        if not obj: return
        
        from PySide6.QtWidgets import QInputDialog
        new_name, ok = QInputDialog.getText(self, "Rename Object", "New Name:", text=obj.get("name", ""))
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

    def add_new_object(self):
        scene = self.state.current_scene
        if not scene:
            return
        
        new_obj = GameObject.create("New Object")
        
        # Try to spawn at canvas center
        from editor.canvas import SceneCanvas
        main_window = self.window()
        if main_window:
            canvas = main_window.findChild(SceneCanvas)
            if canvas:
                cx, cy = canvas.get_canvas_center()
                new_obj.components["Transform"]["position"] = [cx, cy]
        
        # Use Undo Command
        from editor.undo_redo import CreateObjectCommand
        from dataclasses import asdict
        # GameObject.create returns a class instance, but scene.objects stores dicts?
        # Let's check scene_schema.py. It seems it uses dicts in the list based on validation errors before.
        # But wait, Scene.objects is List[GameObject] or List[Dict]?
        # Checking schema... validation usually expects dicts if typed as Dict.
        # The `scene_loader` converts to dicts.
        # Let's assume we need to convert to dict for `scene.objects` if that's what it holds.
        # Checking `EditorState.load_scene`: `self.current_scene = scene` (instance of Scene).
        # `Scene` defines `objects: List[dict] = field(default_factory=list)`.
        # So yes, we should append a dict.
        
        obj_dict = asdict(new_obj)
        cmd = CreateObjectCommand(scene, obj_dict)
        self.state.undo_stack.push(cmd)
        cmd.redo()
        
        self.window().refresh_ui()
        # Select the new object
        # Since refresh rebuilds tree, we need to find it again?
        # We can select by ID
        self.state.select_object(new_obj.id)

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

        self.tree.clear()
        self.refresh()

        # Enable Drag & Drop
        self.tree.setDragEnabled(True)
        self.tree.setAcceptDrops(True)
        self.tree.setDragDropMode(QTreeWidget.InternalMove)
        self.tree.setDefaultDropAction(Qt.MoveAction)

    def refresh(self):
        self.tree.clear()
        scene = self.state.current_scene
        if not scene:
            return

        # 1. Create all items first
        item_map = {} # id -> QTreeWidgetItem
        orphans = []
        
        for obj in scene.objects:
            item = QTreeWidgetItem()
            name = obj.get("name", "Unnamed")
            active = obj.get("active", True)
            obj_id = obj.get("id")
            
            if active:
                item.setText(0, name)
            else:
                item.setText(0, f"[x] {name}")
                item.setForeground(0, Qt.gray)
            
            item.setData(0, Qt.UserRole, obj_id)
            item_map[obj_id] = item
            
        # 2. Build Tree Structure
        for obj in scene.objects:
            obj_id = obj.get("id")
            # Get Parent from Transform
            parent_id = None
            if "Transform" in obj.get("components", {}):
                parent_id = obj["components"]["Transform"].get("parent_id")

            item = item_map[obj_id]
            
            if parent_id and parent_id in item_map:
                # Attach to parent
                parent_item = item_map[parent_id]
                parent_item.addChild(item)
            else:
                # Root item (or orphan)
                self.tree.addTopLevelItem(item)
                
        self.tree.expandAll()

    def dropEvent(self, event):
        item = self.tree.currentItem() # The item being dragged
        if not item: 
            event.ignore()
            return
            
        target_item = self.tree.itemAt(event.position().toPoint())
        drop_indicator = self.tree.dropIndicatorPosition()
        
        obj_id = item.data(0, Qt.UserRole)
        # Find object data
        obj = self.state.get_object_by_id(obj_id)
        if not obj: return
        
        new_parent_id = None
        
        if target_item:
            # Dropped ON an item -> becomes child
            if drop_indicator == QTreeWidget.OnItem:
                new_parent_id = target_item.data(0, Qt.UserRole)
                if new_parent_id == obj_id:
                    event.ignore()
                    return
            
            # Dropped ABOVE/BELOW -> becomes sibling (same parent as target)
            elif drop_indicator in (QTreeWidget.AboveItem, QTreeWidget.BelowItem):
                target_obj_id = target_item.data(0, Qt.UserRole)
                target_obj = self.state.get_object_by_id(target_obj_id)
                if target_obj and "Transform" in target_obj.get("components", {}):
                    new_parent_id = target_obj["components"]["Transform"].get("parent_id")
        
        # Execute Command
        from editor.undo_redo import ReparentCommand
        cmd = ReparentCommand(self.state.current_scene, obj, new_parent_id)
        self.state.undo_stack.push(cmd)
        cmd.redo()
        
        # Refresh UI
        self.refresh()
        self.state.selection_changed.emit(obj_id) # keep selection
        event.accept()

    # Override standard drag events to allow drop
    def dragEnterEvent(self, event):
        event.accept()
        
    def dragMoveEvent(self, event):
        event.accept()
        
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
        menu.addAction("Text", lambda: self.add_new_object("Text", {"TextRenderer": {"text": "New Text", "font_size": 24, "color": [255, 255, 255]}}))
        menu.addAction("Background", lambda: self.add_new_object("Background", {"Background": {}}))

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
        
        # Command now handles finding indices and recursion
        cmd = DeleteObjectCommand(scene, obj_id)
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
                "LightSource": {"color": [255, 255, 255, 255], "intensity": 1.0, "radius": 200.0, "type": "point", "cast_shadows": True},
                "CircleCollider": {"radius": 25.0, "offset": [0.0, 0.0], "is_trigger": False, "category_bitmask": 1, "collision_mask": 4294967295},
                "SpriteRenderer": {"sprite_path": "", "layer": 1, "visible": True, "tint": [255, 255, 255, 255]},
                "BoxCollider": {"size": [50.0, 50.0], "offset": [0.0, 0.0], "is_trigger": False, "category_bitmask": 1, "collision_mask": 4294967295},
                "Background": {"sprite_path": "", "color": [255, 255, 255, 255], "loop_x": False, "loop_y": False, "scroll_speed": [0.0, 0.0], "fixed": True, "layer": 1},
                "TextRenderer": {"text": "New Text", "font_size": 24.0, "color": [255, 255, 255, 255], "layer": 1}
            }
            
            for comp_name, comp_data in components.items():
                # Merge defaults
                data = defaults.get(comp_name, {}).copy()
                data.update(comp_data)
                new_obj.components[comp_name] = data

        # Contextual Spawn: Child of selected object
        selected_id = self.state.selected_object_id
        if selected_id:
            new_obj.parent = selected_id

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

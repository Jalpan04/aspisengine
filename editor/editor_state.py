from PySide6.QtCore import QObject, Signal
from typing import Optional
import os
import sys

# Ensure shared modules are visible
sys.path.append(os.getcwd())

from shared.scene_schema import Scene, GameObject
from editor.undo_redo import UndoStack

from .undo_redo import UndoStack

class EditorState(QObject):
    # Signals
    scene_loaded = Signal() # Structure changed (new scene, add/remove object)
    scene_updated = Signal() # Data changed (property edit, transform)
    selection_changed = Signal(str) # object_id, empty if none
    
    _instance = None

    def __init__(self):
        super().__init__()
        self.undo_stack = UndoStack()
        self.current_scene: Optional[Scene] = None
        self.selected_object_id: Optional[str] = None
        self.current_scene_path: Optional[str] = None
        self.project_root = os.getcwd()

    def set_project_root(self, path: str):
        self.project_root = path
        # If we had signals for project change, emit them here
        print(f"Project Root set to: {self.project_root}")

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = EditorState()
        return cls._instance

    def load_scene(self, scene: Scene):
        self.current_scene = scene
        self.select_object(None)
        self.scene_loaded.emit()

    def select_object(self, object_id: Optional[str]):
        self.selected_object_id = object_id
        self.selection_changed.emit(object_id if object_id else "")

    def get_selected_object(self) -> Optional[GameObject]:
        if not self.current_scene or not self.selected_object_id:
            return None
        
        # Linear search for now, optimization later if needed
        for obj_dict in self.current_scene.objects:
            if obj_dict.get("id") == self.selected_object_id:
                return obj_dict
        return None

    def get_object_by_id(self, obj_id: str) -> Optional[GameObject]:
        if not self.current_scene or not obj_id:
            return None
        
        for obj_dict in self.current_scene.objects:
            if obj_dict.get("id") == obj_id:
                return obj_dict
        return None
    hierarchy_changed = Signal()

    def reparent_object(self, child_id: str, new_parent_id: Optional[str]):
        """Sets the parent of child_id to new_parent_id (or None for root)."""
        if not self.current_scene: return
        
        # 1. Validation
        if child_id == new_parent_id:
            print("Cannot parent object to itself.")
            return
            
        if new_parent_id:
            # Cycle Check: Walk up from new_parent. If we hit child_id, it's a cycle.
            cwd = new_parent_id
            while cwd:
                if cwd == child_id:
                    print(f"Cycle detected! Cannot make {child_id} parent of {new_parent_id}")
                    return
                parent_obj = self.get_object_by_id(cwd)
                if not parent_obj: break
                
                # Get next parent
                cwd = None
                if "Transform" in parent_obj.get("components", {}):
                    cwd = parent_obj["components"]["Transform"].get("parent_id")

        # 2. Update Transform
        child_obj = self.get_object_by_id(child_id)
        if not child_obj: return
        
        if "Transform" not in child_obj.get("components", {}):
            child_obj["components"]["Transform"] = {}
            
        # Record Undo (TODO: Make a dedicated ReparentCommand)
        old_parent = child_obj["components"]["Transform"].get("parent_id")
        
        if new_parent_id:
            child_obj["components"]["Transform"]["parent_id"] = new_parent_id
        else:
            # Remove key or set to None
            child_obj["components"]["Transform"]["parent_id"] = None
            
        print(f"Reparented {child_id} to {new_parent_id}")
        self.hierarchy_changed.emit()
        self.scene_loaded.emit() # Refresh all for now

    def get_children(self, parent_id: Optional[str]):
        """Returns list of objects that have parent_id as their parent."""
        if not self.current_scene: return []
        
        children = []
        for obj in self.current_scene.objects:
            t = obj.get("components", {}).get("Transform", {})
            p_id = t.get("parent_id")
            
            # If parent_id is None, we want root objects (p_id is None or missing)
            if parent_id is None:
                if not p_id:
                    children.append(obj)
            else:
                if p_id == parent_id:
                    children.append(obj)
        return children

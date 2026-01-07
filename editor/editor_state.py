from PySide6.QtCore import QObject, Signal
from typing import Optional
import os
import sys

# Ensure shared modules are visible
sys.path.append(os.getcwd())

from shared.scene_schema import Scene, GameObject

from .undo_redo import UndoStack

class EditorState(QObject):
    # Signals
    scene_loaded = Signal()
    selection_changed = Signal(str) # object_id, empty if none
    
    _instance = None

    def __init__(self):
        super().__init__()
        self.undo_stack = UndoStack()
        self.current_scene: Optional[Scene] = None
        self.selected_object_id: Optional[str] = None
        self.current_scene_path: Optional[str] = None
        self.project_root = os.getcwd()

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

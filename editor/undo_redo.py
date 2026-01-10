import copy
from abc import ABC, abstractmethod
from dataclasses import asdict

class Command(ABC):
    @abstractmethod
    def undo(self):
        pass

    @abstractmethod
    def redo(self):
        pass

    def merge_with(self, other) -> bool:
        """
        Attempts to merge another command into this one.
        Returns True if merged, False otherwise.
        """
        return False

class UndoStack:
    def __init__(self):
        self._history = []
        self._redo_stack = []
        self.max_history = 50

    def push(self, command: Command):
        # Try to merge with top of stack
        if self._history:
            if self._history[-1].merge_with(command):
                return # Merged successfully, no need to push or clear redo
        
        self._history.append(command)
        self._redo_stack.clear()
        if len(self._history) > self.max_history:
            self._history.pop(0)

    def undo(self):
        if not self._history:
            return
        
        cmd = self._history.pop()
        cmd.undo()
        self._redo_stack.append(cmd)

    def redo(self):
        if not self._redo_stack:
            return
            
        cmd = self._redo_stack.pop()
        cmd.redo()
        self._history.append(cmd)

    def can_undo(self):
        return len(self._history) > 0

    def can_redo(self):
        return len(self._redo_stack) > 0

class CreateObjectCommand(Command):
    def __init__(self, scene, obj_data, index=None):
        self.scene = scene
        # Deepcopy to ensure the template is isolated from future edits
        self.obj_data = copy.deepcopy(obj_data)
        self.index = index
        self.created_obj = None

    def redo(self):
        # Create a FRESH copy each time to ensure isolation
        self.created_obj = copy.deepcopy(self.obj_data)
        if self.index is not None:
            self.scene.objects.insert(self.index, self.created_obj)
        else:
            self.scene.objects.append(self.created_obj)

    def undo(self):
        if self.created_obj in self.scene.objects:
            self.scene.objects.remove(self.created_obj)

class DeleteObjectCommand(Command):
    def __init__(self, scene, target_id):
        self.scene = scene
        self.target_id = target_id
        # We store the objects themselves (dicts) to be able to restore them.
        # We must capture the WHOLE subtree at init time.
        self.objects_to_delete = [] # List of (index, object_dict)
        
        # 1. Find all descendants recursively
        to_check = [target_id]
        ids_to_delete = set()
        
        # Build set of all IDs in subtree
        while to_check:
            current_id = to_check.pop(0)
            ids_to_delete.add(current_id)
            # Find children
            for obj in self.scene.objects:
                if obj.get("parent") == current_id:
                    to_check.append(obj.get("id"))
        
        # 2. Store them with their original indices
        
        # Find all objects to delete
        for i, obj in enumerate(self.scene.objects):
            if obj.get("id") in ids_to_delete:
                # DEEPCOPY to save state exactly as it was at deletion time
                self.objects_to_delete.append((i, copy.deepcopy(obj)))
        
        # Sort by index descending so we can pop without invalidating lower indices
        self.objects_to_delete.sort(key=lambda x: x[0], reverse=True)

    def redo(self):
        # Delete from highest index to lowest
        # We need to find objects by ID or assume index integrity?
        # If other commands ran, indices might shift. 
        # But Undo/Redo is linear.
        # Wait, if I undo Delete, then I add valid commands, Redo Stack is cleared.
        # So indices should match unless I have a bug.
        for index, obj_snap in self.objects_to_delete:
            # We search for the object with matching ID at the expected index or nearby?
            # Or just blindly pop index? Safest for simple lists.
            # But if we assume linear history:
            if 0 <= index < len(self.scene.objects):
                 # Verify ID match if possible?
                 if self.scene.objects[index]["id"] == obj_snap["id"]:
                     self.scene.objects.pop(index)
                 else:
                     # Fallback: search by ID
                     for j, o in enumerate(self.scene.objects):
                         if o["id"] == obj_snap["id"]:
                             self.scene.objects.pop(j)
                             break

    def undo(self):
        # Restore in original order (ascending index)
        to_restore = sorted(self.objects_to_delete, key=lambda x: x[0])
        for index, obj_snap in to_restore:
            # Insert a COPY to ensure multiple undo/redos don't link states
            self.scene.objects.insert(index, copy.deepcopy(obj_snap))

class RenameObjectCommand(Command):
    def __init__(self, obj, new_name):
        self.obj = obj
        self.new_name = new_name
        self.old_name = obj.get("name", "GameObject")

    def redo(self):
        self.obj["name"] = self.new_name

    def undo(self):
        self.obj["name"] = self.old_name

class ChangeComponentCommand(Command):
    def __init__(self, obj, comp_name, key, new_value):
        self.obj = obj
        self.comp_name = comp_name
        self.key = key
        # DEEPCOPY values to prevent reference pollution
        self.new_value = copy.deepcopy(new_value)
        
        val = obj["components"][comp_name].get(key)
        self.old_value = copy.deepcopy(val)

    def redo(self):
        # Deepcopy on assignment too? 
        # Usually self.new_value is isolated enough, but inserting it into obj
        # means obj holds ref to it.
        # If obj modifies it, self.new_value is modified?
        # YES. So we must put deepcopy(self.new_value) into obj.
        self.obj["components"][self.comp_name][self.key] = copy.deepcopy(self.new_value)

    def undo(self):
        self.obj["components"][self.comp_name][self.key] = copy.deepcopy(self.old_value)

    def merge_with(self, other) -> bool:
        if not isinstance(other, ChangeComponentCommand):
            return False
        
        # Check if it's the exact same property on the exact same object
        if (self.obj["id"] == other.obj["id"] and 
            self.comp_name == other.comp_name and 
            self.key == other.key):
            
            # Merge: Keep MY old_value (start of drag) and take THEIR new_value (current drag pos)
            self.new_value = copy.deepcopy(other.new_value)
            return True
            
        return False

class AddComponentCommand(Command):
    def __init__(self, obj, comp_name, data):
        self.obj = obj
        self.comp_name = comp_name
        self.data = copy.deepcopy(data)

    def redo(self):
        self.obj["components"][self.comp_name] = copy.deepcopy(self.data)

    def undo(self):
        if self.comp_name in self.obj["components"]:
            del self.obj["components"][self.comp_name]

class RemoveComponentCommand(Command):
    def __init__(self, obj, comp_name):
        self.obj = obj
        self.comp_name = comp_name
        data = obj["components"].get(comp_name)
        self.old_data = copy.deepcopy(data)

    def redo(self):
        if self.comp_name in self.obj["components"]:
            del self.obj["components"][self.comp_name]

    def undo(self):
        if self.old_data:
            self.obj["components"][self.comp_name] = copy.deepcopy(self.old_data)

class ReparentCommand(Command):
    def __init__(self, scene, obj_data, new_parent_id):
        self.scene = scene
        self.obj_data = obj_data # The dict from scene.objects
        self.new_parent_id = new_parent_id
        
        # Helper to safely get/set
        if "Transform" not in self.obj_data["components"]:
             self.obj_data["components"]["Transform"] = {}
             
        self.old_parent_id = self.obj_data["components"]["Transform"].get("parent_id")
    
    def redo(self):
        self.obj_data["components"]["Transform"]["parent_id"] = self.new_parent_id
        
    def undo(self):
        self.obj_data["components"]["Transform"]["parent_id"] = self.old_parent_id

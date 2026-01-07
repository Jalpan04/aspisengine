from abc import ABC, abstractmethod

class Command(ABC):
    @abstractmethod
    def undo(self):
        pass

    @abstractmethod
    def redo(self):
        pass

class UndoStack:
    def __init__(self):
        self._history = []
        self._redo_stack = []
        self.max_history = 50

    def push(self, command: Command):
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

# Common Commands

class CreateObjectCommand(Command):
    def __init__(self, scene, obj_data, index=None):
        self.scene = scene
        self.obj_data = obj_data
        self.index = index # Optional insert index
        self.created_obj = None

    def redo(self):
        self.created_obj = self.obj_data.copy() # Simplistic, assumes obj_data is dict
        if self.index is not None:
            self.scene.objects.insert(self.index, self.created_obj)
        else:
            self.scene.objects.append(self.created_obj)
        
        # Trigger UI update logic via signaling? 
        # For now, we rely on the caller to refresh UI after undo/redo

    def undo(self):
        if self.created_obj in self.scene.objects:
            self.scene.objects.remove(self.created_obj)

class DeleteObjectCommand(Command):
    def __init__(self, scene, obj_index):
        self.scene = scene
        self.obj_index = obj_index
        self.deleted_obj = None

    def redo(self):
        if 0 <= self.obj_index < len(self.scene.objects):
            self.deleted_obj = self.scene.objects.pop(self.obj_index)

    def undo(self):
        if self.deleted_obj:
            self.scene.objects.insert(self.obj_index, self.deleted_obj)

class RenameObjectCommand(Command):
    def __init__(self, obj, new_name):
        self.obj = obj  # The dict
        self.old_name = obj.get("name", "Unnamed")
        self.new_name = new_name

    def redo(self):
        self.obj["name"] = self.new_name

    def undo(self):
        self.obj["name"] = self.old_name

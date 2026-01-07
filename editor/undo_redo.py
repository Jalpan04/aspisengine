from abc import ABC, abstractmethod
from dataclasses import asdict

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

class CreateObjectCommand(Command):
    def __init__(self, scene, obj_data, index=None):
        self.scene = scene
        self.obj_data = obj_data
        self.index = index
        self.created_obj = None

    def redo(self):
        self.created_obj = self.obj_data.copy()
        if self.index is not None:
            self.scene.objects.insert(self.index, self.created_obj)
        else:
            self.scene.objects.append(self.created_obj)

    def undo(self):
        if self.created_obj in self.scene.objects:
            self.scene.objects.remove(self.created_obj)

class DeleteObjectCommand(Command):
    def __init__(self, scene, index):
        self.scene = scene
        self.index = index
        self.deleted_obj = None

    def redo(self):
        if 0 <= self.index < len(self.scene.objects):
            self.deleted_obj = self.scene.objects.pop(self.index)

    def undo(self):
        if self.deleted_obj:
            self.scene.objects.insert(self.index, self.deleted_obj)

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
        self.new_value = new_value
        self.old_value = obj["components"][comp_name].get(key)

    def redo(self):
        self.obj["components"][self.comp_name][self.key] = self.new_value

    def undo(self):
        self.obj["components"][self.comp_name][self.key] = self.old_value

class AddComponentCommand(Command):
    def __init__(self, obj, comp_name, data):
        self.obj = obj
        self.comp_name = comp_name
        self.data = data

    def redo(self):
        self.obj["components"][self.comp_name] = self.data

    def undo(self):
        del self.obj["components"][self.comp_name]

class RemoveComponentCommand(Command):
    def __init__(self, obj, comp_name):
        self.obj = obj
        self.comp_name = comp_name
        self.old_data = obj["components"].get(comp_name)

    def redo(self):
        if self.comp_name in self.obj["components"]:
            del self.obj["components"][self.comp_name]

    def undo(self):
        if self.old_data:
            self.obj["components"][self.comp_name] = self.old_data

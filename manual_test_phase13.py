
import sys
import os
import unittest

# Ensure path
sys.path.append(os.getcwd())

from shared.scene_schema import GameObject, Scene
from shared.component_defs import CircleCollider, LightSource
from editor.undo_redo import UndoStack, AddComponentCommand, RemoveComponentCommand, ChangeComponentCommand
from dataclasses import asdict

class TestPhase13(unittest.TestCase):
    def setUp(self):
        self.scene = Scene.create_empty("Test Scene")
        self.undo_stack = UndoStack()
        obj_dataclass = GameObject.create("Test Object")
        self.scene.add_object(obj_dataclass)
        self.obj = self.scene.objects[0] # Get the dict version stored in scene

    def test_add_remove_component_undo_redo(self):
        # 1. Add CircleCollider
        print("\nTesting Add CircleCollider...")
        comp_data = asdict(CircleCollider(radius=50.0))
        cmd_add = AddComponentCommand(self.obj, "CircleCollider", comp_data)
        self.undo_stack.push(cmd_add)
        cmd_add.redo()

        self.assertIn("CircleCollider", self.obj["components"])
        self.assertEqual(self.obj["components"]["CircleCollider"]["radius"], 50.0)
        print("  Add OK")

        # 2. Modify Property (Live Update logic simulation)
        print("Testing Modify Property...")
        cmd_change = ChangeComponentCommand(self.obj, "CircleCollider", "radius", 75.0)
        self.undo_stack.push(cmd_change)
        cmd_change.redo()

        self.assertEqual(self.obj["components"]["CircleCollider"]["radius"], 75.0)
        print("  Modify OK")

        # 3. Undo Modification
        print("Testing Undo Modify...")
        self.undo_stack.undo()
        self.assertEqual(self.obj["components"]["CircleCollider"]["radius"], 50.0)
        print("  Undo Modify OK")

        # 4. Remove Component
        print("Testing Remove Component...")
        cmd_remove = RemoveComponentCommand(self.obj, "CircleCollider")
        self.undo_stack.push(cmd_remove)
        cmd_remove.redo()

        self.assertNotIn("CircleCollider", self.obj["components"])
        print("  Remove OK")

        # 5. Undo Removal
        print("Testing Undo Remove...")
        self.undo_stack.undo()
        self.assertIn("CircleCollider", self.obj["components"])
        self.assertEqual(self.obj["components"]["CircleCollider"]["radius"], 50.0)
        print("  Undo Remove OK")

        # 6. Redo Removal
        print("Testing Redo Remove...")
        self.undo_stack.redo()
        self.assertNotIn("CircleCollider", self.obj["components"])
        print("  Redo Remove OK")

    def test_new_components_defaults(self):
        print("\nTesting New Component Defaults...")
        # Light Source
        light_data = asdict(LightSource())
        cmd = AddComponentCommand(self.obj, "LightSource", light_data)
        self.undo_stack.push(cmd)
        cmd.redo()

        self.assertIn("LightSource", self.obj["components"])
        self.assertEqual(self.obj["components"]["LightSource"]["radius"], 200.0)
        self.assertEqual(self.obj["components"]["LightSource"]["color"], [255, 255, 255, 255])
        print("  LightSource Defaults OK")

if __name__ == '__main__':
    unittest.main()

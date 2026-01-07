import sys
import os
import json
# from dataclasses import asdict # No longer needed

# Ensure we can import from shared
sys.path.append(os.getcwd())

from shared.scene_schema import Scene, GameObject
from shared.component_defs import SpriteRenderer, Script
from shared.scene_loader import save_scene, load_scene
from shared.validation import validate_scene

def run_manual_test():
    print("========================================")
    print("      MANUAL TEST: PHASE 1 SCHEMA       ")
    print("========================================")
    
    # 1. VALID SCENE TEST
    print("\n[TEST 1] Creating and Saving a VALID Scene...")
    scene = Scene.create_empty("Manual Test Scene")
    
    # Create an object with a sprite
    hero = GameObject.create("Hero")
    # We point to a file that doesn't exist yet to test validation later, 
    # but for now we just want to test structure saving.
    # REPLACED asdict with model_dump
    hero.components["SpriteRenderer"] = SpriteRenderer(sprite_path="assets/sprites/hero_test.png").model_dump()
    scene.add_object(hero)
    
    save_path = "scenes/manual_test.scene.json"
    # REPLACED asdict with model_dump
    save_scene(scene.model_dump(), save_path)
    print(f"-> Scene saved to: {save_path}")
    
    # 2. LOAD TEST
    print("\n[TEST 2] Loading Scene back...")
    loaded_data = load_scene(save_path)
    print(f"-> Scene loaded. Object count: {len(loaded_data['objects'])}")
    
    # 3. VALIDATION TEST (EXPECT ERROR)
    print("\n[TEST 3] Running Validation (Should FAIL)...")
    errors = validate_scene(loaded_data, os.getcwd())
    
    if errors:
        print("-> Validation correctly found errors:")
        for e in errors:
            print(f"   [x] {e}")
    else:
        print("-> [ERROR] Validation should have failed but passed!")

    # 4. VALIDATION FIX TEST
    print("\n[TEST 4] Creating dummy asset and Validating (Should PASS)...")
    # Create the dummy file
    os.makedirs("assets/sprites", exist_ok=True)
    with open("assets/sprites/hero_test.png", "w") as f:
        f.write("dummy")
    
    errors_retry = validate_scene(loaded_data, os.getcwd())
    
    if not errors_retry:
        print("-> Validation passed! (No errors found)")
    else:
        print("-> [ERROR] Validation failed even with asset present!")
        for e in errors_retry:
            print(f"   [x] {e}")

    # Cleanup
    print("\n[CLEANUP] Removing test files...")
    if os.path.exists(save_path):
        os.remove(save_path)
    if os.path.exists("assets/sprites/hero_test.png"):
        os.remove("assets/sprites/hero_test.png")
    
    print("\n========================================")
    print("           TEST COMPLETE                ")
    print("========================================")

if __name__ == "__main__":
    run_manual_test()

import json
import sys
import os

def validate(path):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return

    try:
        with open(path, 'r') as f:
            data = json.load(f)
        print(f"SUCCESS: {path} is valid JSON.")
        
        # Check schema basics
        if "objects" not in data:
            print("WARNING: Missing 'objects' list.")
        else:
            print(f"Scene contains {len(data['objects'])} objects.")
            
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {path}")
        print(f"Line {e.lineno}, Column {e.colno}: {e.msg}")
        
        # Preview context
        try:
            with open(path, 'r') as f:
                lines = f.readlines()
            if 0 <= e.lineno - 1 < len(lines):
                print(f"Context: {lines[e.lineno-1].strip()}")
        except:
            pass

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_scene.py <path_to_scene>")
    else:
        validate(sys.argv[1])

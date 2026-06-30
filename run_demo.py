import sys
import os

# Ensure engine modules are importable
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from runtime.game_loop import run

def main():
    # Default to showcase_demo.scene.json if no argument is provided
    scene = "scenes/showcase_demo.scene.json"
    if len(sys.argv) > 1:
        scene = sys.argv[1]
        
    # Check if scene file exists
    if not os.path.exists(scene):
        # Try relative to current directory if not absolute
        candidate = os.path.join(current_dir, scene)
        if os.path.exists(candidate):
            scene = candidate
        else:
            print(f"Error: Scene file '{scene}' not found.")
            print("Available scenes in scenes/ directory:")
            scenes_dir = os.path.join(current_dir, "scenes")
            if os.path.exists(scenes_dir):
                for f in os.listdir(scenes_dir):
                    if f.endswith(".scene.json"):
                        print(f"  scenes/{f}")
            sys.exit(1)
            
    print(f"Starting Aspis Engine Demo: {os.path.basename(scene)}")
    run(scene)

if __name__ == "__main__":
    main()


import sys
import os
import argparse

# Ensure engine modules are importable
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

def main():
    parser = argparse.ArgumentParser(description="Aspis Engine")
    parser.add_argument("--run-scene", help="Scene file to play immediately (Game Mode)")
    parser.add_argument("project", nargs="?", help="Project path to open directly")
    
    # Use parse_known_args to avoid choking on Qt specific args if any leak through
    args, unknown = parser.parse_known_args()

    if args.run_scene:
        # --- GAME RUNTIME MODE ---
        from runtime.game_loop import run
        run(args.run_scene)
    else:
        # --- EDITOR MODE ---
        from editor.app import run
        run(args.project)

if __name__ == "__main__":
    main()

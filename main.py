
import sys
import os
import argparse

# Ensure engine modules are importable
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

def main():
    try:
        _main_impl()
    except Exception as e:
        import traceback
        log_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd()
        log_path = os.path.join(log_dir, "crash_log.txt")
        try:
            with open(log_path, "w") as f:
                f.write("CRITICAL EXCEPTION IN STANDALONE GAME:\n")
                f.write(f"Exception: {e}\n\n")
                traceback.print_exc(file=f)
            print(f"Logged crash to {log_path}")
        except Exception as write_err:
            print(f"Failed to write crash log: {write_err}")
        traceback.print_exc()
        raise e

def _main_impl():
    parser = argparse.ArgumentParser(description="Aspis Engine")
    parser.add_argument("--run-scene", help="Scene file to play immediately (Game Mode)")
    parser.add_argument("project", nargs="?", help="Project path to open directly")
    
    # Use parse_known_args to avoid choking on Qt specific args if any leak through
    args, unknown = parser.parse_known_args()

    # Determine paths to look for config.json
    config_paths = []
    
    # 1. External config next to executable (or main.py in dev)
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        config_paths.append(os.path.join(exe_dir, "config.json"))
    config_paths.append(os.path.join(current_dir, "config.json"))

    # Check for config.json
    start_scene = None
    for p in config_paths:
        if os.path.exists(p):
            import json
            try:
                with open(p, "r") as f:
                    cfg = json.load(f)
                start_scene = cfg.get("start_scene")
                if start_scene:
                    # If it's relative, make it relative to the config file's directory
                    if not os.path.isabs(start_scene):
                        start_scene = os.path.abspath(os.path.join(os.path.dirname(p), start_scene))
                    break
            except Exception as e:
                print(f"Error loading config at {p}: {e}")

    if start_scene:
        # --- STANDALONE GAME MODE ---
        from runtime.game_loop import run
        game_name = cfg.get("game_name", "Aspis Game")
        version = cfg.get("version", "1.0.0")
        made_by = cfg.get("made_by", "Developer")
        
        print("=========================================")
        print(f"Starting Standalone: {game_name}")
        print(f"Version: {version}")
        print(f"Made by: {made_by}")
        print("=========================================")
        
        run(start_scene)
    elif args.run_scene:
        # --- GAME RUNTIME MODE ---
        from runtime.game_loop import run
        run(args.run_scene)
    else:
        # --- EDITOR MODE ---
        from editor.app import run
        run(args.project)

if __name__ == "__main__":
    main()

import os
import sys
import json

def find_real_project_root(path):
    """
    Traverses parent directories to locate the true project root containing 
    project.json, main.py, or standard project folders (assets, scenes, scripts).
    """
    current = os.path.abspath(path)
    while True:
        if os.path.exists(os.path.join(current, "project.json")):
            return current
        if os.path.exists(os.path.join(current, "main.py")):
            return current
        
        has_dirs = any(os.path.exists(os.path.join(current, d)) for d in ["assets", "scenes", "scripts", "prefabs"])
        if has_dirs:
            return current
            
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return path

def get_pyinstaller_args(project_root, rel_scene_path, game_name, output_dir, exclude_editor=True, icon_path=None):
    """
    Constructs the list of arguments to invoke PyInstaller via python -m PyInstaller.
    """
    engine_root = os.getcwd()
    entry_py = os.path.join(engine_root, "main.py")
    
    args = [
        "-m", "PyInstaller",
        "--onefile",
        "--noconsole",
        f"--name={game_name}",
        f"--distpath={output_dir}",
        "--clean",
        "--collect-binaries=pygame",
        "--collect-binaries=pymunk"
    ]
    
    # 1. Icon Selection
    if icon_path and os.path.exists(icon_path):
        args.append(f"--icon={icon_path}")
    else:
        default_icon = os.path.join(engine_root, "logo.ico")
        if os.path.exists(default_icon):
            args.append(f"--icon={default_icon}")
            
    # 2. Exclude heavy unused packages and optional submodules to minimize file footprint
    excludes = [
        "pygame.tests",
        "pygame.examples",
        "pygame.docs",
        "numpy",
        "PIL",
        "cv2",
        "kivy",
        "kivymd",
        "playwright",
        "yt_dlp",
        "unittest",
        "sqlite3",
    ]
    
    if exclude_editor:
        excludes.extend([
            "PySide6",
            "tkinter",
            "matplotlib",
            "editor",
            "PySide6.QtCore",
            "PySide6.QtGui",
            "PySide6.QtWidgets",
            "shiboken6",
        ])
        
    for mod in excludes:
        args.append(f"--exclude-module={mod}")
        
    sep = os.pathsep
    
    # 3. Add Project Assets and configuration
    for folder in ["assets", "scenes", "scripts", "prefabs"]:
        fp = os.path.join(project_root, folder)
        if os.path.exists(fp):
            args.append(f"--add-data={fp}{sep}{folder}")
            
    # 4. Add Engine Runtime Modules
    for folder in ["runtime", "shared"]:
        fp = os.path.join(engine_root, folder)
        if os.path.exists(fp):
            args.append(f"--add-data={fp}{sep}{folder}")
            
    # 5. Add temporary config.json pointing to starting scene
    temp_config = os.path.join(project_root, "config.json")
    args.append(f"--add-data={temp_config}{sep}.")
    
    args.append(entry_py)
    return args

import sys
import os
import subprocess
from PySide6.QtWidgets import QApplication, QMainWindow, QDockWidget, QMenu, QMenuBar, QFileDialog, QMessageBox, QDialog
from PySide6.QtCore import Qt

# Ensure correct path
sys.path.append(os.getcwd())

from editor.editor_state import EditorState
from editor.canvas import SceneCanvas
from editor.hierarchy import HierarchyPanel
from editor.inspector import InspectorPanel
from editor.inspector import InspectorPanel
from editor.asset_browser import AssetBrowser
from editor.project_manager import ProjectManager
from shared.scene_schema import Scene
from shared.scene_loader import save_scene, load_scene
from dataclasses import asdict

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aspis Engine Editor")
        self.resize(1280, 720)
        
        # Initialize State
        self.state = EditorState.instance()

        # Outline & Style
        self.setup_ui()
        self.setup_menu()

        # Load empty scene on start
        self.state.load_scene(Scene.create_empty("Untitled Scene"))

    def setup_ui(self):
        # 1. Central Area (Tabs: Scene | Script)
        from PySide6.QtWidgets import QTabWidget
        from editor.code_editor import CodeEditor
        
        self.central_tabs = QTabWidget()
        self.setCentralWidget(self.central_tabs)
        
        # Tab 1: Scene Canvas
        self.canvas = SceneCanvas()
        self.central_tabs.addTab(self.canvas, "Scene")
        
        # Tab 2: Script Editor
        self.code_editor = CodeEditor()
        self.central_tabs.addTab(self.code_editor, "Script")

        # 2. Hierarchy (Left)
        self.dock_hierarchy = QDockWidget("Hierarchy", self)
        hierarchy_panel = HierarchyPanel()
        hierarchy_panel.setMinimumWidth(200)
        self.dock_hierarchy.setWidget(hierarchy_panel)
        self.dock_hierarchy.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_hierarchy)

        # 3. Inspector (Right)
        self.dock_inspector = QDockWidget("Inspector", self)
        inspector_panel = InspectorPanel()
        inspector_panel.setMinimumWidth(280)
        self.dock_inspector.setWidget(inspector_panel)
        self.dock_inspector.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_inspector)

        # 4. Asset Browser (Bottom)
        self.dock_assets = QDockWidget("Project", self)
        asset_browser = AssetBrowser(self.state.project_root)
        asset_browser.setMinimumHeight(150)
        self.dock_assets.setWidget(asset_browser)
        self.dock_assets.setAllowedAreas(Qt.BottomDockWidgetArea)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_assets)
        
        # Connect Asset Browser
        asset_browser.file_opened.connect(self.open_script)

        # Apply Theme
        self.apply_theme()
        
        # --- Play Button in Menu Bar (Right Corner) ---
        from PySide6.QtWidgets import QPushButton
        self.play_btn = QPushButton("PLAY") 
        # self.play_btn.setFixedSize(60, 22) # Remove fixed size, let style handle padding
        self.play_btn.setCursor(Qt.PointingHandCursor)
        self.play_btn.setObjectName("PlayButton")
        self.play_btn.clicked.connect(self.run_game)
        
        # This puts it in the same row as File, Edit, View
        self.menuBar().setCornerWidget(self.play_btn, Qt.TopRightCorner)

    def open_script(self, path):
        """Opens a script in the built-in editor."""
        if path.endswith(".py") or path.endswith(".json"):
            self.code_editor.load_file(path)
            self.central_tabs.setCurrentWidget(self.code_editor)


    def setup_menu(self):
        menu_bar = self.menuBar()
        
        # File Menu
        file_menu = menu_bar.addMenu("File")
        
        file_menu.addAction("Switch Project...").triggered.connect(self.switch_project)
        file_menu.addSeparator()
        
        new_action = file_menu.addAction("New Scene")
        new_action.triggered.connect(self.new_scene)
        
        open_action = file_menu.addAction("Open Scene")
        open_action.triggered.connect(self.open_scene)
        
        save_action = file_menu.addAction("Save Scene")
        save_action.triggered.connect(self.save_scene)
        
        save_as_action = file_menu.addAction("Save Scene As...")
        save_as_action.triggered.connect(self.save_scene_as)
        
        file_menu.addSeparator()
        file_menu.addAction("Exit").triggered.connect(self.close)

        # Edit Menu
        edit_menu = menu_bar.addMenu("Edit")
        undo_action = edit_menu.addAction("Undo")
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(lambda: [self.state.undo_stack.undo(), self.refresh_ui()])
        
        redo_action = edit_menu.addAction("Redo")
        redo_action.setShortcut("Ctrl+Shift+Z")
        redo_action.triggered.connect(lambda: [self.state.undo_stack.redo(), self.refresh_ui()])

        # View Menu
        view_menu = menu_bar.addMenu("View")
        view_menu.addAction(self.dock_hierarchy.toggleViewAction())
        view_menu.addAction(self.dock_inspector.toggleViewAction())
        view_menu.addAction(self.dock_assets.toggleViewAction())
        
        # Scene Menu
        scene_menu = menu_bar.addMenu("Scene")
        scene_menu.addAction("Settings").triggered.connect(self.show_scene_settings)

    def show_scene_settings(self):
        scene = self.state.current_scene
        if not scene: return
        
        from PySide6.QtWidgets import QDialog, QFormLayout, QPushButton, QColorDialog
        from PySide6.QtGui import QColor
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Scene Settings")
        dialog.setFixedSize(300, 150)
        
        layout = QFormLayout(dialog)
        
        # Background Color
        current_color = scene.settings.get("background_color", [20, 20, 20, 255])
        
        color_btn = QPushButton()
        color_btn.setStyleSheet(f"background-color: rgba({current_color[0]}, {current_color[1]}, {current_color[2]}, 255); border: 1px solid #555;")
        color_btn.setFixedHeight(30)
        
        def pick_color():
            c = QColorDialog.getColor(
                QColor(current_color[0], current_color[1], current_color[2]), 
                self, 
                "Pick Background Color"
            )
            if c.isValid():
                new_c = [c.red(), c.green(), c.blue(), 255]
                scene.settings["background_color"] = new_c
                color_btn.setStyleSheet(f"background-color: rgba({new_c[0]}, {new_c[1]}, {new_c[2]}, 255); border: 1px solid #555;")
                self.canvas.update() # Preview immediately
                
        color_btn.clicked.connect(pick_color)
        layout.addRow("Background Color:", color_btn)
        
        # Close Button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addRow(close_btn)
        
        dialog.exec()

    def refresh_ui(self):
        """Force a UI refresh after undo/redo."""
        # Hierarchy refresh
        if hasattr(self.dock_hierarchy.widget(), "refresh_tree"):
             self.dock_hierarchy.widget().refresh_tree()
        
        # Canvas refresh
        self.canvas.update()
        
        # Inspector refresh via selection pulse
        self.state.select_object(self.state.selected_object_id)

    def new_scene(self):
        self.state.current_scene_path = None
        self.state.load_scene(Scene.create_empty("New Scene"))
        self.setWindowTitle("Aspis Engine Editor - New Scene")

    def open_scene(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Scene",
            os.path.join(self.state.project_root, "scenes"),
            "Scene Files (*.scene.json);;All Files (*)"
        )
        if path:
            try:
                data = load_scene(path)
                scene = Scene(
                    metadata=data.get("metadata", {}),
                    objects=data.get("objects", []),
                    prefabs=data.get("prefabs", {})
                )
                self.state.current_scene_path = path
                self.state.load_scene(scene)
                self.setWindowTitle(f"Aspis Engine Editor - {os.path.basename(path)}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load scene:\n{e}")

    def save_scene(self):
        if self.state.current_scene_path:
            self._do_save(self.state.current_scene_path)
        else:
            self.save_scene_as()

    def save_scene_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Scene As",
            os.path.join(self.state.project_root, "scenes", "untitled.scene.json"),
            "Scene Files (*.scene.json)"
        )
        if path:
            if not path.endswith(".scene.json"):
                path += ".scene.json"
            self._do_save(path)

    def _do_save(self, path):
        try:
            scene = self.state.current_scene
            if scene:
                data = asdict(scene)
                save_scene(data, path)
                self.state.current_scene_path = path
                self.setWindowTitle(f"Aspis Engine Editor - {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save scene:\n{e}")

    def run_game(self):
        # Auto-save if possible
        if self.state.current_scene_path:
            self._do_save(self.state.current_scene_path)
            
            # Launch runtime logic
            # If Frozen (EXE), we run ourself with --run-scene
            # If Dev (Python), we run main.py with --run-scene
            
            from shared.paths import get_engine_root
            engine_root = get_engine_root()
            
            # Environment setup
            env = os.environ.copy()
            env["PYTHONPATH"] = engine_root + os.pathsep + env.get("PYTHONPATH", "")
            
            if getattr(sys, 'frozen', False):
                # We are running as an EXE
                cmd = [sys.executable, "--run-scene", self.state.current_scene_path]
            else:
                # We are running as code
                main_py = os.path.join(engine_root, "main.py")
                cmd = [sys.executable, main_py, "--run-scene", self.state.current_scene_path]

            try:
                # CWD is Project Root so assets load relative to it
                subprocess.Popen(cmd, cwd=self.state.project_root, env=env)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to launch runtime:\n{e}")
        else:
            QMessageBox.warning(self, "Warning", "Please save the scene before playing.")
            self.save_scene()

    def apply_theme(self):
        # Professional Dark Theme - Sharp Edges, Monochrome
        self.setStyleSheet("""
            * {
                border-radius: 0px !important;
                outline: none;
            }
            QMainWindow, QWidget {
                background-color: #121212;
                color: #cccccc;
                font-family: 'Segoe UI', sans-serif;
                font-size: 11px;
            }
            
            /* Docks */
            QDockWidget {
                titlebar-close-icon: url(close.png);
                titlebar-normal-icon: url(float.png);
                border: 1px solid #1a1a1a;
            }
            
            /* Toolbar */
            QToolBar {
                background: #121212;
                border-bottom: 1px solid #333333;
                spacing: 10px;
                padding: 5px;
            }
            
            QDockWidget::title {
                text-align: left;
                background: #1a1a1a;
                padding: 4px 8px;
                color: #eeeeee;
                font-weight: bold;
                font-size: 11px;
            }
            
            /* Trees / Lists */
            QTreeView, QTreeWidget, QListView, QListWidget, QPlainTextEdit {
                background-color: #181818;
                border: 1px solid #282828;
                color: #cccccc;
            }
            QTreeView::item:selected, QListView::item:selected {
                background-color: #333333;
                color: white;
            }
            QHeaderView::section {
                background-color: #1a1a1a;
                color: #888888;
                border: none;
                border-right: 1px solid #282828;
                padding: 4px;
                text-transform: uppercase;
            }
            
            /* Buttons */
            QPushButton {
                background: #252525;
                color: #cccccc;
                border: 1px solid #333333;
                padding: 5px 12px;
                text-transform: uppercase;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #333333;
                border-color: #444444;
                color: white;
            }
            QPushButton:pressed {
                background: #111111;
                border-color: #444444;
            }
            
            /* Menus */
            QMenuBar {
                background-color: #121212;
                border-bottom: 1px solid #1a1a1a;
            }
            QMenuBar::item {
                padding: 4px 10px;
                background: transparent;
            }
            QMenuBar::item:selected {
                background: #252525;
                color: white;
            }
            QMenu {
                background-color: #181818;
                border: 1px solid #333333;
            }
            QMenu::item {
                padding: 5px 25px 5px 15px;
            }
            QMenu::item:selected {
                background-color: #252525;
                color: white;
            }
            
            /* Tabs */
            QTabWidget::pane {
                border: 1px solid #282828;
                background: #121212;
            }
            QTabBar::tab {
                background: #1a1a1a;
                color: #888888;
                padding: 6px 16px;
                border: 1px solid #1a1a1a;
                border-bottom: none;
                margin-right: 1px;
                text-transform: uppercase;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #252525;
                color: #ffffff;
                border-top: 2px solid #666666;
            }
            QTabBar::tab:hover {
                background: #222222;
                color: #cccccc;
            }
            
            /* Scrollbars */
            QScrollBar:vertical {
                border: none;
                background: #121212;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #333333;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #444444;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            /* Input Fields */
            QLineEdit, QSpinBox, QDoubleSpinBox {
                background: #111111;
                border: 1px solid #333333;
                color: #eeeeee;
                padding: 3px;
                selection-background-color: #444444;
            }
            QLineEdit:focus {
                border: 1px solid #555555;
            }
            
            /* Separators */
            QMainWindow::separator {
                background: #121212;
                width: 4px;
                height: 4px;
            }
            QMainWindow::separator:hover {
                background: #444444;
            }
            
            /* Play Button - Menu Item Style */
            QPushButton#PlayButton {
                background-color: transparent;
                color: #00ff00; /* Green Text */
                border: 1px solid #00aa00;
                font-family: 'Segoe UI', sans-serif;
                font-size: 11px;
                padding: 4px 15px;
                text-transform: uppercase; /* Match section headers? Or match File/Edit? Let's assume standard */
                font-weight: bold; 
            }
            QPushButton#PlayButton:hover {
                background-color: #00aa00;
                color: white;
            }
            QPushButton#PlayButton:pressed {
                background-color: #008800;
                color: white;
            }
        """)

    def switch_project(self):
        # Open Project Manager
        manager = ProjectManager()
        if manager.exec() == QDialog.Accepted:
            new_path = manager.selected_project_path
            if new_path and os.path.exists(new_path):
                self.reload_project(new_path)
    
    def reload_project(self, project_path):
        # 1. Update State
        self.state.set_project_root(project_path)
        self.state.current_scene_path = None
        self.setWindowTitle("Aspis Engine Editor")
        
        # 2. Reload Asset Browser
        # We need to recreate or reset the asset browser model
        # The easiest way is to remove the old dock widget and adding a new one, 
        # or implementing a set_root method in AssetBrowser.
        # AssetBrowser already has set_root(path) but it only sets root index, 
        # let's make sure it updates everything.
        
        # Access the AssetBrowser widget inside the dock
        asset_browser = self.dock_assets.widget()
        # We need to implement a full reset method in AssetBrowser or just hack it:
        # Actually I can just replace the widget content
        new_browser = AssetBrowser(project_path)
        new_browser.file_opened.connect(self.open_script)
        self.dock_assets.setWidget(new_browser)
        
        # 3. Load Empty Scene
        self.state.load_scene(Scene.create_empty("Untitled Scene"))
        
        # 4. Clear/Reset other panels if needed
        # Hierarchy/Inspector listen to signals, so they should auto-clear on load_scene
        
        QMessageBox.information(self, "Project Loaded", f"Switched to project:\n{project_path}")

def run(project_path=None):
    app = QApplication(sys.argv)
    
    # 1. Check if Project Path is provided (CLI arg)
    if not project_path and len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        candidate = sys.argv[1]
        if os.path.exists(candidate) and os.path.isdir(candidate):
            project_path = candidate

    # 2. If no project, Show Project Manager
    if not project_path:
        manager = ProjectManager()
        if manager.exec() != QDialog.Accepted:
            sys.exit(0) # User cancelled
        project_path = manager.selected_project_path
    
    # 3. Launch Main Window
    if project_path and os.path.exists(project_path):
        # Update Global State BEFORE MainWindow is created
        EditorState.instance().set_project_root(project_path)
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)
            
if __name__ == "__main__":
    run()

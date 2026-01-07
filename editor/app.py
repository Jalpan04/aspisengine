import sys
import os
import subprocess
from PySide6.QtWidgets import QApplication, QMainWindow, QDockWidget, QMenu, QMenuBar, QFileDialog, QMessageBox
from PySide6.QtCore import Qt

# Ensure correct path
sys.path.append(os.getcwd())

from editor.editor_state import EditorState
from editor.canvas import SceneCanvas
from editor.hierarchy import HierarchyPanel
from editor.inspector import InspectorPanel
from editor.asset_browser import AssetBrowser
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
        # 1. Central Widget - Canvas
        self.canvas = SceneCanvas()
        self.setCentralWidget(self.canvas)

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

        # Toolbar
        self.toolbar = self.addToolBar("Main")
        from PySide6.QtWidgets import QPushButton
        play_btn = QPushButton("▶ Play")
        play_btn.clicked.connect(self.run_game)
        play_btn.setStyleSheet("color: #44ff44; font-weight: bold; padding: 4px 10px; background: #333333; border: 1px solid #444444;")
        self.toolbar.addWidget(play_btn)

        self.apply_theme()

    def setup_menu(self):
        menu_bar = self.menuBar()
        
        # File Menu
        file_menu = menu_bar.addMenu("File")
        
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
            
            # Launch runtime
            cmd = [sys.executable, "runtime/game_loop.py", self.state.current_scene_path]
            try:
                # Reverting console hide to debug "nothing happened"
                subprocess.Popen(cmd, cwd=self.state.project_root)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to launch runtime:\n{e}")
        else:
            QMessageBox.warning(self, "Warning", "Please save the scene before playing.")
            self.save_scene()

    def apply_theme(self):
        # Sharp dark theme - no rounded corners, space efficient
        self.setStyleSheet("""
            * {
                border-radius: 0px;
            }
            QMainWindow {
                background-color: #1a1a1a;
            }
            QDockWidget {
                titlebar-close-icon: url(close.png);
                titlebar-normal-icon: url(float.png);
            }
            QDockWidget::title {
                text-align: left;
                background: #222222;
                padding: 3px 5px;
                color: #999999;
                font-weight: normal;
                font-size: 11px;
            }
            QWidget {
                color: #b0b0b0;
                background-color: #1a1a1a;
                font-family: 'Segoe UI', sans-serif;
                font-size: 11px;
            }
            QTreeView, QTreeWidget {
                background-color: #1e1e1e;
                border: none;
                color: #a0a0a0;
            }
            QTreeView::item, QTreeWidget::item {
                padding: 2px 0;
            }
            QHeaderView::section {
                background-color: #252525;
                color: #888888;
                border: none;
                padding: 3px;
                font-size: 10px;
            }
            QMenuBar {
                background-color: #1e1e1e;
                color: #999999;
                padding: 2px;
            }
            QMenuBar::item {
                padding: 3px 8px;
            }
            QMenuBar::item:selected {
                background-color: #2a2a2a;
            }
            QMenu {
                background-color: #1e1e1e;
                color: #999999;
                border: 1px solid #333333;
            }
            QMenu::item {
                padding: 4px 20px;
            }
            QMenu::item:selected {
                background-color: #2a2a2a;
            }
            QPushButton {
                background: #2a2a2a;
                color: #999999;
                border: 1px solid #333333;
                padding: 3px 8px;
                font-size: 10px;
            }
            QPushButton:hover {
                background: #333333;
            }
            QScrollArea {
                border: none;
            }
            QLabel {
                background: transparent;
            }
        """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

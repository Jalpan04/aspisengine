import os
import sys
import json
import shutil
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                             QLineEdit, QPushButton, QCheckBox, QProgressBar, 
                             QLabel, QTextEdit, QFileDialog, QMessageBox, QFrame)
from PySide6.QtCore import Qt, QProcess, QUrl
from PySide6.QtGui import QDesktopServices
from editor.theme import Theme
from editor.exporter import get_pyinstaller_args, find_real_project_root

class ExportDialog(QDialog):
    def __init__(self, parent=None, project_root=None, current_scene_path=None):
        super().__init__(parent)
        self.setWindowTitle("Export Standalone Game")
        self.resize(600, 500)
        self.setMinimumSize(500, 400)
        
        self.project_root = find_real_project_root(project_root) if project_root else os.getcwd()
        self.current_scene_path = current_scene_path
        self.process = None
        self.temp_config_path = None
        
        # Apply Editor Dark Theme
        self.setStyleSheet(Theme.get_global_stylesheet())
        
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)
        
        # 1. Title / Header
        title_label = QLabel("Export standalone game to EXE executable.")
        title_label.setStyleSheet(f"font-size: {Theme.FONT_HEADER}; color: {Theme.ACCENT}; font-weight: bold;")
        main_layout.addWidget(title_label)
        
        # Divider Line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"background-color: {Theme.BORDER_DEFAULT}; max-height: 1px; border: none;")
        main_layout.addWidget(line)
        
        # 2. Form Layout
        form = QFormLayout()
        form.setSpacing(10)
        
        # Game Name Input
        self.name_input = QLineEdit()
        default_name = os.path.basename(self.project_root) if self.project_root else "MyAspisGame"
        self.name_input.setText(default_name)
        self.name_input.setPlaceholderText("Game Name")
        form.addRow("Game Name:", self.name_input)
        
        # Version Input
        self.version_input = QLineEdit()
        self.version_input.setText("1.0.0")
        self.version_input.setPlaceholderText("e.g. 1.0.0")
        form.addRow("Version:", self.version_input)
        
        # Made By Input
        self.author_input = QLineEdit()
        self.author_input.setText("Developer")
        self.author_input.setPlaceholderText("Author/Studio Name")
        form.addRow("Made By:", self.author_input)
        
        # Output Directory Input
        self.dir_input = QLineEdit()
        default_dist = os.path.join(self.project_root, "dist") if self.project_root else ""
        self.dir_input.setText(default_dist)
        self.dir_input.setPlaceholderText("Select folder...")
        
        dir_layout = QHBoxLayout()
        dir_layout.setSpacing(6)
        dir_layout.addWidget(self.dir_input)
        
        browse_dir_btn = QPushButton("Browse...")
        browse_dir_btn.clicked.connect(self.browse_output_dir)
        dir_layout.addWidget(browse_dir_btn)
        form.addRow("Output Folder:", dir_layout)
        
        # Optional Icon Input
        self.icon_input = QLineEdit()
        self.icon_input.setPlaceholderText("Optional path to .ico file")
        
        icon_layout = QHBoxLayout()
        icon_layout.setSpacing(6)
        icon_layout.addWidget(self.icon_input)
        
        browse_icon_btn = QPushButton("Browse...")
        browse_icon_btn.clicked.connect(self.browse_icon_file)
        icon_layout.addWidget(browse_icon_btn)
        form.addRow("Icon File:", icon_layout)
        
        # Checkbox Settings
        self.exclude_editor_check = QCheckBox("Exclude Editor modules (Reduces executable size from ~120MB to ~30MB)")
        self.exclude_editor_check.setChecked(True)
        form.addRow("", self.exclude_editor_check)
        
        main_layout.addLayout(form)
        
        # 3. Text Log Viewer
        log_label = QLabel("Build Logs:")
        log_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-weight: bold;")
        main_layout.addWidget(log_label)
        
        self.log_viewer = QTextEdit()
        self.log_viewer.setReadOnly(True)
        self.log_viewer.setPlaceholderText("Logs will appear here during compilation...")
        self.log_viewer.setStyleSheet(f"""
            background-color: {Theme.BG_INPUT}; 
            color: #A0C0A0; 
            font-family: 'Consolas', monospace; 
            border: 1px solid {Theme.BORDER_DEFAULT};
        """)
        main_layout.addWidget(self.log_viewer)
        
        # 4. Progress Section
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {Theme.BG_INPUT};
                border: 1px solid {Theme.BORDER_DEFAULT};
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {Theme.ACCENT};
            }}
        """)
        main_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
        main_layout.addWidget(self.status_label)
        
        # 5. Buttons Layout
        buttons_layout = QHBoxLayout()
        
        # Success action (hidden initially) - Far Left
        self.run_btn = QPushButton("Run Game")
        self.run_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.SUCCESS};
                color: #FFFFFF;
                font-weight: bold;
                padding: 6px 15px;
            }}
            QPushButton:hover {{
                background-color: {Theme.SUCCESS_HOVER};
            }}
        """)
        self.run_btn.clicked.connect(self.run_exported_game)
        self.run_btn.hide()
        buttons_layout.addWidget(self.run_btn)
        
        # Stretch between Left (Run Game) and Right (Open Folder + Close)
        buttons_layout.addStretch()
        
        # Success action (hidden initially) - Far Right (next to Close)
        self.open_folder_btn = QPushButton("Open Folder")
        self.open_folder_btn.clicked.connect(self.open_output_folder)
        self.open_folder_btn.hide()
        buttons_layout.addWidget(self.open_folder_btn)
        
        # Build/Cancel - Far Right
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_btn)
        
        self.build_btn = QPushButton("Build")
        self.build_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.ACCENT};
                color: {Theme.BG_WINDOW};
                font-weight: bold;
                padding: 6px 15px;
            }}
            QPushButton:hover {{
                background-color: {Theme.ACCENT_HOVER};
            }}
        """)
        self.build_btn.clicked.connect(self.start_build)
        buttons_layout.addWidget(self.build_btn)
        
        main_layout.addLayout(buttons_layout)

    def browse_output_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Directory", self.dir_input.text())
        if folder:
            self.dir_input.setText(folder)

    def browse_icon_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Icon File", "", "Icon Files (*.ico)")
        if file_path:
            self.icon_input.setText(file_path)

    def start_build(self):
        game_name = self.name_input.text().strip()
        output_dir = self.dir_input.text().strip()
        icon_path = self.icon_input.text().strip()
        exclude_editor = self.exclude_editor_check.isChecked()
        
        if not game_name:
            QMessageBox.warning(self, "Warning", "Please specify a Game Name.")
            return
        if not output_dir:
            QMessageBox.warning(self, "Warning", "Please specify an Output Folder.")
            return
        if not self.current_scene_path:
            QMessageBox.warning(self, "Warning", "No active scene loaded. Please open or save a scene first.")
            return
            
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Step A. Write config.json starter scene settings
        version = self.version_input.text().strip() or "1.0.0"
        made_by = self.author_input.text().strip() or "Developer"
        try:
            rel_scene = os.path.relpath(self.current_scene_path, self.project_root)
            self.temp_config_path = os.path.join(self.project_root, "config.json")
            config_data = {
                "start_scene": rel_scene,
                "game_name": game_name,
                "version": version,
                "made_by": made_by
            }
            with open(self.temp_config_path, "w") as f:
                json.dump(config_data, f, indent=2)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate starter config:\n{e}")
            return
            
        # Step B. Get command line arguments
        cmd_args = get_pyinstaller_args(
            project_root=self.project_root,
            rel_scene_path=rel_scene,
            game_name=game_name,
            output_dir=output_dir,
            exclude_editor=exclude_editor,
            icon_path=icon_path
        )
        
        # Step C. Initialize UI state
        self.log_viewer.clear()
        self.log_viewer.append(f"--- Export Started for {game_name} ---")
        self.log_viewer.append(f"Starter scene: {rel_scene}")
        self.log_viewer.append(f"Build command: {sys.executable} {' '.join(cmd_args)}")
        self.log_viewer.append("Initializing PyInstaller compiling thread...\n")
        
        self.progress_bar.setRange(0, 0) # Infinite busy state
        self.status_label.setText("Running PyInstaller... (this may take up to a minute)")
        self.set_widgets_enabled(False)
        
        # Step D. Start compilation process asynchronously
        self.process = QProcess(self)
        self.process.setWorkingDirectory(self.project_root)
        self.process.readyReadStandardOutput.connect(self.read_stdout)
        self.process.readyReadStandardError.connect(self.read_stderr)
        self.process.finished.connect(self.build_finished)
        
        # Set environment PYTHONPATH to current directory so PyInstaller runs fine
        env = QProcess.systemEnvironment()
        engine_root = os.getcwd()
        python_path_val = engine_root
        for var in env:
            if var.startswith("PYTHONPATH="):
                python_path_val = engine_root + os.pathsep + var.split("=", 1)[1]
        env.append(f"PYTHONPATH={python_path_val}")
        self.process.setEnvironment(env)
        
        self.process.start(sys.executable, cmd_args)

    def set_widgets_enabled(self, enabled):
        self.name_input.setEnabled(enabled)
        self.version_input.setEnabled(enabled)
        self.author_input.setEnabled(enabled)
        self.dir_input.setEnabled(enabled)
        self.icon_input.setEnabled(enabled)
        self.exclude_editor_check.setEnabled(enabled)
        self.build_btn.setEnabled(enabled)
        if enabled:
            self.build_btn.setText("Build")
            self.cancel_btn.setText("Cancel")
        else:
            self.build_btn.setText("Building...")
            self.cancel_btn.setText("Background") # Allow closing to background while QProcess runs

    def read_stdout(self):
        data = self.process.readAllStandardOutput().data().decode("utf-8", errors="ignore")
        self.log_viewer.append(data.strip())
        self.log_viewer.verticalScrollBar().setValue(self.log_viewer.verticalScrollBar().maximum())

    def read_stderr(self):
        data = self.process.readAllStandardError().data().decode("utf-8", errors="ignore")
        self.log_viewer.append(data.strip())
        self.log_viewer.verticalScrollBar().setValue(self.log_viewer.verticalScrollBar().maximum())

    def build_finished(self, exit_code, exit_status):
        self.set_widgets_enabled(True)
        self.progress_bar.setRange(0, 100)
        
        # Step E. Clean up build artifacts from Project and Engine Root directories
        self.cleanup_build_artifacts()
        
        if exit_code == 0:
            self.progress_bar.setValue(100)
            self.status_label.setText("Build Successful!")
            self.log_viewer.append("\n--- Export Successful! Standalone EXE generated in output folder. ---")
            
            # Hide standard cancel button
            self.cancel_btn.hide()
            
            # Show success action buttons
            self.run_btn.show()
            self.open_folder_btn.show()
            
            # Change Build button to Close
            self.build_btn.setText("Close")
            self.build_btn.clicked.disconnect()
            self.build_btn.clicked.connect(self.accept)
            
            game_name = self.name_input.text().strip()
            dest_exe = os.path.join(self.dir_input.text().strip(), f"{game_name}.exe")
            QMessageBox.information(
                self, 
                "Success", 
                f"Game successfully exported!\n\nExecutable location:\n{dest_exe}"
            )
        else:
            self.progress_bar.setValue(0)
            self.status_label.setText("Build Failed!")
            self.log_viewer.append(f"\n--- Export Failed with Exit Code: {exit_code} ---")
            QMessageBox.critical(
                self, 
                "Error", 
                "Build process failed. Please check the logs in the text viewer for compilation errors."
            )

    def run_exported_game(self):
        game_name = self.name_input.text().strip()
        dest_exe = os.path.join(self.dir_input.text().strip(), f"{game_name}.exe")
        if os.path.exists(dest_exe):
            QProcess.startDetached(dest_exe, [], os.path.dirname(dest_exe))
        else:
            QMessageBox.warning(self, "Error", f"Executable not found:\n{dest_exe}")

    def open_output_folder(self):
        output_dir = self.dir_input.text().strip()
        if os.path.exists(output_dir):
            QDesktopServices.openUrl(QUrl.fromLocalFile(output_dir))
        else:
            QMessageBox.warning(self, "Error", f"Folder not found:\n{output_dir}")

    def cleanup_build_artifacts(self):
        game_name = self.name_input.text().strip()
        engine_root = os.getcwd()
        
        # 1. Delete temporary config.json
        if self.temp_config_path and os.path.exists(self.temp_config_path):
            try:
                os.remove(self.temp_config_path)
            except:
                pass
                
        # 2. Delete build folder and spec files (from both project root and engine root)
        targets = [
            os.path.join(self.project_root, "build"),
            os.path.join(engine_root, "build"),
            os.path.join(self.project_root, f"{game_name}.spec"),
            os.path.join(engine_root, f"{game_name}.spec")
        ]
        
        for path in targets:
            if os.path.exists(path):
                try:
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                except:
                    pass

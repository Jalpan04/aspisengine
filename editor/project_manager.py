
import sys
import os
import json
import shutil
import subprocess
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QFileDialog, QListWidget, 
                               QMessageBox, QWidget, QListWidgetItem, QInputDialog,
                               QFrame, QMenu, QSizePolicy)
from PySide6.QtCore import Qt, Signal, QSize, QPoint, QUrl
from PySide6.QtGui import QIcon, QFont, QColor, QAction, QDesktopServices, QPainter

# --- Custom Icon Widget for Perfect Centering ---
class ProjectIcon(QWidget):
    def __init__(self, letter, parent=None):
        super().__init__(parent)
        self.letter = letter
        self.setFixedSize(36, 36)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 1. Background (Transparent Cyan)
        rect = self.rect()
        bg_color = QColor("#5E9EA3")
        bg_color.setAlphaF(0.2)
        painter.fillRect(rect, bg_color)
        
        # 2. Border (Subtle)
        border_color = QColor("#5E9EA3")
        border_color.setAlphaF(0.3)
        painter.setPen(border_color)
        painter.drawRect(rect.adjusted(0, 0, -1, -1))
        
        # 3. Text (Centered)
        painter.setPen(QColor(255, 255, 255, 240)) # White, 95% opacity
        
        font = QFont("Segoe UI", 16, QFont.Black) # Extra Bold
        font.setStyleStrategy(QFont.PreferAntialias)
        painter.setFont(font)
        
        # Draw Text Centered
        painter.drawText(rect, Qt.AlignCenter, self.letter)

# --- Custom Widget for Project List Item ---
class ProjectItemWidget(QWidget):
    action_triggered = Signal(str, str) # action, path

    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.path = path
        self.name = os.path.basename(path)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(12)
        
        # 1. Icon (Custom Painted Widget)
        self.icon_lbl = ProjectIcon(self.name[0].upper() if self.name else "?")
        layout.addWidget(self.icon_lbl)
        
        # 2. Text Info (Name & Path)
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        text_layout.setAlignment(Qt.AlignVCenter)
        
        self.name_lbl = QLabel(self.name)
        self.name_lbl.setObjectName("ProjectName")
        
        self.path_lbl = QLabel(path)
        self.path_lbl.setObjectName("ProjectPath")
        
        text_layout.addWidget(self.name_lbl)
        text_layout.addWidget(self.path_lbl)
        layout.addLayout(text_layout)
        
        layout.addStretch()
        
        # 3. Context Menu Button ("...")
        self.menu_btn = QPushButton("⋮")  # Vertical Ellipsis
        self.menu_btn.setObjectName("MenuBtn")
        self.menu_btn.setFixedSize(30, 30)
        self.menu_btn.setCursor(Qt.PointingHandCursor)
        self.menu_btn.clicked.connect(self.show_menu)
        layout.addWidget(self.menu_btn)

    def show_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #252525;
                color: #E0E0E0;
                border: 1px solid #444;
            }
            QMenu::item {
                padding: 5px 20px;
            }
            QMenu::item:selected {
                background-color: #5E9EA3;
                color: #000;
            }
        """)
        
        open_folder = menu.addAction("Show in Explorer")
        remove_item = menu.addAction("Remove from List")
        
        # Calculate position (below the button)
        pos = self.menu_btn.mapToGlobal(QPoint(0, self.menu_btn.height()))
        action = menu.exec(pos)
        
        if action == open_folder:
            self.action_triggered.emit("open_folder", self.path)
        elif action == remove_item:
            self.action_triggered.emit("remove", self.path)


class ProjectManager(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aspis Engine Hub")
        self.resize(900, 550)
        self.selected_project_path = None
        
        # Preferences Path
        self.prefs_path = os.path.join(os.path.expanduser("~"), ".aspis_prefs.json")
        self.recent_projects = self.load_recent()

        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        # We use a custom Frameless hint if we wanted full custom window, 
        # but for now we stick to standard frame for stability.
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- LEFT SIDEBAR (30%) ---
        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 30, 20, 30)
        sidebar_layout.setSpacing(15)
        
        # 1. Logo Block
        logo_container = QVBoxLayout()
        logo_container.setSpacing(0)
        
        logo_lbl = QLabel("ASPIS")
        logo_lbl.setObjectName("LogoText")
        
        engine_lbl = QLabel("ENGINE")
        engine_lbl.setObjectName("LogoSub")
        
        version_lbl = QLabel("v1.0.0 Beta")
        version_lbl.setObjectName("VersionText")
        
        logo_container.addWidget(logo_lbl)
        logo_container.addWidget(engine_lbl)
        logo_container.addWidget(version_lbl)
        
        sidebar_layout.addLayout(logo_container)
        
        sidebar_layout.addSpacing(10)
        
        # 2. Main Action Buttons
        # Container to constrain width slightly if needed, but margin handles it.
        
        btn_new = QPushButton("NEW PROJECT")
        btn_new.setObjectName("BtnPrimary")
        btn_new.setCursor(Qt.PointingHandCursor)
        btn_new.clicked.connect(self.on_new_project)
        
        btn_open = QPushButton("OPEN PROJECT")
        btn_open.setObjectName("BtnSecondary")
        btn_open.setCursor(Qt.PointingHandCursor)
        btn_open.clicked.connect(self.on_open_project)
        
        sidebar_layout.addWidget(btn_new)
        sidebar_layout.addWidget(btn_open)
        
        sidebar_layout.addStretch()
        
        # 3. Footer Links
        links_layout = QVBoxLayout()
        links_layout.setSpacing(10)
        
        doc_link = QLabel('<a href="https://docs.aspisengine.com" style="color: #888; text-decoration: none;">Documentation</a>')
        doc_link.setOpenExternalLinks(True)
        doc_link.setObjectName("FooterLink")
        
        settings_link = QLabel('<a href="#" style="color: #888; text-decoration: none;">Settings</a>')
        settings_link.setObjectName("FooterLink")
        
        copyright_lbl = QLabel("© 2026 Aspis Team")
        copyright_lbl.setObjectName("Copyright")
        
        links_layout.addWidget(doc_link)
        links_layout.addWidget(settings_link)
        links_layout.addSpacing(5)
        links_layout.addWidget(copyright_lbl)
        
        sidebar_layout.addLayout(links_layout)
        
        main_layout.addWidget(sidebar, 30)

        # --- RIGHT AREA (70%) ---
        content_area = QWidget()
        content_area.setObjectName("ContentArea")
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(15)
        
        # Header Row (Title + Search)
        header_layout = QHBoxLayout()
        
        header_lbl = QLabel("Recent Projects")
        header_lbl.setObjectName("ContentHeader")
        header_layout.addWidget(header_lbl)
        
        header_layout.addStretch()
        
        # Search Bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.search_input.setObjectName("SearchInput")
        self.search_input.setFixedWidth(200)
        self.search_input.textChanged.connect(self.filter_projects)
        header_layout.addWidget(self.search_input)
        
        content_layout.addLayout(header_layout)
        
        # Project List
        self.recent_list = QListWidget()
        self.recent_list.setObjectName("RecentList")
        self.recent_list.setSelectionMode(QListWidget.SingleSelection)
        self.recent_list.itemDoubleClicked.connect(self.on_recent_double_click)
        self.recent_list.setFocusPolicy(Qt.NoFocus) # Remove dotted outline
        
        self.refresh_recent_list()
        
        content_layout.addWidget(self.recent_list)

        main_layout.addWidget(content_area, 70)

    def apply_theme(self):
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', 'Roboto', sans-serif;
            }
            QDialog {
                background-color: #121212;
            }
            
            /* --- SIDEBAR --- */
            QWidget#Sidebar {
                background-color: #121212;
                border-right: 1px solid #2A2A2A; /* Vertical Divider */
            }
            QLabel#LogoText {
                font-size: 36px;
                font-weight: 900;
                color: #5E9EA3; /* Dull Cyan */
                margin-bottom: -5px;
            }
            QLabel#LogoSub {
                font-size: 14px;
                font-weight: 600;
                color: #E0E0E0;
                letter-spacing: 8px; /* EXPANDED SPACING */
                margin-left: 2px;
            }
            QLabel#VersionText {
                color: #555;
                font-size: 11px;
                margin-top: 5px;
            }
            QLabel#FooterLink {
                font-size: 13px;
                color: #888;
            }
            QLabel#FooterLink:hover {
                color: #E0E0E0;
            }
            QLabel#Copyright {
                color: #444; 
                font-size: 10px;
            }
            
            /* Buttons */
            QPushButton {
                border-radius: 0px; /* SHARP RECTANGLES */
                padding: 8px 12px;
                font-weight: bold;
                font-size: 11px;
                text-align: center;
                margin-left: 0px; 
                margin-right: 0px;
                letter-spacing: 1px;
            }
            
            /* Primary Button (New) */
            QPushButton#BtnPrimary {
                background-color: #5E9EA3;
                color: #121212;
                border: none;
            }
            QPushButton#BtnPrimary:hover {
                background-color: #6FBCC2;
            }
            QPushButton#BtnPrimary:pressed {
                background-color: #4A8589;
            }
            
            /* Secondary Button (Open) */
            QPushButton#BtnSecondary {
                background-color: transparent;
                color: #E0E0E0;
                border: 1px solid #444;
            }
            QPushButton#BtnSecondary:hover {
                border: 1px solid #5E9EA3;
                color: #5E9EA3;
            }
            
            /* --- CONTENT AREA --- */
            QWidget#ContentArea {
                background-color: #121212; 
            }
            QLabel#ContentHeader {
                font-size: 18px; 
                color: #FFF; 
                font-weight: bold;
            }
            
            /* Search Input */
            QLineEdit#SearchInput {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 1px solid #333;
                border-radius: 0px; /* Sharp */
                padding: 8px 12px; /* Increased padding for vertical center */
                font-size: 13px;   /* Better readability */
                selection-background-color: #5E9EA3;
            }
            QLineEdit#SearchInput:focus {
                border: 1px solid #5E9EA3;
            }
            
            /* Project List */
            QListWidget#RecentList {
                background-color: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item {
                background-color: #1E1E1E; /* Card Background */
                color: #E0E0E0;
                border-radius: 0px; /* Sharp */
                margin-bottom: 5px; /* Compact */
                padding: 0px;
                border: 1px solid #252525;
            }
            QListWidget::item:hover {
                background-color: #232323;
                border: 1px solid #5E9EA3; /* Hover Glow */
            }
            QListWidget::item:selected {
                background-color: #1A2A2C;
                border: 1px solid #5E9EA3;
            }
            

            QLabel#ProjectName {
                color: white; 
                font-weight: bold; 
                font-size: 13px;
            }
            QLabel#ProjectPath {
                color: #777; 
                font-size: 10px;
            }
            QPushButton#MenuBtn {
                background-color: transparent;
                color: #666;
                border: none;
                margin: 0px;
                border-radius: 0px;
                font-size: 18px;
                padding: 0px;
            }
            QPushButton#MenuBtn:hover {
                background-color: #333;
                color: #FFF;
            }
        """)

    def load_recent(self):
        if os.path.exists(self.prefs_path):
            try:
                with open(self.prefs_path, 'r') as f:
                    data = json.load(f)
                    return data.get("recent_projects", [])
            except:
                return []
        return []

    def save_recent(self):
        data = {"recent_projects": self.recent_projects}
        try:
            with open(self.prefs_path, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Failed to save preferences: {e}")

    def add_to_recent(self, path):
        if path in self.recent_projects:
            self.recent_projects.remove(path)
        self.recent_projects.insert(0, path)
        self.recent_projects = self.recent_projects[:20]
        self.save_recent()
        self.refresh_recent_list()

    def remove_from_recent(self, path):
        if path in self.recent_projects:
            self.recent_projects.remove(path)
            self.save_recent()
            self.refresh_recent_list()
            
    def open_in_explorer(self, path):
        # Determine OS
        try:
            if sys.platform == 'win32':
                os.startfile(path)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', path])
            else:
                subprocess.Popen(['xdg-open', path])
        except Exception as e:
            print(f"Failed to open explorer: {e}")

    def handle_item_action(self, action, path):
        if action == "open_folder":
            self.open_in_explorer(path)
        elif action == "remove":
            self.remove_from_recent(path)

    def refresh_recent_list(self):
        self.recent_list.clear()
        search_text = self.search_input.text().lower() if hasattr(self, 'search_input') else ""
        
        for path in self.recent_projects:
            name = os.path.basename(path).lower()
            if search_text and search_text not in name:
                continue
                
            # Create widget
            widget = ProjectItemWidget(path)
            widget.action_triggered.connect(self.handle_item_action)
            
            item = QListWidgetItem(self.recent_list)
            item.setSizeHint(widget.sizeHint())
            item.setData(Qt.UserRole, path)
            
            self.recent_list.setItemWidget(item, widget)

    def filter_projects(self, text):
        self.refresh_recent_list()

    def on_recent_double_click(self, item):
        path = item.data(Qt.UserRole)
        # Verify path, else show warning
        if os.path.exists(path):
            self.finish_selection(path)
        else:
            reply = QMessageBox.question(self, "Project Not Found", 
                                        f"The path '{path}' does not exist.\nRemove from list?",
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.remove_from_recent(path)

    def on_new_project(self):
        name, ok = QInputDialog.getText(self, "New Project", "Project Name:")
        if not ok or not name.strip():
            return
        
        # Default to Documents/My Games/Aspis/ if possible, or just ask
        parent_dir = QFileDialog.getExistingDirectory(self, "Select Parent Folder")
        if not parent_dir:
            return

        project_path = os.path.join(parent_dir, name)
        
        if os.path.exists(project_path):
            QMessageBox.warning(self, "Error", "Directory already exists!")
            return

        try:
            os.makedirs(os.path.join(project_path, "assets"), exist_ok=True)
            os.makedirs(os.path.join(project_path, "scenes"), exist_ok=True)
            os.makedirs(os.path.join(project_path, "scripts"), exist_ok=True)
            
            meta = {
                "name": name,
                "version": "1.0",
                "engine_version": "Beta 1.0"
            }
            with open(os.path.join(project_path, "project.json"), "w") as f:
                json.dump(meta, f, indent=4)
            
            self.finish_selection(project_path)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create project: {e}")

    def on_open_project(self):
        path = QFileDialog.getExistingDirectory(self, "Open Project Folder")
        if path:
            self.finish_selection(path)

    def finish_selection(self, path):
        self.selected_project_path = path
        self.add_to_recent(path)
        self.accept()

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = ProjectManager()
    if window.exec() == QDialog.Accepted:
        print(f"Selected: {window.selected_project_path}")
    else:
        print("Cancelled")

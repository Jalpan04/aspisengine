from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFileSystemModel, QListView, QHBoxLayout, QPushButton
from PySide6.QtCore import QDir, Qt, QSize, Signal
import os

class AssetBrowser(QWidget):
    file_opened = Signal(str)

    def __init__(self, project_root):
        super().__init__()
        self.project_root = project_root
        self.current_root = project_root
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(2)
        
        # Toolbar
        toolbar = QHBoxLayout()
        self.btn_back = QPushButton("..")
        self.btn_back.setFixedWidth(30)
        self.btn_back.clicked.connect(self.go_up)
        toolbar.addWidget(self.btn_back)
        
        self.lbl_path = QLabel(project_root)
        self.lbl_path.setStyleSheet("color: #888; padding: 2px;")
        toolbar.addWidget(self.lbl_path)
        
        self.layout.addLayout(toolbar)

        self.model = QFileSystemModel()
        self.model.setRootPath(project_root)
        self.model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot | QDir.AllDirs)
        # self.model.setNameFilters(["*.png", "*.jpg", "*.jpeg", "*.scene.json", "*.py", "*.prefab"])
        # self.model.setNameFilterDisables(False)
        
        self.list_view = QListView()
        self.list_view.setModel(self.model)
        self.list_view.setRootIndex(self.model.index(project_root))
        
        self.list_view.setViewMode(QListView.IconMode)
        self.list_view.setIconSize(QSize(64, 64))
        self.list_view.setResizeMode(QListView.Adjust)
        self.list_view.setGridSize(QSize(80, 80))
        self.list_view.setSpacing(5)
        self.list_view.setUniformItemSizes(True)
        self.list_view.setWordWrap(True)
        
        self.list_view.setDragEnabled(True)
        
        self.list_view.doubleClicked.connect(self.on_double_click)
        
        self.layout.addWidget(self.list_view)

    def on_double_click(self, index):
        path = self.model.filePath(index)
        if os.path.isdir(path):
            self.set_root(path)
        else:
            self.file_opened.emit(path)

    def go_up(self):
        parent_dir = os.path.dirname(self.current_root)
        if parent_dir and os.path.abspath(parent_dir).startswith(os.path.abspath(self.project_root)):
            self.set_root(parent_dir)

    def set_root(self, path):
        self.current_root = path
        self.list_view.setRootIndex(self.model.index(path))
        rel_path = os.path.relpath(path, self.project_root)
        self.lbl_path.setText(f"/{rel_path if rel_path != '.' else ''}")

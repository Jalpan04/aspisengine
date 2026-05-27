class Theme:
    # --- COLORS ---
    # Backgrounds
    BG_WINDOW   = "#121212"    # Main window / top-level background
    BG_PANEL    = "#181818"    # Trees, lists, sidebars
    BG_HEADER   = "#1E1E1E"    # Dock title bars, section headers
    BG_CARD     = "#252525"    # Buttons, project cards, inactive tabs
    BG_INPUT    = "#111111"    # Text inputs, spin boxes
    BG_HOVER    = "#2A2A2A"    # General hover state
    BG_PRESSED  = "#0D0D0D"    # General pressed state
    BG_SELECTED = "#1A2E30"    # Selected rows/items in trees

    # Accents & Borders
    ACCENT          = "#5E9EA3"  # Primary action colour (teal)
    ACCENT_HOVER    = "#6FBCC2"  # Hovered primary button
    ACCENT_PLAY     = "#00CC66"  # Play button (green)
    ACCENT_PLAY_BG  = "#00AA55"  # Play button hover background
    SUCCESS         = "#2E7D32"  # Success/confirm state (dark green)
    SUCCESS_HOVER   = "#388E3C"  # Success hover state
    BORDER_DEFAULT  = "#303030"  # Standard panel borders
    BORDER_DARK     = "#1E1E1E"  # Subtle dividers
    BORDER_FOCUS    = "#5E9EA3"  # Input focus ring

    # Typography colours
    TEXT_PRIMARY   = "#E0E0E0"   # Standard text
    TEXT_SECONDARY = "#888888"   # Subtitles, breadcrumbs
    TEXT_MUTED     = "#505050"   # Disabled, X/Y axis labels
    TEXT_HIGHLIGHT = "#FFFFFF"   # Active, selected text

    # --- TYPOGRAPHY ---
    FONT_FAMILY   = "'Segoe UI', sans-serif"
    FONT_TINY     = "9px"
    FONT_SMALL    = "10px"
    FONT_REGULAR  = "11px"
    FONT_HEADER   = "13px"
    FONT_HUGE     = "36px"

    # --- LAYOUT & SPACING ---
    MARGIN_NONE     = (0, 0, 0, 0)
    MARGIN_STANDARD = (6, 6, 6, 6)
    MARGIN_RELAXED  = (10, 8, 10, 8)

    SPACING_TIGHT    = 2
    SPACING_STANDARD = 4
    SPACING_RELAXED  = 12

    # ------------------------------------------------------------------
    # Global stylesheet — single source of truth for every widget
    # ------------------------------------------------------------------
    @classmethod
    def get_global_stylesheet(cls) -> str:
        """Returns the complete application stylesheet derived from theme tokens."""
        return f"""
            /* ── Base ─────────────────────────────────────────────────── */
            * {{
                border-radius: 0px;
                outline: none;
            }}
            QWidget {{
                background-color: {cls.BG_WINDOW};
                color: {cls.TEXT_PRIMARY};
                font-family: {cls.FONT_FAMILY};
                font-size: {cls.FONT_REGULAR};
            }}
            QMainWindow, QDialog {{
                background-color: {cls.BG_WINDOW};
            }}

            /* ── Dock Widgets ─────────────────────────────────────────── */
            QDockWidget {{
                border: 1px solid {cls.BORDER_DARK};
            }}
            QDockWidget::title {{
                text-align: left;
                background: {cls.BG_HEADER};
                padding: 5px 8px;
                color: {cls.TEXT_HIGHLIGHT};
                font-weight: bold;
                font-size: {cls.FONT_REGULAR};
                border-bottom: 1px solid {cls.BORDER_DEFAULT};
            }}

            /* ── Toolbar ──────────────────────────────────────────────── */
            QToolBar {{
                background: {cls.BG_WINDOW};
                border-bottom: 1px solid {cls.BORDER_DEFAULT};
                spacing: 10px;
                padding: 5px;
            }}

            /* ── Trees / Lists ────────────────────────────────────────── */
            QTreeView, QTreeWidget, QListView, QListWidget {{
                background-color: {cls.BG_PANEL};
                border: 1px solid {cls.BORDER_DEFAULT};
                color: {cls.TEXT_PRIMARY};
                selection-background-color: transparent;
            }}
            QTreeView::item, QTreeWidget::item, QListView::item, QListWidget::item {{
                padding: 2px 4px;
            }}
            QTreeView::item:hover, QTreeWidget::item:hover,
            QListView::item:hover, QListWidget::item:hover {{
                background-color: {cls.BG_HOVER};
            }}
            QTreeView::item:selected, QTreeWidget::item:selected,
            QListView::item:selected, QListWidget::item:selected {{
                background-color: {cls.BG_SELECTED};
                color: {cls.TEXT_HIGHLIGHT};
            }}
            QHeaderView::section {{
                background-color: {cls.BG_HEADER};
                color: {cls.TEXT_SECONDARY};
                border: none;
                border-right: 1px solid {cls.BORDER_DEFAULT};
                border-bottom: 1px solid {cls.BORDER_DEFAULT};
                padding: 4px 6px;
            }}

            /* ── Plain Text / Code Views ──────────────────────────────── */
            QPlainTextEdit, QTextEdit {{
                background-color: {cls.BG_PANEL};
                border: 1px solid {cls.BORDER_DEFAULT};
                color: {cls.TEXT_PRIMARY};
            }}

            /* ── Buttons ──────────────────────────────────────────────── */
            QPushButton {{
                background: {cls.BG_CARD};
                color: {cls.TEXT_PRIMARY};
                border: 1px solid {cls.BORDER_DEFAULT};
                padding: 5px 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {cls.BG_HOVER};
                border-color: {cls.ACCENT};
                color: {cls.TEXT_HIGHLIGHT};
            }}
            QPushButton:pressed {{
                background: {cls.BG_PRESSED};
            }}
            QPushButton:disabled {{
                color: {cls.TEXT_MUTED};
                border-color: {cls.BORDER_DARK};
            }}

            /* Play Button — distinctive green */
            QPushButton#PlayButton {{
                background-color: transparent;
                color: {cls.ACCENT_PLAY};
                border: 1px solid {cls.ACCENT_PLAY};
                font-family: {cls.FONT_FAMILY};
                font-size: {cls.FONT_REGULAR};
                padding: 4px 15px;
                font-weight: bold;
            }}
            QPushButton#PlayButton:hover {{
                background-color: {cls.ACCENT_PLAY_BG};
                color: {cls.TEXT_HIGHLIGHT};
                border-color: {cls.ACCENT_PLAY_BG};
            }}
            QPushButton#PlayButton:pressed {{
                background-color: #008844;
                color: {cls.TEXT_HIGHLIGHT};
            }}

            /* ── Menu Bar ─────────────────────────────────────────────── */
            QMenuBar {{
                background-color: {cls.BG_WINDOW};
                border-bottom: 1px solid {cls.BORDER_DARK};
                color: {cls.TEXT_PRIMARY};
            }}
            QMenuBar::item {{
                padding: 4px 10px;
                background: transparent;
            }}
            QMenuBar::item:selected {{
                background: {cls.BG_CARD};
                color: {cls.TEXT_HIGHLIGHT};
            }}
            QMenu {{
                background-color: {cls.BG_PANEL};
                border: 1px solid {cls.BORDER_DEFAULT};
                color: {cls.TEXT_PRIMARY};
            }}
            QMenu::item {{
                padding: 5px 28px 5px 16px;
            }}
            QMenu::item:selected {{
                background-color: {cls.BG_CARD};
                color: {cls.TEXT_HIGHLIGHT};
            }}
            QMenu::separator {{
                height: 1px;
                background: {cls.BORDER_DEFAULT};
                margin: 3px 0px;
            }}

            /* ── Tabs ─────────────────────────────────────────────────── */
            QTabWidget::pane {{
                border: 1px solid {cls.BORDER_DEFAULT};
                background: {cls.BG_WINDOW};
            }}
            QTabBar::tab {{
                background: {cls.BG_HEADER};
                color: {cls.TEXT_SECONDARY};
                padding: 6px 18px;
                border: 1px solid {cls.BORDER_DARK};
                border-bottom: none;
                margin-right: 1px;
                font-weight: bold;
            }}
            QTabBar::tab:selected {{
                background: {cls.BG_CARD};
                color: {cls.TEXT_HIGHLIGHT};
                border-top: 2px solid {cls.ACCENT};
            }}
            QTabBar::tab:hover:!selected {{
                background: {cls.BG_HOVER};
                color: {cls.TEXT_PRIMARY};
            }}

            /* ── Scroll Bars ──────────────────────────────────────────── */
            QScrollBar:vertical {{
                border: none;
                background: {cls.BG_WINDOW};
                width: 10px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {cls.BORDER_DEFAULT};
                min-height: 24px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {cls.TEXT_MUTED};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar:horizontal {{
                border: none;
                background: {cls.BG_WINDOW};
                height: 10px;
                margin: 0px;
            }}
            QScrollBar::handle:horizontal {{
                background: {cls.BORDER_DEFAULT};
                min-width: 24px;
                border-radius: 3px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {cls.TEXT_MUTED};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}

            /* ── Input Fields ─────────────────────────────────────────── */
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
                background: {cls.BG_INPUT};
                border: 1px solid {cls.BORDER_DEFAULT};
                color: {cls.TEXT_PRIMARY};
                padding: 3px 5px;
                selection-background-color: {cls.BG_SELECTED};
            }}
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
                border: 1px solid {cls.BORDER_FOCUS};
            }}
            QSpinBox::up-button, QDoubleSpinBox::up-button,
            QSpinBox::down-button, QDoubleSpinBox::down-button {{
                background: {cls.BG_CARD};
                border: none;
                width: 14px;
            }}
            QComboBox::drop-down {{
                border: none;
                background: {cls.BG_CARD};
                width: 20px;
            }}
            QComboBox QAbstractItemView {{
                background: {cls.BG_PANEL};
                border: 1px solid {cls.BORDER_DEFAULT};
                selection-background-color: {cls.BG_SELECTED};
            }}

            /* ── Check Boxes ──────────────────────────────────────────── */
            QCheckBox {{
                spacing: 6px;
                color: {cls.TEXT_PRIMARY};
            }}
            QCheckBox::indicator {{
                width: 13px;
                height: 13px;
                background: {cls.BG_INPUT};
                border: 1px solid {cls.BORDER_DEFAULT};
            }}
            QCheckBox::indicator:checked {{
                background: {cls.ACCENT};
                border-color: {cls.ACCENT};
            }}

            /* ── Splitter / Dock Separators ───────────────────────────── */
            QMainWindow::separator {{
                background: {cls.BG_WINDOW};
                width: 4px;
                height: 4px;
            }}
            QMainWindow::separator:hover {{
                background: {cls.ACCENT};
            }}
            QSplitter::handle {{
                background: {cls.BORDER_DARK};
            }}
            QSplitter::handle:hover {{
                background: {cls.ACCENT};
            }}

            /* ── Status Bar ───────────────────────────────────────────── */
            QStatusBar {{
                background: {cls.BG_HEADER};
                color: {cls.TEXT_SECONDARY};
                border-top: 1px solid {cls.BORDER_DARK};
            }}

            /* ── Group Box ────────────────────────────────────────────── */
            QGroupBox {{
                border: 1px solid {cls.BORDER_DEFAULT};
                margin-top: 8px;
                padding-top: 6px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 8px;
                color: {cls.TEXT_SECONDARY};
                font-size: {cls.FONT_SMALL};
            }}

            /* ── Label ────────────────────────────────────────────────── */
            QLabel {{
                background: transparent;
                color: {cls.TEXT_PRIMARY};
            }}

            /* ── Slider ───────────────────────────────────────────────── */
            QSlider::groove:horizontal {{
                height: 4px;
                background: {cls.BORDER_DEFAULT};
            }}
            QSlider::handle:horizontal {{
                background: {cls.ACCENT};
                width: 12px;
                height: 12px;
                margin: -4px 0;
                border-radius: 2px;
            }}
            QSlider::sub-page:horizontal {{
                background: {cls.ACCENT};
            }}

            /* ── Semantic Button: Primary (Teal) ──────────────────────── */
            QPushButton#btnPrimary {{
                background-color: {cls.ACCENT};
                color: {cls.BG_WINDOW};
                border: none;
                padding: 6px 16px;
                font-weight: bold;
            }}
            QPushButton#btnPrimary:hover {{
                background-color: {cls.ACCENT_HOVER};
                color: {cls.BG_WINDOW};
            }}
            QPushButton#btnPrimary:pressed {{
                background-color: {cls.ACCENT};
                opacity: 0.8;
            }}

            /* ── Semantic Button: Play / Success (Green) ──────────────── */
            QPushButton#btnPlay {{
                background-color: {cls.SUCCESS};
                color: {cls.TEXT_HIGHLIGHT};
                border: none;
                padding: 6px 16px;
                font-weight: bold;
            }}
            QPushButton#btnPlay:hover {{
                background-color: {cls.SUCCESS_HOVER};
                color: {cls.TEXT_HIGHLIGHT};
            }}
            QPushButton#btnPlay:pressed {{
                background-color: {cls.SUCCESS};
            }}
        """

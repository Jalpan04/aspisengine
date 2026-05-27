import os
import sys
import copy
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QScrollArea, QFrame,
    QLineEdit, QPushButton, QCheckBox, QComboBox, QSizePolicy, QFormLayout, QDialog, QGridLayout, QMenu
)
from PySide6.QtCore import Qt, Signal, QSize, QRectF, QPointF
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QPixmap
from editor.editor_state import EditorState
from editor.theme import Theme
from editor.inspector import FloatField

class FrameItem(QWidget):
    clicked = Signal(int)
    
    def __init__(self, frame_idx, pixmap, parent=None):
        super().__init__(parent)
        self.frame_idx = frame_idx
        self.pixmap = pixmap
        self.positions = None
        self.setFixedSize(72, 72)
        self.setCursor(Qt.PointingHandCursor)
        self.hovered = False

    def enterEvent(self, event):
        self.hovered = True
        self.update()

    def leaveEvent(self, event):
        self.hovered = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.frame_idx)

    def set_selection_order(self, positions):
        self.positions = positions # List of 1-based indices
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        
        # 1. Background Color
        bg_color = QColor(Theme.BG_CARD)
        if self.positions:
            bg_color = QColor(Theme.BG_SELECTED)
        elif self.hovered:
            bg_color = QColor(Theme.BG_HOVER)
        
        painter.setBrush(bg_color)
        
        # 2. Border Color and Width
        border_color = QColor(Theme.BORDER_DEFAULT)
        border_width = 1
        if self.positions:
            border_color = QColor(Theme.ACCENT)
            border_width = 2
        elif self.hovered:
            border_color = QColor(Theme.BORDER_FOCUS)
            
        painter.setPen(QPen(border_color, border_width))
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 4, 4)
        
        # 3. Render sliced pixmap frame inside (with 8px padding)
        if self.pixmap and not self.pixmap.isNull():
            target_rect = rect.adjusted(8, 8, -8, -8)
            scaled = self.pixmap.scaled(target_rect.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            # Center the scaled frame
            x = target_rect.x() + (target_rect.width() - scaled.width()) // 2
            y = target_rect.y() + (target_rect.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
            
        # 4. Draw frame index (top-left)
        painter.setPen(QColor(Theme.TEXT_MUTED))
        font = QFont(Theme.FONT_FAMILY)
        font.setPixelSize(9)
        painter.setFont(font)
        painter.drawText(rect.adjusted(4, 2, -4, -2), Qt.AlignLeft | Qt.AlignTop, str(self.frame_idx))
        
        # 5. Draw selection order circular badge (bottom-right)
        if self.positions:
            badge_rect = QRectF(rect.width() - 20, rect.height() - 20, 16, 16)
            painter.setBrush(QColor(Theme.ACCENT))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(badge_rect)
            
            painter.setPen(QColor(Theme.BG_WINDOW))
            font.setPixelSize(9)
            font.setBold(True)
            painter.setFont(font)
            
            # Show first position, append "+" if this frame is selected multiple times
            txt = str(self.positions[0])
            if len(self.positions) > 1:
                txt += "+"
            painter.drawText(badge_rect, Qt.AlignCenter, txt)


class FrameSelectorDialog(QDialog):
    def __init__(self, sprite_sheet_path, frame_width, frame_height, current_frames, project_root, scene_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Animation Frames")
        self.resize(550, 480)
        self.setMinimumSize(400, 300)
        self.setStyleSheet(Theme.get_global_stylesheet())
        
        self.sprite_sheet_path = sprite_sheet_path
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.selected_sequence = list(current_frames)
        self.project_root = project_root
        self.scene_path = scene_path
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        
        # Guide Label
        self.info_lbl = QLabel("Click frames in order to build your animation sequence.\nClick an active frame to deselect/remove it from sequence.")
        self.info_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: {Theme.FONT_REGULAR};")
        layout.addWidget(self.info_lbl)
        
        # Scroll area for frame grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"background-color: {Theme.BG_WINDOW}; border: 1px solid {Theme.BORDER_DEFAULT}; border-radius: 4px;")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.grid_widget = QWidget()
        self.grid_widget.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setContentsMargins(8, 8, 8, 8)
        self.grid_layout.setSpacing(8)
        
        scroll.setWidget(self.grid_widget)
        layout.addWidget(scroll)
        
        # Selected Sequence Preview & Action
        seq_layout = QHBoxLayout()
        self.seq_lbl = QLabel("Sequence: None")
        self.seq_lbl.setStyleSheet(f"font-weight: bold; color: {Theme.ACCENT}; font-size: {Theme.FONT_REGULAR};")
        self.seq_lbl.setWordWrap(True)
        seq_layout.addWidget(self.seq_lbl, 4)
        
        clear_btn = QPushButton("Clear")
        clear_btn.setFixedHeight(22)
        clear_btn.setFixedWidth(60)
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.clicked.connect(self.clear_selection)
        seq_layout.addWidget(clear_btn, 1)
        
        layout.addLayout(seq_layout)
        
        # Buttons Row
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(24)
        cancel_btn.setFixedWidth(70)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        
        ok_btn = QPushButton("OK")
        ok_btn.setFixedHeight(24)
        ok_btn.setFixedWidth(70)
        ok_btn.setCursor(Qt.PointingHandCursor)
        ok_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.ACCENT}; color: {Theme.BG_WINDOW}; border: none; font-weight: bold; border-radius: 2px; }} "
            f"QPushButton:hover {{ background-color: {Theme.ACCENT_HOVER}; }}"
        )
        ok_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)
        
        self.frame_buttons = {}
        self.load_and_slice()
        self.update_sequence_label()

    def load_and_slice(self):
        if not self.sprite_sheet_path:
            err = QLabel("No sprite sheet path configured.")
            err.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-style: italic;")
            self.grid_layout.addWidget(err, 0, 0)
            return
            
        # Path resolution strategy matching canvas.py
        full_path = ""
        if os.path.isabs(self.sprite_sheet_path):
            full_path = os.path.normpath(self.sprite_sheet_path)
        else:
            full_path = os.path.normpath(os.path.join(self.project_root, self.sprite_sheet_path))
            if not os.path.exists(full_path) and self.scene_path:
                scene_dir = os.path.dirname(self.scene_path)
                full_path = os.path.normpath(os.path.join(scene_dir, "..", self.sprite_sheet_path))
                if not os.path.exists(full_path):
                    full_path = os.path.normpath(os.path.join(scene_dir, self.sprite_sheet_path))
            if not os.path.exists(full_path):
                full_path = os.path.normpath(os.path.abspath(self.sprite_sheet_path))
                
        if not os.path.exists(full_path):
            err = QLabel(f"Sprite sheet file not found:\n{self.sprite_sheet_path}")
            err.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-style: italic;")
            self.grid_layout.addWidget(err, 0, 0)
            return
            
        pixmap = QPixmap(full_path)
        if pixmap.isNull():
            err = QLabel("Failed to load sprite sheet image.")
            err.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-style: italic;")
            self.grid_layout.addWidget(err, 0, 0)
            return
            
        fw = self.frame_width
        fh = self.frame_height
        if fw <= 0 or fh <= 0:
            err = QLabel("Invalid frame dimensions (Width/Height must be > 0).")
            err.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-style: italic;")
            self.grid_layout.addWidget(err, 0, 0)
            return
            
        cols = pixmap.width() // fw
        rows = pixmap.height() // fh
        total_frames = cols * rows
        
        if total_frames <= 0:
            err = QLabel("Sprite sheet is smaller than a single frame.")
            err.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-style: italic;")
            self.grid_layout.addWidget(err, 0, 0)
            return
            
        max_cols = 6
        for f_idx in range(total_frames):
            row = f_idx // cols
            col = f_idx % cols
            
            # Slice frame
            cropped = pixmap.copy(col * fw, row * fh, fw, fh)
            
            item = FrameItem(f_idx, cropped, self)
            item.clicked.connect(self.on_frame_clicked)
            
            grid_row = f_idx // max_cols
            grid_col = f_idx % max_cols
            self.grid_layout.addWidget(item, grid_row, grid_col)
            self.frame_buttons[f_idx] = item
            
        self.refresh_highlights()

    def on_frame_clicked(self, frame_idx):
        if frame_idx in self.selected_sequence:
            # Deselect / remove all occurrences
            self.selected_sequence = [f for f in self.selected_sequence if f != frame_idx]
        else:
            # Add to end of sequence
            self.selected_sequence.append(frame_idx)
            
        self.refresh_highlights()
        self.update_sequence_label()

    def clear_selection(self):
        self.selected_sequence.clear()
        self.refresh_highlights()
        self.update_sequence_label()

    def refresh_highlights(self):
        # Reset all items
        for f_idx, item in self.frame_buttons.items():
            item.set_selection_order(None)
            
        # Draw badges based on sequence
        for seq_pos, f_idx in enumerate(self.selected_sequence):
            if f_idx in self.frame_buttons:
                # Store all indices (1-based) where this frame occurs
                positions = [i + 1 for i, val in enumerate(self.selected_sequence) if val == f_idx]
                self.frame_buttons[f_idx].set_selection_order(positions)

    def update_sequence_label(self):
        if self.selected_sequence:
            self.seq_lbl.setText(f"Sequence: {', '.join(map(str, self.selected_sequence))}")
        else:
            self.seq_lbl.setText("Sequence: None")


class AnimatorPanel(QWidget):

    def __init__(self):
        super().__init__()
        self.state = EditorState.instance()
        self.state.selection_changed.connect(self.on_selection_changed)
        self.state.scene_loaded.connect(self.refresh_ui)
        self.state.scene_updated.connect(self.refresh_ui)

        # Main Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

        # Main Workspace Columns Layout
        self.workspace_layout = QHBoxLayout()
        self.workspace_layout.setSpacing(10)

        # 1. Left Column: Parameters
        self.param_widget = self.build_column_container("Parameters Register")
        self.workspace_layout.addWidget(self.param_widget, 2)

        # 2. Middle Column: Animation States
        self.states_widget = self.build_column_container("Animation States")
        self.workspace_layout.addWidget(self.states_widget, 3)

        # 3. Right Column: State Transitions
        self.trans_widget = self.build_column_container("State Transitions")
        self.workspace_layout.addWidget(self.trans_widget, 3)

        self.main_layout.addLayout(self.workspace_layout)
        
        # Placeholder for inactive state
        self.placeholder_label = QLabel("Select a GameObject with an Animator component to edit animations.")
        self.placeholder_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: {Theme.FONT_REGULAR};")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.placeholder_label)
        self.placeholder_label.hide()

        self.refresh_ui()

    def build_column_container(self, title):
        frame = QFrame()
        frame.setObjectName("columnContainer")
        frame.setStyleSheet(
            f"QFrame#columnContainer {{ background: {Theme.BG_PANEL}; border: 1px solid {Theme.BORDER_DEFAULT}; border-radius: 4px; }}"
        )
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Header Row
        header_layout = QHBoxLayout()
        lbl = QLabel(title)
        lbl.setStyleSheet(f"font-weight: bold; font-size: {Theme.FONT_REGULAR}; color: {Theme.TEXT_HIGHLIGHT};")
        header_layout.addWidget(lbl)
        header_layout.addStretch()
        
        # Consistent, unclipped Add button
        btn = QPushButton("+ Add")
        btn.setFixedHeight(22)
        btn.setFixedWidth(65)
        btn.setCursor(Qt.PointingHandCursor)
        
        if title == "Parameters Register":
            btn.clicked.connect(self.add_parameter)
            header_layout.addWidget(btn)
        elif title == "Animation States":
            btn.clicked.connect(self.add_state)
            header_layout.addWidget(btn)
        elif title == "State Transitions":
            btn.clicked.connect(self.add_transition)
            header_layout.addWidget(btn)

        layout.addLayout(header_layout)

        # Separator line
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {Theme.BORDER_DEFAULT};")
        layout.addWidget(sep)

        # Scrollable Area for Contents — NO side scrolling
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        content = QWidget()
        content.setStyleSheet("background: transparent; border: none;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(6)
        content_layout.setAlignment(Qt.AlignTop)
        
        scroll.setWidget(content)
        layout.addWidget(scroll)

        # Save reference to content layout so we can clear/rebuild it
        frame.content_layout = content_layout
        
        return frame

    def on_selection_changed(self, obj_id):
        self.refresh_ui()

    def get_selected_animator(self):
        obj = self.state.get_selected_object()
        if not obj:
            return None, None
        anim_data = obj.get("components", {}).get("Animator")
        return obj, anim_data

    def refresh_ui(self):
        obj, anim_data = self.get_selected_animator()
        
        if not obj or not anim_data:
            # Hide Columns, Show Placeholder
            self.placeholder_label.show()
            self.param_widget.hide()
            self.states_widget.hide()
            self.trans_widget.hide()
            return

        # Show Columns, Hide Placeholder
        self.placeholder_label.hide()
        self.param_widget.show()
        self.states_widget.show()
        self.trans_widget.show()

        # Rebuild Columns
        self.rebuild_parameters(obj, anim_data)
        self.rebuild_states(obj, anim_data)
        self.rebuild_transitions(obj, anim_data)

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())

    # --- Rebuild Helpers ---

    def rebuild_parameters(self, obj, data):
        layout = self.param_widget.content_layout
        self.clear_layout(layout)

        params_dict = data.get("parameters", {})
        for name, param in list(params_dict.items()):
            p_frame = QFrame()
            p_frame.setObjectName("paramCard")
            p_frame.setStyleSheet(
                f"QFrame#paramCard {{ background: {Theme.BG_CARD}; border: 1px solid {Theme.BORDER_DEFAULT}; border-radius: 4px; }}"
            )
            
            # Context Menu for copy, paste, delete
            p_frame.setContextMenuPolicy(Qt.CustomContextMenu)
            def make_p_context_menu_callback(n, p):
                return lambda pos: self.show_parameter_context_menu(pos, p_frame, obj, data, n, p)
            p_frame.customContextMenuRequested.connect(make_p_context_menu_callback(name, param))
            
            # Ultra-compact single-row horizontal layout (completely fits narrow registers with no scroll)
            p_layout = QHBoxLayout(p_frame)
            p_layout.setContentsMargins(4, 4, 4, 4)
            p_layout.setSpacing(4)
            
            # 1. Parameter Name Edit
            name_edit = QLineEdit(name)
            name_edit.setPlaceholderText("Name")
            name_edit.setStyleSheet("font-weight: bold;")
            name_edit.setMinimumWidth(50)
            name_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            
            def make_pname_callback(old_n, edit_w):
                return lambda: self.edit_param_name(obj, data, old_n, edit_w.text())
            name_edit.editingFinished.connect(make_pname_callback(name, name_edit))
            p_layout.addWidget(name_edit, 3)

            # 2. Type Selector Dropdown — Solid background, no transparency leak
            type_combo = QComboBox()
            type_combo.addItems(["float", "bool", "trigger"])
            type_combo.setCurrentText(param.get("type", "float"))
            type_combo.setMinimumWidth(60)
            type_combo.setStyleSheet(
                f"QComboBox {{ background-color: {Theme.BG_INPUT}; color: {Theme.TEXT_PRIMARY}; border: 1px solid {Theme.BORDER_DEFAULT}; padding: 2px 4px; }} "
                f"QComboBox QAbstractItemView {{ background-color: {Theme.BG_PANEL}; color: {Theme.TEXT_PRIMARY}; border: 1px solid {Theme.BORDER_DEFAULT}; selection-background-color: {Theme.BG_SELECTED}; }}"
            )
            
            def make_ptype_callback(n, combo_w):
                return lambda text: self.edit_param_type(obj, data, n, text)
            type_combo.currentTextChanged.connect(make_ptype_callback(name, type_combo))
            p_layout.addWidget(type_combo, 2)

            # 3. Dynamic Default Value Editor
            p_type = param.get("type", "float")
            if p_type == "float":
                f_val = param.get("value", 0.0)
                f_field = FloatField(f_val)
                f_field.setMinimumWidth(40)
                def make_pval_float_callback(n):
                    return lambda v, old: self.edit_param_value(obj, data, n, float(v))
                f_field.value_committed.connect(make_pval_float_callback(name))
                p_layout.addWidget(f_field, 2)
            elif p_type == "bool":
                b_val = param.get("value", False)
                b_cb = QCheckBox()  
                b_cb.setChecked(b_val)
                def make_pval_bool_callback(n):
                    return lambda state: self.edit_param_value(obj, data, n, state == 2)
                b_cb.stateChanged.connect(make_pval_bool_callback(name))
                p_layout.addWidget(b_cb, 1, Qt.AlignCenter)
            else:
                fire_btn = QPushButton("Fire")
                fire_btn.setFixedHeight(20)
                fire_btn.setCursor(Qt.PointingHandCursor)
                fire_btn.setStyleSheet(
                    f"QPushButton {{ background: {Theme.ACCENT}; color: {Theme.BG_WINDOW}; border: none; font-weight: bold; border-radius: 2px; padding: 0px 4px; }} "
                    f"QPushButton:hover {{ background: {Theme.ACCENT_HOVER}; }}"
                )
                def make_pval_trigger_callback(n):
                    return lambda: self.edit_param_value(obj, data, n, True)
                fire_btn.clicked.connect(make_pval_trigger_callback(name))
                p_layout.addWidget(fire_btn, 2)
                
            # 4. Delete button
            del_btn = QPushButton("x")
            del_btn.setFixedSize(14, 14)
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.setStyleSheet(
                "QPushButton { background: transparent; color: #777; border: none; font-weight: bold; font-size: 10px; } "
                "QPushButton:hover { color: #ff4444; }"
            )
            
            def make_pdel_callback(n):
                return lambda: self.delete_param(obj, data, n)
            del_btn.clicked.connect(make_pdel_callback(name))
            p_layout.addWidget(del_btn)
            
            layout.addWidget(p_frame)

    def rebuild_states(self, obj, data):
        layout = self.states_widget.content_layout
        self.clear_layout(layout)

        anims_dict = data.get("animations", {})
        for name, anim in list(anims_dict.items()):
            anim_frame = QFrame()
            anim_frame.setObjectName("stateCard")
            anim_frame.setStyleSheet(
                f"QFrame#stateCard {{ background: {Theme.BG_CARD}; border: 1px solid {Theme.BORDER_DEFAULT}; border-radius: 4px; }}"
            )
            
            # Context Menu for copy, paste, delete
            anim_frame.setContextMenuPolicy(Qt.CustomContextMenu)
            def make_s_context_menu_callback(n, a):
                return lambda pos: self.show_state_context_menu(pos, anim_frame, obj, data, n, a)
            anim_frame.customContextMenuRequested.connect(make_s_context_menu_callback(name, anim))
            
            anim_layout = QVBoxLayout(anim_frame)
            anim_layout.setContentsMargins(8, 8, 8, 8)
            anim_layout.setSpacing(6)
            
            # Card Header: Name Input and Delete Button
            header = QHBoxLayout()
            name_edit = QLineEdit(name)
            name_edit.setPlaceholderText("State Name")
            name_edit.setStyleSheet("font-weight: bold; font-size: 12px; background: transparent; border: none; border-bottom: 1px solid transparent;")
            name_edit.textChanged.connect(lambda v, w=name_edit: w.setStyleSheet("font-weight: bold; font-size: 12px; background: transparent; border: none; border-bottom: 1px solid #444;"))
            
            def make_name_callback(old_n, edit_widget):
                return lambda: [
                    edit_widget.setStyleSheet("font-weight: bold; font-size: 12px; background: transparent; border: none; border-bottom: 1px solid transparent;"),
                    self.edit_anim_name(obj, data, old_n, edit_widget.text())
                ]
            name_edit.editingFinished.connect(make_name_callback(name, name_edit))
            
            del_btn = QPushButton("x")
            del_btn.setFixedSize(16, 16)
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.setStyleSheet(
                "QPushButton { background: transparent; color: #777; border: none; font-weight: bold; } "
                "QPushButton:hover { color: #ff4444; }"
            )
            
            def make_del_callback(n):
                return lambda: self.delete_state(obj, data, n)
            del_btn.clicked.connect(make_del_callback(name))
            
            header.addWidget(name_edit)
            header.addStretch()
            header.addWidget(del_btn)
            anim_layout.addLayout(header)

            # Divider line
            sep = QFrame()
            sep.setFrameShape(QFrame.HLine)
            sep.setFixedHeight(1)
            sep.setStyleSheet(f"background: {Theme.BORDER_DARK};")
            anim_layout.addWidget(sep)
            
            # Form Layout for aligned properties
            form = QFormLayout()
            form.setContentsMargins(0, 2, 0, 2)
            form.setSpacing(6)
            form.setLabelAlignment(Qt.AlignRight)
            
            # 1. Frames Edit + Visual Selection Button
            frames_row = QHBoxLayout()
            frames_row.setSpacing(4)
            frames_edit = QLineEdit(",".join(map(str, anim.get("frames", [0]))))
            frames_edit.setPlaceholderText("0,1,2...")
            frames_edit.setToolTip("Comma-separated frame indices (e.g. 0,1,2,3)")
            
            def make_frames_callback(n, edit_w):
                return lambda: self.edit_anim_frames(obj, data, n, edit_w.text())
            frames_edit.editingFinished.connect(make_frames_callback(name, frames_edit))
            frames_row.addWidget(frames_edit, 3)
            
            # The brand-new Premium Visual Splicing selector button
            select_btn = QPushButton("Select...")
            select_btn.setFixedSize(55, 20)
            select_btn.setCursor(Qt.PointingHandCursor)
            select_btn.setStyleSheet(
                f"QPushButton {{ background: {Theme.BG_CARD}; border: 1px solid {Theme.BORDER_DEFAULT}; border-radius: 2px; padding: 0px 4px; font-weight: normal; }} "
                f"QPushButton:hover {{ background: {Theme.BG_HOVER}; border-color: {Theme.ACCENT}; }}"
            )
            
            def make_select_click_callback(state_name, edit_w):
                return lambda: self.open_frame_selector(obj, data, state_name, edit_w)
            select_btn.clicked.connect(make_select_click_callback(name, frames_edit))
            frames_row.addWidget(select_btn)
            
            flabel = QLabel("Frames:")
            flabel.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
            form.addRow(flabel, frames_row)
            
            # 2. FPS & Loop Row
            fps_val = anim.get("frame_rate", 10.0)
            fps_field = FloatField(fps_val, min_val=0.1)
            
            def make_fps_callback(n):
                return lambda v, old: self.edit_anim_fps(obj, data, n, v)
            fps_field.value_committed.connect(make_fps_callback(name))
            
            loop_cb = QCheckBox("Loop")
            loop_cb.setChecked(anim.get("loop", True))
            
            def make_loop_callback(n):
                return lambda state: self.edit_anim_loop(obj, data, n, state == 2)
            loop_cb.stateChanged.connect(make_loop_callback(name))
            
            h_row = QHBoxLayout()
            h_row.addWidget(fps_field, 1)
            h_row.addWidget(loop_cb, 1)
            
            fpslabel = QLabel("Speed (FPS):")
            fpslabel.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
            form.addRow(fpslabel, h_row)
            
            anim_layout.addLayout(form)
            layout.addWidget(anim_frame)

    def rebuild_transitions(self, obj, data):
        layout = self.trans_widget.content_layout
        self.clear_layout(layout)

        transitions = data.get("transitions", [])
        anims_dict = data.get("animations", {})
        params_dict = data.get("parameters", {})

        for idx, trans in enumerate(transitions):
            t_frame = QFrame()
            t_frame.setObjectName("transitionCard")
            t_frame.setStyleSheet(
                f"QFrame#transitionCard {{ background: {Theme.BG_CARD}; border: 1px solid {Theme.BORDER_DEFAULT}; border-radius: 4px; }}"
            )
            
            # Context Menu for copy, paste, delete
            t_frame.setContextMenuPolicy(Qt.CustomContextMenu)
            def make_t_context_menu_callback(index, t):
                return lambda pos: self.show_transition_context_menu(pos, t_frame, obj, data, index, t)
            t_frame.customContextMenuRequested.connect(make_t_context_menu_callback(idx, trans))
            
            t_layout = QVBoxLayout(t_frame)
            t_layout.setContentsMargins(8, 8, 8, 8)
            t_layout.setSpacing(6)
            
            # Row 1: States Selector (From State -> To State)
            row1 = QHBoxLayout()
            from_combo = QComboBox()
            to_combo = QComboBox()
            
            # Explicit solid pop-up styles on QComboBox to completely fix transparency
            from_combo.setStyleSheet(
                f"QComboBox {{ background-color: {Theme.BG_INPUT}; color: {Theme.TEXT_PRIMARY}; border: 1px solid {Theme.BORDER_DEFAULT}; padding: 3px 5px; }} "
                f"QComboBox QAbstractItemView {{ background-color: {Theme.BG_PANEL}; color: {Theme.TEXT_PRIMARY}; border: 1px solid {Theme.BORDER_DEFAULT}; selection-background-color: {Theme.BG_SELECTED}; }}"
            )
            to_combo.setStyleSheet(
                f"QComboBox {{ background-color: {Theme.BG_INPUT}; color: {Theme.TEXT_PRIMARY}; border: 1px solid {Theme.BORDER_DEFAULT}; padding: 3px 5px; }} "
                f"QComboBox QAbstractItemView {{ background-color: {Theme.BG_PANEL}; color: {Theme.TEXT_PRIMARY}; border: 1px solid {Theme.BORDER_DEFAULT}; selection-background-color: {Theme.BG_SELECTED}; }}"
            )
            
            for anim_name in anims_dict.keys():
                from_combo.addItem(anim_name)
                to_combo.addItem(anim_name)
            
            from_combo.setCurrentText(trans.get("from_state", ""))
            to_combo.setCurrentText(trans.get("to_state", ""))
            
            def make_tfrom_callback(index, combo_w):
                return lambda text: self.edit_trans_field(obj, data, index, "from_state", text)
            from_combo.currentTextChanged.connect(make_tfrom_callback(idx, from_combo))
            
            def make_tto_callback(index, combo_w):
                return lambda text: self.edit_trans_field(obj, data, index, "to_state", text)
            to_combo.currentTextChanged.connect(make_tto_callback(idx, to_combo))
            
            del_btn = QPushButton("x")
            del_btn.setFixedSize(16, 16)
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.setStyleSheet(
                "QPushButton { background: transparent; color: #777; border: none; font-weight: bold; } "
                "QPushButton:hover { color: #ff4444; }"
            )
            
            def make_tdel_callback(index):
                return lambda: self.delete_trans(obj, data, index)
            del_btn.clicked.connect(make_tdel_callback(idx))
            
            row1.addWidget(from_combo, 2)
            arrow = QLabel("→")
            arrow.setFixedWidth(16)
            arrow.setAlignment(Qt.AlignCenter)
            arrow.setStyleSheet(f"font-weight: bold; color: {Theme.TEXT_MUTED};")
            row1.addWidget(arrow)
            row1.addWidget(to_combo, 2)
            row1.addWidget(del_btn)
            t_layout.addLayout(row1)

            # Divider line
            sep = QFrame()
            sep.setFrameShape(QFrame.HLine)
            sep.setFixedHeight(1)
            sep.setStyleSheet(f"background: {Theme.BORDER_DARK};")
            t_layout.addWidget(sep)
            
            # Row 2: Aligned Condition Row
            conditions = trans.get("conditions", [])
            if conditions:
                cond = conditions[0]
                row2 = QHBoxLayout()
                row2.setSpacing(4)
                
                if_lbl = QLabel("If:")
                if_lbl.setStyleSheet(f"font-weight: bold; color: {Theme.TEXT_SECONDARY};")
                if_lbl.setFixedWidth(16)
                row2.addWidget(if_lbl)
                
                param_combo = QComboBox()
                param_combo.setStyleSheet(
                    f"QComboBox {{ background-color: {Theme.BG_INPUT}; color: {Theme.TEXT_PRIMARY}; border: 1px solid {Theme.BORDER_DEFAULT}; padding: 3px 5px; }} "
                    f"QComboBox QAbstractItemView {{ background-color: {Theme.BG_PANEL}; color: {Theme.TEXT_PRIMARY}; border: 1px solid {Theme.BORDER_DEFAULT}; selection-background-color: {Theme.BG_SELECTED}; }}"
                )
                for p_name in params_dict.keys():
                    param_combo.addItem(p_name)
                param_combo.setCurrentText(cond.get("parameter", ""))
                
                def make_tparam_callback(index, combo_w):
                    return lambda text: self.edit_trans_cond(obj, data, index, "parameter", text)
                param_combo.currentTextChanged.connect(make_tparam_callback(idx, param_combo))
                row2.addWidget(param_combo, 3)
                
                op_combo = QComboBox()
                op_combo.setStyleSheet(
                    f"QComboBox {{ background-color: {Theme.BG_INPUT}; color: {Theme.TEXT_PRIMARY}; border: 1px solid {Theme.BORDER_DEFAULT}; padding: 3px 5px; }} "
                    f"QComboBox QAbstractItemView {{ background-color: {Theme.BG_PANEL}; color: {Theme.TEXT_PRIMARY}; border: 1px solid {Theme.BORDER_DEFAULT}; selection-background-color: {Theme.BG_SELECTED}; }}"
                )
                
                # Visual symbols mappings keeping full runtime compatibility
                op_to_symbol = {"greater": ">", "less": "<", "equals": "==", "not_equals": "!=", "fired": "fired"}
                symbol_to_op = {">": "greater", "<": "less", "==": "equals", "!=": "not_equals", "fired": "fired"}
                
                p_selected = cond.get("parameter", "")
                p_type = params_dict.get(p_selected, {}).get("type", "float")
                if p_type == "float":
                    op_combo.addItems([">", "<", "==", "!="])
                elif p_type == "bool":
                    op_combo.addItems(["==", "!="])
                else:
                    op_combo.addItems(["fired"])
                
                serialized_op = cond.get("operator", "greater")
                op_combo.setCurrentText(op_to_symbol.get(serialized_op, serialized_op))
                
                def make_top_callback(index, combo_w):
                    return lambda text: self.edit_trans_cond(obj, data, index, "operator", symbol_to_op.get(text, text))
                op_combo.currentTextChanged.connect(make_top_callback(idx, op_combo))
                row2.addWidget(op_combo, 2)
                
                if p_type == "float" or p_type == "bool":
                    val_edit = QLineEdit(str(cond.get("value", 0.0)))
                    val_edit.setMinimumWidth(40)
                    
                    def make_tval_callback(index, edit_w):
                        return lambda: self.edit_trans_cond_value(obj, data, index, edit_w.text())
                    val_edit.editingFinished.connect(make_tval_callback(idx, val_edit))
                    row2.addWidget(val_edit, 2)
                
                t_layout.addLayout(row2)
                
            layout.addWidget(t_frame)

    # --- Splicer Popup Spawner ---
    def open_frame_selector(self, obj, data, state_name, edit_w):
        sprite_sheet = data.get("sprite_sheet", "")
        fw = data.get("frame_width", 32)
        fh = data.get("frame_height", 32)
        
        anim_info = data.get("animations", {}).get(state_name, {})
        current_frames = anim_info.get("frames", [0])
        
        dialog = FrameSelectorDialog(
            sprite_sheet_path=sprite_sheet,
            frame_width=fw,
            frame_height=fh,
            current_frames=current_frames,
            project_root=self.state.project_root,
            scene_path=self.state.current_scene_path,
            parent=self
        )
        
        if dialog.exec() == QDialog.Accepted:
            selected_sequence = dialog.selected_sequence
            if not selected_sequence:
                selected_sequence = [0]
                
            # Update visual frames line-edit
            edit_w.setText(",".join(map(str, selected_sequence)))
            # Propagate back to scene JSON
            self.edit_anim_frames(obj, data, state_name, edit_w.text())

    # --- Right-Click Context Menu Handlers ---
    def show_parameter_context_menu(self, pos, widget, obj, data, name, param):
        menu = QMenu(self)
        menu.setStyleSheet(
            f"QMenu {{ background-color: {Theme.BG_PANEL}; border: 1px solid {Theme.BORDER_DEFAULT}; color: {Theme.TEXT_PRIMARY}; }} "
            f"QMenu::item:selected {{ background-color: {Theme.BG_CARD}; color: {Theme.TEXT_HIGHLIGHT}; }}"
        )
        
        duplicate_act = menu.addAction("Duplicate Parameter")
        menu.addSeparator()
        delete_act = menu.addAction("Delete Parameter")
        
        action = menu.exec(widget.mapToGlobal(pos))
        if action == duplicate_act:
            self.duplicate_parameter(obj, data, name, param)
        elif action == delete_act:
            self.delete_param(obj, data, name)

    def duplicate_parameter(self, obj, data, name, param_data):
        params = copy.deepcopy(data.get("parameters", {}))
        new_name = name + "_copy"
        idx = 1
        while new_name in params:
            new_name = f"{name}_copy{idx}"
            idx += 1
            
        params[new_name] = copy.deepcopy(param_data)
        self.update_component(obj, "Animator", "parameters", params)
        self.refresh_ui()

    def show_state_context_menu(self, pos, widget, obj, data, name, anim):
        menu = QMenu(self)
        menu.setStyleSheet(
            f"QMenu {{ background-color: {Theme.BG_PANEL}; border: 1px solid {Theme.BORDER_DEFAULT}; color: {Theme.TEXT_PRIMARY}; }} "
            f"QMenu::item:selected {{ background-color: {Theme.BG_CARD}; color: {Theme.TEXT_HIGHLIGHT}; }}"
        )
        
        duplicate_act = menu.addAction("Duplicate State")
        menu.addSeparator()
        delete_act = menu.addAction("Delete State")
        
        action = menu.exec(widget.mapToGlobal(pos))
        if action == duplicate_act:
            self.duplicate_state(obj, data, name, anim)
        elif action == delete_act:
            self.delete_state(obj, data, name)

    def duplicate_state(self, obj, data, name, anim_data):
        anims = copy.deepcopy(data.get("animations", {}))
        new_name = name + "_copy"
        idx = 1
        while new_name in anims:
            new_name = f"{name}_copy{idx}"
            idx += 1
            
        anims[new_name] = copy.deepcopy(anim_data)
        anims[new_name]["name"] = new_name
        self.update_component(obj, "Animator", "animations", anims)
        self.refresh_ui()

    def show_transition_context_menu(self, pos, widget, obj, data, index, trans):
        menu = QMenu(self)
        menu.setStyleSheet(
            f"QMenu {{ background-color: {Theme.BG_PANEL}; border: 1px solid {Theme.BORDER_DEFAULT}; color: {Theme.TEXT_PRIMARY}; }} "
            f"QMenu::item:selected {{ background-color: {Theme.BG_CARD}; color: {Theme.TEXT_HIGHLIGHT}; }}"
        )
        
        duplicate_act = menu.addAction("Duplicate Transition")
        menu.addSeparator()
        delete_act = menu.addAction("Delete Transition")
        
        action = menu.exec(widget.mapToGlobal(pos))
        if action == duplicate_act:
            self.duplicate_transition(obj, data, trans)
        elif action == delete_act:
            self.delete_trans(obj, data, index)

    def duplicate_transition(self, obj, data, trans_data):
        trans_list = copy.deepcopy(data.get("transitions", []))
        trans_list.append(copy.deepcopy(trans_data))
        self.update_component(obj, "Animator", "transitions", trans_list)
        self.refresh_ui()

    # --- Structural Commands (Updates scene JSON & registers Undo) ---

    def update_component(self, obj, comp_name, key, value):
        from editor.undo_redo import ChangeComponentCommand
        cmd = ChangeComponentCommand(obj, comp_name, key, value)
        self.state.undo_stack.push(cmd)
        cmd.redo()
        self.state.scene_updated.emit()

    def add_parameter(self):
        obj, data = self.get_selected_animator()
        if not obj: return
        params = copy.deepcopy(data.get("parameters", {}))
        new_name = f"param_{len(params)}"
        params[new_name] = {"type": "float", "value": 0.0}
        self.update_component(obj, "Animator", "parameters", params)
        self.refresh_ui()

    def edit_param_name(self, obj, data, old_name, new_name):
        if not new_name or new_name == old_name: return
        params = copy.deepcopy(data.get("parameters", {}))
        if old_name in params:
            params[new_name] = params.pop(old_name)
            self.update_component(obj, "Animator", "parameters", params)
            
            # Clean transitions
            trans_list = copy.deepcopy(data.get("transitions", []))
            for t in trans_list:
                for c in t.get("conditions", []):
                    if c.get("parameter") == old_name:
                        c["parameter"] = new_name
            self.update_component(obj, "Animator", "transitions", trans_list)
            self.refresh_ui()

    def edit_param_type(self, obj, data, name, p_type):
        params = copy.deepcopy(data.get("parameters", {}))
        if name in params:
            params[name]["type"] = p_type
            if p_type == "float":
                params[name]["value"] = 0.0
            elif p_type == "bool":
                params[name]["value"] = False
            else:
                params[name]["value"] = False
            self.update_component(obj, "Animator", "parameters", params)
            self.refresh_ui()

    def edit_param_value(self, obj, data, name, value):
        params = copy.deepcopy(data.get("parameters", {}))
        if name in params:
            params[name]["value"] = value
            self.update_component(obj, "Animator", "parameters", params)

    def delete_param(self, obj, data, name):
        params = copy.deepcopy(data.get("parameters", {}))
        if name in params:
            del params[name]
        self.update_component(obj, "Animator", "parameters", params)
        
        # Clean transitions
        trans_list = copy.deepcopy(data.get("transitions", []))
        trans_list = [t for t in trans_list if all(c.get("parameter") != name for c in t.get("conditions", []))]
        self.update_component(obj, "Animator", "transitions", trans_list)
        self.refresh_ui()

    def add_state(self):
        obj, data = self.get_selected_animator()
        if not obj: return
        anims = copy.deepcopy(data.get("animations", {}))
        new_name = f"state_{len(anims)}"
        anims[new_name] = {
            "name": new_name,
            "frames": [0],
            "frame_rate": 10.0,
            "loop": True
        }
        self.update_component(obj, "Animator", "animations", anims)
        if not data.get("current_state"):
            self.update_component(obj, "Animator", "current_state", new_name)
        self.refresh_ui()

    def edit_anim_name(self, obj, data, old_name, new_name):
        if not new_name or new_name == old_name: return
        anims = copy.deepcopy(data.get("animations", {}))
        if old_name in anims:
            anim_info = anims.pop(old_name)
            anim_info["name"] = new_name
            anims[new_name] = anim_info
            
            # Clean transitions
            trans_list = copy.deepcopy(data.get("transitions", []))
            for t in trans_list:
                if t.get("from_state") == old_name: t["from_state"] = new_name
                if t.get("to_state") == old_name: t["to_state"] = new_name
            self.update_component(obj, "Animator", "transitions", trans_list)
            
            self.update_component(obj, "Animator", "animations", anims)
            if data.get("current_state") == old_name:
                self.update_component(obj, "Animator", "current_state", new_name)
            self.refresh_ui()

    def edit_anim_frames(self, obj, data, name, frames_str):
        try:
            frames_list = []
            for f in frames_str.split(","):
                f = f.strip()
                if f.isdigit():
                    frames_list.append(int(f))
            if not frames_list:
                frames_list = [0]
            anims = copy.deepcopy(data.get("animations", {}))
            if name in anims:
                anims[name]["frames"] = frames_list
                self.update_component(obj, "Animator", "animations", anims)
        except Exception as e:
            print(f"Error parsing frames: {e}")

    def edit_anim_fps(self, obj, data, name, val):
        anims = copy.deepcopy(data.get("animations", {}))
        if name in anims:
            anims[name]["frame_rate"] = float(val)
            self.update_component(obj, "Animator", "animations", anims)

    def edit_anim_loop(self, obj, data, name, val):
        anims = copy.deepcopy(data.get("animations", {}))
        if name in anims:
            anims[name]["loop"] = bool(val)
            self.update_component(obj, "Animator", "animations", anims)

    def delete_state(self, obj, data, name):
        anims = copy.deepcopy(data.get("animations", {}))
        if name in anims:
            del anims[name]
        self.update_component(obj, "Animator", "animations", anims)
        
        # Clean transitions
        trans_list = copy.deepcopy(data.get("transitions", []))
        trans_list = [t for t in trans_list if t.get("from_state") != name and t.get("to_state") != name]
        self.update_component(obj, "Animator", "transitions", trans_list)
        
        if data.get("current_state") == name:
            next_curr = list(anims.keys())[0] if anims else ""
            self.update_component(obj, "Animator", "current_state", next_curr)
        self.refresh_ui()

    def add_transition(self):
        obj, data = self.get_selected_animator()
        if not obj: return
        trans_list = copy.deepcopy(data.get("transitions", []))
        states = list(data.get("animations", {}).keys())
        params = list(data.get("parameters", {}).keys())
        
        from_s = states[0] if states else ""
        to_s = states[0] if states else ""
        param_s = params[0] if params else ""
        
        new_trans = {
            "from_state": from_s,
            "to_state": to_s,
            "conditions": [
                {"parameter": param_s, "operator": "greater" if data.get("parameters", {}).get(param_s, {}).get("type") == "float" else "equals", "value": 1.0}
            ]
        }
        trans_list.append(new_trans)
        self.update_component(obj, "Animator", "transitions", trans_list)
        self.refresh_ui()

    def edit_trans_field(self, obj, data, index, field, value):
        trans_list = copy.deepcopy(data.get("transitions", []))
        if 0 <= index < len(trans_list):
            trans_list[index][field] = value
            self.update_component(obj, "Animator", "transitions", trans_list)

    def edit_trans_cond(self, obj, data, index, field, value):
        trans_list = copy.deepcopy(data.get("transitions", []))
        if 0 <= index < len(trans_list):
            conds = trans_list[index].get("conditions", [])
            if conds:
                conds[0][field] = value
                
                # Auto adjust operator on parameter changes
                if field == "parameter":
                    params = data.get("parameters", {})
                    p_type = params.get(value, {}).get("type", "float")
                    if p_type == "float":
                        conds[0]["operator"] = "greater"
                        conds[0]["value"] = 0.0
                    elif p_type == "bool":
                        conds[0]["operator"] = "equals"
                        conds[0]["value"] = True
                    else:
                        conds[0]["operator"] = "fired"
                        conds[0]["value"] = True
                        
                self.update_component(obj, "Animator", "transitions", trans_list)
                self.refresh_ui()

    def edit_trans_cond_value(self, obj, data, index, value_str):
        trans_list = copy.deepcopy(data.get("transitions", []))
        if 0 <= index < len(trans_list):
            conds = trans_list[index].get("conditions", [])
            if conds:
                try:
                    if "." in value_str:
                        val = float(value_str)
                    elif value_str.isdigit() or (value_str.startswith("-") and value_str[1:].isdigit()):
                        val = int(value_str)
                    elif value_str.lower() in ("true", "false"):
                        val = value_str.lower() == "true"
                    else:
                        val = value_str
                    conds[0]["value"] = val
                    self.update_component(obj, "Animator", "transitions", trans_list)
                except ValueError:
                    pass

    def delete_trans(self, obj, data, index):
        trans_list = copy.deepcopy(data.get("transitions", []))
        if 0 <= index < len(trans_list):
            trans_list.pop(index)
            self.update_component(obj, "Animator", "transitions", trans_list)
            self.refresh_ui()

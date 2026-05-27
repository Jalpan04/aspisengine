from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPixmap, QCursor, QPolygonF, QPainterPath
from PySide6.QtCore import Qt, QRectF, QPointF
from editor.editor_state import EditorState
from editor.undo_redo import ChangeComponentCommand
import os
import math
import copy
from enum import Enum

class ViewportState(Enum):
    IDLE = 0
    NAVIGATING = 1
    SELECTING = 2
    MANIPULATING = 3

class ToolMode(Enum):
    SELECT = 0
    TRANSLATE = 1
    ROTATE = 2
    SCALE = 3

class SceneCanvas(QWidget):
    # Handle types
    HANDLE_NONE = 0
    HANDLE_MOVE_ALL = 1
    HANDLE_MOVE_X = 2
    HANDLE_MOVE_Y = 3
    HANDLE_ROTATE = 4
    HANDLE_SCALE_UNIFORM = 5
    HANDLE_SCALE_X = 6
    HANDLE_SCALE_Y = 7

    def __init__(self):
        super().__init__()
        self.setMinimumSize(400, 300)
        self.setStyleSheet("background-color: #141414;")
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAcceptDrops(True)
        
        self.state = EditorState.instance()
        self.state.scene_loaded.connect(self.update)
        self.state.scene_updated.connect(self.update)
        self.state.selection_changed.connect(lambda _: self.update())
        
        # View
        self.grid_size = 50
        self.show_grid = True
        self.zoom = 1.0
        self.pan_offset = QPointF(0, 0)
        
        # Interaction
        self.viewport_state = ViewportState.IDLE
        self.tool_mode = ToolMode.TRANSLATE
        self.local_space = True
        self.hovered_handle = self.HANDLE_NONE
        self.active_handle = self.HANDLE_NONE
        self.drag_start = QPointF()
        self.drag_screen_start = QPointF()
        self.drag_obj_start_pos = [0, 0]
        self.drag_rot_start = 0
        self.drag_scale_start = [1, 1]
        self.drag_zoom_start = 1.0
        self.drag_obj_start_bounds = (0, 0)
        self.active_command = None
        
        self.sprite_cache = {}
        self.handle_size = 10

    def get_canvas_center(self):
        cx = (self.width() / 2 - self.pan_offset.x()) / self.zoom - (self.width() / 2 / self.zoom)
        cy = (self.height() / 2 - self.pan_offset.y()) / self.zoom - (self.height() / 2 / self.zoom)
        # Simplified:
        # Screen Center = (W/2, H/2)
        # World Center = screen_to_world(W/2, H/2)
        return self.screen_to_world(self.width()/2, self.height()/2)

    def screen_to_world(self, sx, sy):
        # Inverse of: Screen = World * Zoom + Pan + CenterOffset
        # World = (Screen - Pan - CenterOffset) / Zoom
        cx = self.width() / 2
        cy = self.height() / 2
        return ((sx - self.pan_offset.x() - cx) / self.zoom, 
                (sy - self.pan_offset.y() - cy) / self.zoom)

    def load_sprite(self, path):
        if not path:
            return None
        if path in self.sprite_cache:
            return self.sprite_cache[path]
        full_path = os.path.join(self.state.project_root, path)
        if os.path.exists(full_path):
            pixmap = QPixmap(full_path)
            if pixmap.isNull():
                print(f"Failed to load pixmap: {full_path}")
            else:
                pass 
                # print(f"Loaded pixmap: {full_path} ({pixmap.width()}x{pixmap.height()})")
            self.sprite_cache[path] = pixmap
            return pixmap
        else:
            print(f"Sprite file not found: {full_path}")
        return None

    def get_obj_geometry(self, obj):
        transform = obj.get("components", {}).get("Transform", {})
        sprite_data = obj.get("components", {}).get("SpriteRenderer", {})
        pos = transform.get("position", [0, 0])
        scale = transform.get("scale", [1, 1])
        rotation = transform.get("rotation", 0)
        
        animator_data = obj.get("components", {}).get("Animator")
        if animator_data:
            w = animator_data.get("frame_width", 32) * scale[0]
            h = animator_data.get("frame_height", 32) * scale[1]
        else:
            sprite_path = sprite_data.get("sprite_path", "")
            pixmap = self.load_sprite(sprite_path) if sprite_path else None
            
            if pixmap and not pixmap.isNull():
                w = pixmap.width() * scale[0]
                h = pixmap.height() * scale[1]
            else:
                # Fallback to BoxCollider if available
                box = obj.get("components", {}).get("BoxCollider")
                if box:
                     bs = box.get("size", [50, 50])
                     w = bs[0] * scale[0]
                     h = bs[1] * scale[1]
                else:
                     # Check for Camera component
                     cam = obj.get("components", {}).get("Camera")
                     if cam:
                         cw = cam.get("width", 800.0)
                         ch = cam.get("height", 600.0)
                         cz = cam.get("zoom", 1.0)
                         if cz <= 0.001: cz = 1.0
                         # Camera viewport size in world space
                         w = (cw / cz) # We ignore object scale for camera viewport as runtime does
                         h = (ch / cz)
                     else:
                         # Standard Fallback
                         w = 40 * scale[0]
                         h = 40 * scale[1]
        
        return pos[0], pos[1], w, h, rotation

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # Center the view
        cx = self.width() / 2
        cy = self.height() / 2
        
        painter.translate(cx, cy)
        painter.translate(self.pan_offset)
        painter.scale(self.zoom, self.zoom)
        
        if self.show_grid:
            self.draw_grid(painter)
            self.draw_axes(painter) # New axis drawing
        
        scene = self.state.current_scene
        if scene:
            # Sort by layer: Background (-100), Sprite (0), Text (100)
            def get_layer(o):
                bg = o.get("components", {}).get("Background")
                if bg: return bg.get("layer", 1) - 1000
                sr = o.get("components", {}).get("SpriteRenderer")
                if sr: return sr.get("layer", 1)
                tr = o.get("components", {}).get("TextRenderer")
                if tr: return tr.get("layer", 1)
                return 1
            
            sorted_objs = sorted(scene.objects, key=get_layer)
            
            for obj in sorted_objs:
                self.draw_object(painter, obj)

    def draw_axes(self, painter):
        # Draw World Origin Axes (X=Red, Y=Green)
        # We are already in World Space (mostly, aside from infinite lines)
        
        pen_width = 2 / self.zoom
        
        # X Axis - Dull Red
        painter.setPen(QPen(QColor(70, 40, 40), pen_width))
        painter.drawLine(-10000, 0, 10000, 0)
        
        # Y Axis - Dull Green
        painter.setPen(QPen(QColor(40, 70, 40), pen_width))
        painter.drawLine(0, -10000, 0, 10000)

    def draw_grid(self, painter):
        pen = QPen(QColor(30, 30, 30))
        pen.setWidthF(1 / self.zoom)
        painter.setPen(pen)
        
        # Get visible bounds in world space
        tl_x, tl_y = self.screen_to_world(0, 0)
        br_x, br_y = self.screen_to_world(self.width(), self.height())
        
        x = int(tl_x / self.grid_size) * self.grid_size
        while x < br_x:
            painter.drawLine(x, int(tl_y), x, int(br_y))
            x += self.grid_size
        
        y = int(tl_y / self.grid_size) * self.grid_size
        while y < br_y:
            painter.drawLine(int(tl_x), y, int(br_x), y)
            y += self.grid_size

    def draw_object(self, painter, obj):
        if not obj.get("active", True):
            return
        
        transform = obj.get("components", {}).get("Transform", {})
        sprite_data = obj.get("components", {}).get("SpriteRenderer", {})
        
        pos = transform.get("position", [0, 0])
        scale = transform.get("scale", [1, 1])
        rotation = transform.get("rotation", 0)
        
        # --- Background Drawing ---
        bg_data = obj.get("components", {}).get("Background")
        if bg_data:
            painter.save()
            
            is_fixed = bg_data.get("fixed", True)
            target_rect = QRectF(0, 0, self.width(), self.height()) # Default full screen for fixed

            # If Fixed, reset transform to draw in screen space
            if is_fixed:
                painter.resetTransform()
                # Draw at (0,0) with size (width, height)
                pass 
            else:
                # World Space (Standard)
                painter.translate(pos[0], pos[1])
                painter.rotate(rotation)
                # Use base size logic later

            # Draw Image or Rect
            path = bg_data.get("sprite_path")
            pixmap = self.load_sprite(path) if path else None
            
            color = bg_data.get("color", [255, 255, 255, 255])
            if len(color) == 3: color.append(255)
            
            if pixmap and not pixmap.isNull():
                if is_fixed:
                     target_rect = QRectF(0, 0, self.width(), self.height())
                else:
                     w = pixmap.width() * scale[0]
                     h = pixmap.height() * scale[1]
                     target_rect = QRectF(-w/2, -h/2, w, h)
                
                # Tint? QPainter weak support. 
                painter.drawPixmap(target_rect, pixmap, QRectF(pixmap.rect()))
                
                # Tint overlay
                if color[:3] != [255, 255, 255]:
                    painter.setCompositionMode(QPainter.CompositionMode_Multiply)
                    painter.fillRect(target_rect, QColor(*color))
            else:
                # Draw Color Rect
                if is_fixed:
                    target_rect = QRectF(0, 0, self.width(), self.height())
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QColor(*color))
                    painter.drawRect(target_rect)
                else:
                    base_s = 100
                    w = base_s * scale[0]
                    h = base_s * scale[1]
                    target_rect = QRectF(-w/2, -h/2, w, h)
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QColor(*color))
                    painter.drawRect(target_rect)
            
            painter.restore()
            return # Skip SpriteRenderer if Background exists to avoid double draw? Or allow both?
                 # If both exist, allow both? But usually mutually exclusive component usage.
                 # Let's verify if SpriteRenderer is also there.
        
        if not sprite_data.get("visible", True):
            return
        
        is_selected = (obj.get("id") == self.state.selected_object_id)
        
        animator_data = obj.get("components", {}).get("Animator")
        if animator_data:
            sprite_path = animator_data.get("sprite_sheet", "")
            pixmap = self.load_sprite(sprite_path) if sprite_path else None
            
            frame_width = animator_data.get("frame_width", 32)
            frame_height = animator_data.get("frame_height", 32)
            
            w = frame_width * scale[0]
            h = frame_height * scale[1]
            
            painter.save()
            painter.translate(pos[0], pos[1])
            painter.rotate(rotation)
            
            if pixmap and not pixmap.isNull():
                target_rect = QRectF(-w/2, -h/2, w, h)
                
                # Determine current frame index
                current_state = animator_data.get("current_state", "")
                frames = []
                if current_state and "animations" in animator_data:
                    anim_info = animator_data["animations"].get(current_state, {})
                    frames = anim_info.get("frames", [])
                
                frame_val = frames[0] if frames else 0
                
                cols = pixmap.width() // frame_width if frame_width > 0 else 1
                cols = max(1, cols)
                row = frame_val // cols
                col = frame_val % cols
                
                source_rect = QRectF(col * frame_width, row * frame_height, frame_width, frame_height)
                painter.drawPixmap(target_rect, pixmap, source_rect)
            else:
                # Draw Animator placeholder box
                tint = sprite_data.get("tint", [255, 255, 255, 255])
                if len(tint) == 3: tint.append(255)
                color = QColor(*tint)
                painter.setBrush(QBrush(color))
                
                if is_selected:
                    pen = QPen(QColor(100, 180, 255), 2/self.zoom)
                else:
                    pen = QPen(QColor(50, 50, 50, 150), 1/self.zoom)
                painter.setPen(pen)
                painter.drawRect(QRectF(-w/2, -h/2, w, h))
                
                # Render state name inside the placeholder
                state_text = f"Anim: {animator_data.get('current_state', 'none')}"
                painter.setPen(QColor(255, 255, 255, 200))
                font = QFont("Arial", 8)
                painter.setFont(font)
                painter.drawText(QRectF(-w/2, -h/2, w, h), Qt.AlignCenter, state_text)
                
            # Outline if selected
            if is_selected:
                painter.setPen(QPen(QColor(100, 180, 255), 1/self.zoom, Qt.DashLine))
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(QRectF(-w/2 - 2/self.zoom, -h/2 - 2/self.zoom, w + 4/self.zoom, h + 4/self.zoom))
            
            painter.restore()
            return
            
        sprite_path = sprite_data.get("sprite_path", "")
        pixmap = self.load_sprite(sprite_path) if sprite_path else None
        
        # Calculate Unrotated dimensions
        if pixmap and not pixmap.isNull():
            base_w = pixmap.width()
            base_h = pixmap.height()
        else:
            base_w = 100
            base_h = 100
        
        w = base_w * scale[0]
        h = base_h * scale[1]

        painter.save()
        painter.translate(pos[0], pos[1])
        painter.rotate(rotation)
        
        # Draw Sprite/Box
        if pixmap and not pixmap.isNull():
            target_rect = QRectF(-w/2, -h/2, w, h)
            
            # Simple tinting only if no sprite logic or separate shader
            # For MVP, we just draw the pixmap. Full tinting is expensive in QPainter per frame without caching.
            # But let's check if we can simply multiply color
            painter.drawPixmap(target_rect, pixmap, QRectF(pixmap.rect()))
        else:
            # Fallback Shapes (Square/Circle)
            if "LightSource" not in obj.get("components", {}):
                # Get Tint Color
                tint = sprite_data.get("tint", [255, 255, 255, 255])
                if len(tint) == 3: tint.append(255)
                color = QColor(*tint)
                
                brush = QBrush(color)
                
                # Selection Style (Overlay)
                if is_selected:
                    pen = QPen(QColor(100, 180, 255), 2/self.zoom)
                else:
                    pen = QPen(QColor(50, 50, 50, 150), 1/self.zoom)
                
                painter.setBrush(brush)
                painter.setPen(pen)
                
                # Draw Circle if CircleCollider exists
                if "CircleCollider" in obj.get("components", {}):
                    # Assume diameter matches width/height derived from scale (usually 50 base)
                    painter.drawEllipse(QRectF(-w/2, -h/2, w, h))
                elif "Camera" in obj.get("components", {}):
                    # Special Camera Icon
                    icon_size = 40 
                    iw = icon_size * scale[0]
                    ih = icon_size * scale[1]
                    
                    # Styling: Professional Icon
                    # Fill: Faint Yellow-White
                    # Stroke: Subtle Outline
                    alpha_mult = 1.0 if is_selected else 0.15
                    painter.setBrush(QColor(255, 240, 150, int(40 * alpha_mult))) 
                    painter.setPen(QPen(QColor(255, 240, 150, int(150 * alpha_mult)), 1.5/self.zoom))
                    
                    # 1. Body (Rounded Rect)
                    body_w = iw * 0.7
                    body_h = ih * 0.6
                    path = QPainterPath()
                    path.addRoundedRect(QRectF(-iw/2, -body_h/2, body_w, body_h), 2, 2)
                    
                    # 2. Lens (Triangle on right)
                    lens_size = body_h * 0.7
                    # Triangle pointing right
                    path.moveTo(iw/2 - lens_size, -lens_size/2)
                    path.lineTo(iw/2, -lens_size)
                    path.lineTo(iw/2, lens_size)
                    path.lineTo(iw/2 - lens_size, lens_size/2)
                    
                    painter.drawPath(path)
                    
                elif "TextRenderer" in obj.get("components", {}):
                    # Text Rendering
                    text_data = obj["components"]["TextRenderer"]
                    text_content = text_data.get("text", "Text")
                    font_size = int(text_data.get("font_size", 24))
                    color_list = text_data.get("color", [255, 255, 255])
                    if len(color_list) == 3: color_list.append(255)
                    
                    # Undo Scale so text size is in Screen/World units (not affected by object scale)
                    # Note: Painter is already scaled by self.zoom, which we WANT (to zoom in on text).
                    # But we DON'T want object scale affecting text distortion.
                    painter.save()
                    if scale[0] != 0 and scale[1] != 0:
                        painter.scale(1/scale[0], 1/scale[1])
                    
                    painter.setPen(QColor(*color_list))
                    font = QFont("Arial")
                    font.setPixelSize(font_size)
                    painter.setFont(font)
                    
                    # Draw Center
                    # Bounding box large enough
                    painter.drawText(QRectF(-1000, -1000, 2000, 2000), Qt.AlignCenter, text_content)
                    
                    painter.restore()
                    
                else:
                    # Default Square
                    painter.drawRect(QRectF(-w/2, -h/2, w, h))
                
                # Name Tag
                # Name Tag (Skip if TextRenderer is present to avoid clutter)
                if "TextRenderer" not in obj.get("components", {}):
                    if is_selected:
                        painter.setPen(QPen(Qt.white))
                    else:
                        painter.setPen(QPen(Qt.lightGray))
                        
                    painter.setFont(QFont("Segoe UI", 10))
                    painter.drawText(QRectF(-w/2, -h/2, w, h), Qt.AlignCenter, obj.get("name", "?")[:10])

        # Draw Camera Gizmo
        camera_data = obj.get("components", {}).get("Camera")
        if camera_data:
            cw = camera_data.get("width", 800.0)
            ch = camera_data.get("height", 600.0)
            zoom = camera_data.get("zoom", 1.0)
            if zoom <= 0.001: zoom = 1.0
            
            # The yellow box represents the WORLD AREA visible in the camera.
            # If Zoom > 1 (Zoom In), we see LESS world (Box shrinks).
            # If Zoom < 1 (Zoom Out), we see MORE world (Box grows).
            world_w = cw / zoom
            world_h = ch / zoom
            
            alpha_mult = 1.0 if is_selected else 0.15
            painter.setPen(QPen(QColor(255, 255, 0, int(255 * alpha_mult)), 1.0 / self.zoom)) # Yellow with alpha
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(QRectF(-world_w/2, -world_h/2, world_w, world_h))
            
            # Label
            scale_factor = 1.0 / self.zoom if self.zoom else 1.0
            painter.save()
            painter.scale(scale_factor, scale_factor)
            painter.setPen(QPen(QColor(255, 255, 0, int(255 * alpha_mult))))
            # Adjust label position to top-left of the scaled box
            label_x = -world_w/2 / scale_factor
            label_y = (-world_h/2 / scale_factor) - 20
            painter.drawText(QRectF(label_x, label_y, 100, 20), Qt.AlignLeft, f"Camera ({int(cw)}x{int(ch)})")
            painter.restore()

        # Draw LightSource Gizmo
        light_data = obj.get("components", {}).get("LightSource")
        if light_data:
            color_list = light_data.get("color", [255, 255, 255, 255])
            if len(color_list) < 4:
                color_list = list(color_list) + [255]
            radius = light_data.get("radius", 200.0)
            intensity = light_data.get("intensity", 1.0)
            
            painter.save()
            
            # Draw center glow dot
            glow_color = QColor(*color_list)
            glow_color.setAlphaF(0.4 * min(1.0, intensity))
            painter.setBrush(glow_color)
            painter.setPen(QPen(QColor(255, 230, 100), 1.0 / self.zoom))
            painter.drawEllipse(QPointF(0, 0), 8, 8)
            
            # Draw small ray lines to make it look like a light bulb icon
            painter.setPen(QPen(QColor(255, 230, 100), 1.5 / self.zoom))
            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                painter.drawLine(QPointF(10 * math.cos(rad), 10 * math.sin(rad)),
                                 QPointF(15 * math.cos(rad), 15 * math.sin(rad)))
            
            # Draw Radius Circle if selected
            if is_selected:
                radius_pen = QPen(QColor(255, 255, 100), 1.0 / self.zoom)
                radius_pen.setStyle(Qt.DashLine)
                painter.setPen(radius_pen)
                painter.setBrush(QColor(255, 255, 100, 20)) # Very faint yellow fill
                painter.drawEllipse(QPointF(0, 0), radius, radius)
                
                # Label
                scale_factor = 1.0 / self.zoom if self.zoom else 1.0
                painter.save()
                painter.scale(scale_factor, scale_factor)
                painter.setPen(QColor(255, 255, 100))
                label_y = (-radius / scale_factor) - 15
                painter.drawText(QRectF(0, label_y, 150, 15), Qt.AlignLeft, f"Light (Radius: {int(radius)})")
                painter.restore()
                
            painter.restore()

        # Draw Selection Handles (in rotated local space)
        if is_selected:
            self.draw_handles_local(painter, w, h)
            
        # --- Draw Collider Gizmos (Green - Selected Only) ---
        if is_selected:
            painter.save()
            # Draw BoxCollider
            box = obj.get("components", {}).get("BoxCollider")
            if box:
                size_w, size_h = box.get("size", [50, 50])
                off_x, off_y = box.get("offset", [0, 0])
                
                # Apply Object Scale
                cw = size_w * scale[0]
                ch = size_h * scale[1]
                cox = off_x * scale[0]
                coy = off_y * scale[1]
                
                collider_rect = QRectF(cox - cw/2, coy - ch/2, cw, ch)
                
                # Style: Dashed Light Green with subtle fill
                pen = QPen(QColor(100, 255, 100), 1 / self.zoom)
                pen.setStyle(Qt.DashLine)
                painter.setPen(pen)
                painter.setBrush(QColor(100, 255, 100, 30)) # 30 alpha fill
                painter.drawRect(collider_rect)
                
            # Draw CircleCollider
            circle = obj.get("components", {}).get("CircleCollider")
            if circle:
                radius = circle.get("radius", 25.0)
                off_x, off_y = circle.get("offset", [0, 0])
                
                s_radius = radius * max(abs(scale[0]), abs(scale[1]))
                cox = off_x * scale[0]
                coy = off_y * scale[1]
                
                pen = QPen(QColor(100, 255, 100), 1 / self.zoom)
                pen.setStyle(Qt.DashLine)
                painter.setPen(pen)
                painter.setBrush(QColor(100, 255, 100, 30))
                painter.drawEllipse(QPointF(cox, coy), s_radius, s_radius)
            
            painter.restore()

        painter.restore()

    def draw_handles_local(self, painter, w, h):
        hs = self.handle_size / self.zoom
        length = 60 / self.zoom
        
        # 1. Selection Outline Bounding Box (Subtle light blue dashed line)
        pen = QPen(QColor(80, 150, 255, 180))
        pen.setWidthF(1.5 / self.zoom)
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(QRectF(-w/2, -h/2, w, h))
        
        # Helper to get handle color with hover highlight
        def get_color(handle_type, default_color):
            if self.viewport_state == ViewportState.MANIPULATING:
                if self.active_handle == handle_type:
                    return QColor(240, 200, 80) # Active Gold
            elif self.hovered_handle == handle_type:
                return QColor(240, 200, 80) # Hover Gold
            return default_color

        # Draw handles depending on Tool Mode
        if self.tool_mode == ToolMode.SELECT:
            # No interactive handles, just outline
            return
            
        elif self.tool_mode == ToolMode.TRANSLATE:
            # Draw Translate Gizmo
            # Center free-move block (Gold)
            center_color = get_color(self.HANDLE_MOVE_ALL, QColor(240, 200, 80, 200))
            painter.setPen(QPen(QColor(20, 20, 20), 1 / self.zoom))
            painter.setBrush(QBrush(center_color))
            painter.drawRect(QRectF(-hs/2, -hs/2, hs, hs))
            
            # X-Axis Line and Arrow (Red)
            x_color = get_color(self.HANDLE_MOVE_X, QColor(230, 80, 80))
            painter.setPen(QPen(x_color, 2 / self.zoom))
            painter.drawLine(QPointF(0, 0), QPointF(length, 0))
            
            # X Arrow Head
            arrow_w = 6 / self.zoom
            arrow_h = 10 / self.zoom
            arrow_x = QPolygonF([
                QPointF(length, 0),
                QPointF(length - arrow_h, -arrow_w),
                QPointF(length - arrow_h, arrow_w)
            ])
            painter.setBrush(QBrush(x_color))
            painter.setPen(Qt.NoPen)
            painter.drawPolygon(arrow_x)
            
            # Y-Axis Line and Arrow (Green)
            y_color = get_color(self.HANDLE_MOVE_Y, QColor(80, 230, 80))
            painter.setPen(QPen(y_color, 2 / self.zoom))
            painter.drawLine(QPointF(0, 0), QPointF(0, -length))
            
            # Y Arrow Head
            arrow_y = QPolygonF([
                QPointF(0, -length),
                QPointF(-arrow_w, -length + arrow_h),
                QPointF(arrow_w, -length + arrow_h)
            ])
            painter.setBrush(QBrush(y_color))
            painter.setPen(Qt.NoPen)
            painter.drawPolygon(arrow_y)

        elif self.tool_mode == ToolMode.ROTATE:
            # Draw Rotate Gizmo (Circular Ring)
            ring_color = get_color(self.HANDLE_ROTATE, QColor(80, 230, 80))
            
            pen = QPen(ring_color, 2 / self.zoom)
            pen.setStyle(Qt.DashLine if self.hovered_handle != self.HANDLE_ROTATE and self.active_handle != self.HANDLE_ROTATE else Qt.SolidLine)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(0, 0), length, length)
            
            # Small green circle at top to represent the grab anchor
            painter.setPen(QPen(QColor(20, 20, 20), 1 / self.zoom))
            painter.setBrush(QBrush(ring_color))
            painter.drawEllipse(QPointF(0, -length), hs/2, hs/2)
            
        elif self.tool_mode == ToolMode.SCALE:
            # Center uniform scale box (Blue)
            center_color = get_color(self.HANDLE_SCALE_UNIFORM, QColor(80, 150, 255))
            painter.setPen(QPen(QColor(20, 20, 20), 1 / self.zoom))
            painter.setBrush(QBrush(center_color))
            painter.drawRect(QRectF(-hs/2, -hs/2, hs, hs))
            
            # X-Axis Line and Box (Red)
            x_color = get_color(self.HANDLE_SCALE_X, QColor(230, 80, 80))
            painter.setPen(QPen(x_color, 2 / self.zoom))
            painter.drawLine(QPointF(0, 0), QPointF(length, 0))
            painter.setBrush(QBrush(x_color))
            painter.setPen(QPen(QColor(20, 20, 20), 1 / self.zoom))
            painter.drawRect(QRectF(length - hs/2, -hs/2, hs, hs))
            
            # Y-Axis Line and Box (Green)
            y_color = get_color(self.HANDLE_SCALE_Y, QColor(80, 230, 80))
            painter.setPen(QPen(y_color, 2 / self.zoom))
            painter.drawLine(QPointF(0, 0), QPointF(0, -length))
            painter.setBrush(QBrush(y_color))
            painter.setPen(QPen(QColor(20, 20, 20), 1 / self.zoom))
            painter.drawRect(QRectF(-hs/2, -length - hs/2, hs, hs))

    def rotate_point(self, x, y, cx, cy, angle_deg):
        """Rotate point (x,y) around (cx,cy) by angle."""
        rad = math.radians(angle_deg)
        cos_val = math.cos(rad)
        sin_val = math.sin(rad)
        
        dx = x - cx
        dy = y - cy
        
        rx = dx * cos_val - dy * sin_val
        ry = dx * sin_val + dy * cos_val
        
        return rx + cx, ry + cy

    def hit_handle(self, wx, wy, obj):
        if self.tool_mode == ToolMode.SELECT:
            return self.HANDLE_NONE
            
        cx, cy, w, h, rotation = self.get_obj_geometry(obj)
        hs = self.handle_size / self.zoom
        length = 60 / self.zoom
        tolerance = 8 / self.zoom
        
        # Transform mouse world pos into object local unrotated space
        lx, ly = self.rotate_point(wx, wy, cx, cy, -rotation)
        lx -= cx
        ly -= cy
        
        # Center Pivot/Uniform handle check (Move/Scale)
        if abs(lx) < hs/2 and abs(ly) < hs/2:
            if self.tool_mode == ToolMode.TRANSLATE:
                return self.HANDLE_MOVE_ALL
            elif self.tool_mode == ToolMode.SCALE:
                return self.HANDLE_SCALE_UNIFORM
        
        if self.tool_mode == ToolMode.TRANSLATE:
            # X-Axis handle (Line segment from (0,0) to (length,0))
            if 0 <= lx <= length + tolerance and abs(ly) < tolerance:
                return self.HANDLE_MOVE_X
            # Y-Axis handle (Line segment from (0,0) to (0,-length))
            if -tolerance <= lx <= tolerance and -length - tolerance <= ly <= 0:
                return self.HANDLE_MOVE_Y
                
        elif self.tool_mode == ToolMode.SCALE:
            # X-Axis scale handle
            if 0 <= lx <= length + tolerance and abs(ly) < tolerance:
                return self.HANDLE_SCALE_X
            # Y-Axis scale handle
            if -tolerance <= lx <= tolerance and -length - tolerance <= ly <= 0:
                return self.HANDLE_SCALE_Y
                
        elif self.tool_mode == ToolMode.ROTATE:
            # Circular ring of radius 'length'
            dist = math.sqrt(lx**2 + ly**2)
            if abs(dist - length) < tolerance:
                return self.HANDLE_ROTATE
                
        return self.HANDLE_NONE

    def mousePressEvent(self, event):
        pos = event.position()
        wx, wy = self.screen_to_world(pos.x(), pos.y())

        if event.button() == Qt.LeftButton:
            # Alt + Left Click to pan
            if event.modifiers() & Qt.AltModifier:
                self.grabMouse()
                self.viewport_state = ViewportState.NAVIGATING
                self.drag_start = pos
                self.setCursor(Qt.ClosedHandCursor)
                return

            # Priority 1: UI (Reserved/No-op, but routed)
            # Priority 2: Transform Gizmo of already selected object
            if self.state.selected_object_id:
                obj = self.state.get_selected_object()
                if obj:
                    handle = self.hit_handle(wx, wy, obj)
                    if handle != self.HANDLE_NONE:
                        # Grab mouse and lock into Manipulation State
                        self.grabMouse()
                        self.viewport_state = ViewportState.MANIPULATING
                        self.active_handle = handle
                        self.drag_start = QPointF(wx, wy)
                        self.drag_screen_start = pos
                        
                        transform = obj.get("components", {}).get("Transform", {})
                        self.drag_obj_start_pos = list(transform.get("position", [0, 0]))
                        self.drag_rot_start = transform.get("rotation", 0)
                        self.drag_scale_start = list(transform.get("scale", [1, 1]))
                        
                        # Cache camera zoom
                        cam = obj.get("components", {}).get("Camera")
                        self.drag_zoom_start = cam.get("zoom", 1.0) if cam else 1.0
                        
                        # Initialize Undo Command
                        comp_name = "Transform"
                        key = "position"
                        start_val = self.drag_obj_start_pos
                        
                        if self.tool_mode == ToolMode.ROTATE:
                            key = "rotation"
                            start_val = self.drag_rot_start
                        elif self.tool_mode == ToolMode.SCALE:
                            if cam:
                                comp_name = "Camera"
                                key = "zoom"
                                start_val = self.drag_zoom_start
                            else:
                                key = "scale"
                                start_val = self.drag_scale_start
                                
                        self.active_command = ChangeComponentCommand(obj, comp_name, key, start_val)
                        
                        # Set custom cursor
                        if self.tool_mode == ToolMode.TRANSLATE:
                            self.setCursor(Qt.SizeAllCursor)
                        elif self.tool_mode == ToolMode.ROTATE:
                            self.setCursor(Qt.CrossCursor)
                        elif self.tool_mode == ToolMode.SCALE:
                            self.setCursor(Qt.SizeAllCursor)
                        return

            # Priority 3: Scene Objects (Cameras excluded from single-click selection)
            hit_obj = self.hit_test(wx, wy, allow_camera=False)
            if hit_obj:
                self.state.select_object(hit_obj.get("id"))
                self.update()
            else:
                # Priority 4: Empty Space -> Clear selection and start panning
                self.state.select_object(None)
                self.update()
                self.grabMouse()
                self.viewport_state = ViewportState.NAVIGATING
                self.drag_start = pos
                self.setCursor(Qt.ClosedHandCursor)

        elif event.button() in (Qt.RightButton, Qt.MiddleButton):
            # Consume panning only if we are idle or selecting
            if self.viewport_state in (ViewportState.IDLE, ViewportState.SELECTING):
                self.grabMouse()
                self.viewport_state = ViewportState.NAVIGATING
                self.drag_start = pos
                self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        pos = event.position()
        wx, wy = self.screen_to_world(pos.x(), pos.y())

        # 1. Update hovered handle when idle
        if self.viewport_state == ViewportState.IDLE:
            old_hover = self.hovered_handle
            self.hovered_handle = self.HANDLE_NONE
            if self.state.selected_object_id:
                obj = self.state.get_selected_object()
                if obj:
                    self.hovered_handle = self.hit_handle(wx, wy, obj)
            if self.hovered_handle != old_hover:
                self.update()

        # 2. Camera Navigation
        if self.viewport_state == ViewportState.NAVIGATING:
            delta = pos - self.drag_start
            self.pan_offset += delta
            self.drag_start = pos
            self.update()
            return

        # 3. Handle Manipulation
        if self.viewport_state == ViewportState.MANIPULATING and self.state.selected_object_id:
            obj = self.state.get_selected_object()
            if not obj: return
            
            transform = obj["components"]["Transform"]
            
            # --- Translate Tool ---
            if self.tool_mode == ToolMode.TRANSLATE:
                dx = wx - self.drag_start.x()
                dy = wy - self.drag_start.y()
                
                # Check Local Space vs World Space
                rot_rad = math.radians(transform.get("rotation", 0)) if self.local_space else 0
                cos_r = math.cos(rot_rad)
                sin_r = math.sin(rot_rad)
                
                axis_x = (cos_r, sin_r)
                axis_y = (-sin_r, cos_r)
                
                if self.active_handle == self.HANDLE_MOVE_ALL:
                    new_pos_x = self.drag_obj_start_pos[0] + dx
                    new_pos_y = self.drag_obj_start_pos[1] + dy
                    if event.modifiers() & Qt.ControlModifier:
                        snap = 50.0 # Standard grid size snapping
                        new_pos_x = round(new_pos_x / snap) * snap
                        new_pos_y = round(new_pos_y / snap) * snap
                    transform["position"] = [new_pos_x, new_pos_y]
                    
                elif self.active_handle == self.HANDLE_MOVE_X:
                    dist = dx * axis_x[0] + dy * axis_x[1]
                    if event.modifiers() & Qt.ControlModifier:
                        dist = round(dist / 50.0) * 50.0
                    new_pos_x = self.drag_obj_start_pos[0] + dist * axis_x[0]
                    new_pos_y = self.drag_obj_start_pos[1] + dist * axis_x[1]
                    transform["position"] = [new_pos_x, new_pos_y]
                    
                elif self.active_handle == self.HANDLE_MOVE_Y:
                    dist = dx * axis_y[0] + dy * axis_y[1]
                    if event.modifiers() & Qt.ControlModifier:
                        dist = round(dist / 50.0) * 50.0
                    new_pos_x = self.drag_obj_start_pos[0] + dist * axis_y[0]
                    new_pos_y = self.drag_obj_start_pos[1] + dist * axis_y[1]
                    transform["position"] = [new_pos_x, new_pos_y]

            # --- Rotate Tool ---
            elif self.tool_mode == ToolMode.ROTATE:
                cx, cy = self.drag_obj_start_pos
                angle_start = math.atan2(self.drag_start.y() - cy, self.drag_start.x() - cx)
                angle_now = math.atan2(wy - cy, wx - cx)
                delta_deg = math.degrees(angle_now - angle_start)
                
                raw_rot = self.drag_rot_start + delta_deg
                if event.modifiers() & Qt.ControlModifier:
                    snap_angle = 15.0
                    raw_rot = round(raw_rot / snap_angle) * snap_angle
                    
                transform["rotation"] = raw_rot % 360

            # --- Scale Tool ---
            elif self.tool_mode == ToolMode.SCALE:
                delta_screen_x = pos.x() - self.drag_screen_start.x()
                factor = 1.0 + (delta_screen_x / 100.0)
                factor = max(0.01, min(100.0, factor))
                
                if event.modifiers() & Qt.ControlModifier:
                    factor = round(factor * 10) / 10.0
                    factor = max(0.01, factor)
                
                cam_data = obj.get("components", {}).get("Camera")
                
                if self.active_handle == self.HANDLE_SCALE_UNIFORM:
                    if cam_data:
                        if factor > 0.001:
                            new_zoom = self.drag_zoom_start / factor
                            cam_data["zoom"] = max(0.01, min(100.0, new_zoom))
                    else:
                        nsx = self.drag_scale_start[0] * factor
                        nsy = self.drag_scale_start[1] * factor
                        transform["scale"] = [nsx, nsy]
                        
                elif self.active_handle == self.HANDLE_SCALE_X:
                    if not cam_data:
                        nsx = self.drag_scale_start[0] * factor
                        transform["scale"] = [nsx, self.drag_scale_start[1]]
                        
                elif self.active_handle == self.HANDLE_SCALE_Y:
                    if not cam_data:
                        nsy = self.drag_scale_start[1] * factor
                        transform["scale"] = [self.drag_scale_start[0], nsy]
            
            # Emit scene update to redraw immediately
            self.state.scene_updated.emit()

    def mouseReleaseEvent(self, event):
        # Always release grab when mouse goes up
        try:
            self.releaseMouse()
        except Exception:
            pass
        
        if self.viewport_state == ViewportState.NAVIGATING:
            if event.button() in (Qt.LeftButton, Qt.RightButton, Qt.MiddleButton):
                self.viewport_state = ViewportState.IDLE
                self.setCursor(Qt.ArrowCursor)
                self.update()

        elif self.viewport_state == ViewportState.MANIPULATING:
            if event.button() == Qt.LeftButton:
                self.viewport_state = ViewportState.IDLE
                self.active_handle = self.HANDLE_NONE
                self.setCursor(Qt.ArrowCursor)
                
                # Commit single combined transaction to Undo stack
                if self.active_command and self.state.selected_object_id:
                    obj = self.state.get_selected_object()
                    if obj:
                        comp_name = self.active_command.comp_name
                        key = self.active_command.key
                        final_val = obj["components"][comp_name].get(key)
                        
                        # Only push if the value actually changed
                        if final_val != self.active_command.old_value:
                            self.active_command.new_value = copy.deepcopy(final_val)
                            self.state.undo_stack.push(self.active_command)
                            
                self.active_command = None
                self.update()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.position()
            wx, wy = self.screen_to_world(pos.x(), pos.y())
            
            # Double-click selects the camera
            hit_obj = self.hit_test(wx, wy, allow_camera=True)
            if hit_obj and "Camera" in hit_obj.get("components", {}):
                self.state.select_object(hit_obj.get("id"))
                self.update()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        factor = 1.1 if delta > 0 else 0.9
        mouse_pos = event.position()
        
        old_world = self.screen_to_world(mouse_pos.x(), mouse_pos.y())
        self.zoom *= factor
        self.zoom = max(0.1, min(5.0, self.zoom))
        new_world = self.screen_to_world(mouse_pos.x(), mouse_pos.y())
        
        self.pan_offset.setX(self.pan_offset.x() + (new_world[0] - old_world[0]) * self.zoom)
        self.pan_offset.setY(self.pan_offset.y() + (new_world[1] - old_world[1]) * self.zoom)
        self.update()

    def hit_test(self, wx, wy, allow_camera=False):
        scene = self.state.current_scene
        if not scene: return None
        # Sort by visual order (High Layers on Top)
        # We want to pick the "Topmost" object, so highest Layer first.
        # Layer: Text(100) > Sprite(0) > Background(-100)
        # Sort key: Layer
        def get_layer(o):
            bg = o.get("components", {}).get("Background")
            if bg: return bg.get("layer", 1) - 1000
            sr = o.get("components", {}).get("SpriteRenderer")
            if sr: return sr.get("layer", 1)
            tr = o.get("components", {}).get("TextRenderer")
            if tr: return tr.get("layer", 1)
            return 1
        
        # Sort Descending (Highest First)
        sorted_objs = sorted(scene.objects, key=get_layer, reverse=True)

        camera_hits = []
        for obj in sorted_objs:
            if not obj.get("active", True): continue
            
            cx, cy, w, h, rotation = self.get_obj_geometry(obj)
            
            # Hit test in local space
            lx, ly = self.rotate_point(wx, wy, cx, cy, -rotation)
            dx = abs(lx - cx)
            dy = abs(ly - cy)
            
            if dx <= w/2 and dy <= h/2:
                # If it's a camera, we save it as a low-priority hit
                if "Camera" in obj.get("components", {}):
                    if allow_camera:
                        camera_hits.append(obj)
                    continue
                return obj
        
        # Only return a camera if nothing else was hit
        if allow_camera and camera_hits:
            return camera_hits[0]
        return None

    def cancel_manipulation(self):
        if not self.state.selected_object_id:
            return
        obj = self.state.get_selected_object()
        if not obj:
            return
        
        # Revert changes to cached start transform
        transform = obj.get("components", {}).get("Transform", {})
        if transform:
            transform["position"] = list(self.drag_obj_start_pos)
            transform["rotation"] = self.drag_rot_start
            transform["scale"] = list(self.drag_scale_start)
            
        cam = obj.get("components", {}).get("Camera")
        if cam:
            cam["zoom"] = self.drag_zoom_start
            
        self.viewport_state = ViewportState.IDLE
        self.active_handle = self.HANDLE_NONE
        try:
            self.releaseMouse()
        except Exception:
            pass
        self.setCursor(Qt.ArrowCursor)
        self.update()
        self.state.scene_updated.emit()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_R and event.modifiers() == Qt.ControlModifier:
            self.zoom = 1.0
            self.pan_offset = QPointF(0, 0)
            self.update()
        elif event.key() == Qt.Key_Escape:
            if self.viewport_state == ViewportState.MANIPULATING:
                self.cancel_manipulation()
            else:
                self.state.select_object(None)
                self.update()
        elif event.key() == Qt.Key_Q:
            self.tool_mode = ToolMode.SELECT
            self.update()
        elif event.key() == Qt.Key_W:
            self.tool_mode = ToolMode.TRANSLATE
            self.update()
        elif event.key() == Qt.Key_E:
            self.tool_mode = ToolMode.ROTATE
            self.update()
        elif event.key() == Qt.Key_R:
            self.tool_mode = ToolMode.SCALE
            self.update()
        elif event.key() == Qt.Key_G:
            self.local_space = not self.local_space
            print(f"Space changed: {'Local' if self.local_space else 'World'}")
            self.update()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            for url in urls:
                path = url.toLocalFile()
                if path.endswith(".prefab"):
                    self.instantiate_prefab(path, event.position())
            event.accept()

    def instantiate_prefab(self, path, drop_pos):
        import json
        from shared.scene_schema import GameObject
        
        try:
            with open(path, 'r') as f:
                prefab_data = json.load(f)
            
            # Generate new ID
            import uuid
            new_id = str(uuid.uuid4())
            new_name = prefab_data.get("name", "Prefab Instance")
            
            # Position at drop location
            wx, wy = self.screen_to_world(drop_pos.x(), drop_pos.y())
            
            # Update Position in Transform
            if "components" in prefab_data and "Transform" in prefab_data["components"]:
                prefab_data["components"]["Transform"]["position"] = [wx, wy]
            
            # Assign new ID
            prefab_data["id"] = new_id
            
            # Add to scene
            scene = self.state.current_scene
            if scene:
                scene.objects.append(prefab_data)
                self.state.scene_loaded.emit()
                self.state.select_object(new_id)
                print(f"Instantiated prefab {new_name} at {wx:.1f}, {wy:.1f}")

        except Exception as e:
            print(f"Failed to instantiate prefab: {e}")

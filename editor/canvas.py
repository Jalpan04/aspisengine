from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPixmap, QCursor, QPolygonF, QPainterPath
from PySide6.QtCore import Qt, QRectF, QPointF
from editor.editor_state import EditorState
from editor.undo_redo import ChangeComponentCommand
import os
import math

class SceneCanvas(QWidget):
    # Handle types
    HANDLE_NONE = 0
    HANDLE_MOVE = 1
    HANDLE_SCALE_TL = 2
    HANDLE_SCALE_TR = 3
    HANDLE_SCALE_BL = 4
    HANDLE_SCALE_BR = 5
    HANDLE_ROTATE = 6

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
        self.panning = False
        self.active_handle = self.HANDLE_NONE
        self.drag_start = QPointF()
        self.drag_obj_start_pos = [0, 0] # Store as list to be mutable if needed
        self.drag_rot_start = 0
        self.drag_scale_start = [1, 1]
        self.drag_zoom_start = 1.0
        self.drag_obj_start_bounds = (0, 0) # w, h at start
        
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
                if bg: return bg.get("layer", -100)
                sr = o.get("components", {}).get("SpriteRenderer")
                if sr: return sr.get("layer", 0)
                return 0
            
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
                painter.setBrush(QColor(255, 240, 150, 40)) 
                # Stroke: Subtle Outline
                painter.setPen(QPen(QColor(255, 240, 150, 150), 1.5/self.zoom))
                
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
            
            painter.setPen(QColor(255, 255, 0)) # Yellow
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(QRectF(-world_w/2, -world_h/2, world_w, world_h))
            
            # Label
            scale_factor = 1.0 / self.zoom if self.zoom else 1.0
            painter.save()
            painter.scale(scale_factor, scale_factor)
            painter.setPen(QColor(255, 255, 0))
            # Adjust label position to top-left of the scaled box
            label_x = -world_w/2 / scale_factor
            label_y = (-world_h/2 / scale_factor) - 20
            painter.drawText(QRectF(label_x, label_y, 100, 20), Qt.AlignLeft, f"Camera ({int(cw)}x{int(ch)})")
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
        
        # Selection Outline
        pen = QPen(QColor(100, 180, 255))
        pen.setWidthF(2 / self.zoom)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(QRectF(-w/2, -h/2, w, h))
        
        # Handles
        painter.setBrush(QBrush(QColor(100, 180, 255)))
        
        # Corners relative to center (0,0)
        corners = [
            (-w/2, -h/2), (w/2, -h/2), (-w/2, h/2), (w/2, h/2)
        ]
        
        for cx, cy in corners:
            painter.drawRect(QRectF(cx - hs/2, cy - hs/2, hs, hs))
        
        # Center handle (Move)
        painter.setBrush(QBrush(QColor(255, 200, 100)))
        painter.drawRect(QRectF(-hs/2, -hs/2, hs, hs))
        
        # Rotation Handle (Top)
        painter.setBrush(QBrush(QColor(100, 255, 100)))
        rot_y = -h/2 - 25 / self.zoom
        painter.drawEllipse(QPointF(0, rot_y), hs/2, hs/2)
        painter.drawLine(QPointF(0, -h/2), QPointF(0, rot_y))

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
        cx, cy, w, h, rotation = self.get_obj_geometry(obj)
        hs = self.handle_size / self.zoom
        
        # Transform mouse world pos into object local unrotated space
        # Translate to 0,0 then Rotate by -rotation
        lx, ly = self.rotate_point(wx, wy, cx, cy, -rotation)
        lx -= cx
        ly -= cy
        
        # Now check against unrotated AABB centered at 0,0
        # Box is [-w/2, -h/2] to [w/2, h/2]
        
        # Check rotation handle (Top)
        rot_y = -h/2 - 25 / self.zoom
        if abs(lx - 0) < hs and abs(ly - rot_y) < hs:
            return self.HANDLE_ROTATE
            
        # Check corner handles
        corners = [
            (-w/2, -h/2, self.HANDLE_SCALE_TL),
            (w/2, -h/2, self.HANDLE_SCALE_TR),
            (-w/2, h/2, self.HANDLE_SCALE_BL),
            (w/2, h/2, self.HANDLE_SCALE_BR)
        ]
        for hx, hy, h_type in corners:
            if abs(lx - hx) < hs and abs(ly - hy) < hs:
                return h_type
        
        # Check center (Move)
        if abs(lx) < hs and abs(ly) < hs:
            return self.HANDLE_MOVE
            
        # Check body (Move)
        if -w/2 <= lx <= w/2 and -h/2 <= ly <= h/2:
            return self.HANDLE_MOVE
            
        return self.HANDLE_NONE

    def mousePressEvent(self, event):
        pos = event.position()
        wx, wy = self.screen_to_world(pos.x(), pos.y())
        
        if event.button() == Qt.LeftButton:
            # Check handles on selected object first
            if self.state.selected_object_id:
                obj = self.state.get_selected_object()
                if obj:
                    handle = self.hit_handle(wx, wy, obj)
                    if handle != self.HANDLE_NONE:
                        self.active_handle = handle
                        self.drag_start = QPointF(wx, wy)
                        transform = obj.get("components", {}).get("Transform", {})
                        self.drag_obj_start_pos = list(transform.get("position", [0, 0]))
                        self.drag_rot_start = transform.get("rotation", 0)
                        self.drag_scale_start = list(transform.get("scale", [1, 1]))
                        
                        cam = obj.get("components", {}).get("Camera")
                        if cam:
                            self.drag_zoom_start = cam.get("zoom", 1.0)
                        else:
                            self.drag_zoom_start = 1.0
                        
                        _, _, w, h, _ = self.get_obj_geometry(obj)
                        self.drag_obj_start_bounds = (w, h)
                        return

            # Hit test for selection
            hit_obj = self.hit_test(wx, wy)
            if hit_obj:
                self.state.select_object(hit_obj.get("id"))
                return
            
            # Pan
            self.state.select_object(None)
            self.panning = True
            self.drag_start = pos
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        pos = event.position()
        
        if self.panning:
            delta = pos - self.drag_start
            self.pan_offset += delta
            self.drag_start = pos
            self.update()
            return

        if self.active_handle != self.HANDLE_NONE and self.state.selected_object_id:
            obj = self.state.get_selected_object()
            if not obj: return
            
            wx, wy = self.screen_to_world(pos.x(), pos.y())
            transform = obj["components"]["Transform"]
            

            if self.active_handle == self.HANDLE_MOVE:
                dx = wx - self.drag_start.x()
                dy = wy - self.drag_start.y()
                
                new_pos_x = self.drag_obj_start_pos[0] + dx
                new_pos_y = self.drag_obj_start_pos[1] + dy
                
                # Snapping (Hold Ctrl)
                if event.modifiers() & Qt.ControlModifier:
                    snap = self.grid_size
                    new_pos_x = round(new_pos_x / snap) * snap
                    new_pos_y = round(new_pos_y / snap) * snap
                
                new_pos = [new_pos_x, new_pos_y]
                
                # Push Command (will merge with previous move command)
                cmd = ChangeComponentCommand(obj, "Transform", "position", new_pos)
                self.state.undo_stack.push(cmd)
                cmd.redo() # Ensure visual update
            
            elif self.active_handle in (self.HANDLE_SCALE_TL, self.HANDLE_SCALE_TR, 
                                        self.HANDLE_SCALE_BL, self.HANDLE_SCALE_BR):
                # Distance based uniform scale
                # Center of object
                cx, cy = self.drag_obj_start_pos
                
                # Distance from center at start
                dist_start = math.sqrt((self.drag_start.x() - cx)**2 + (self.drag_start.y() - cy)**2)
                dist_now = math.sqrt((wx - cx)**2 + (wy - cy)**2)
                
                if dist_start > 0.001:
                    factor = dist_now / dist_start
                    factor = max(0.01, min(100.0, factor))
                    
                    # Snapping Scale? Maybe 0.1 increments?
                    if event.modifiers() & Qt.ControlModifier:
                        factor = round(factor * 10) / 10.0
                    
                    nsx = self.drag_scale_start[0] * factor
                    nsy = self.drag_scale_start[1] * factor
                    
                    nsx = max(0.01, min(1000.0, nsx))
                    nsy = max(0.01, min(1000.0, nsy))
                    
                    cam_data = obj.get("components", {}).get("Camera")
                    if cam_data:
                        # Map visual scale factor to Zoom
                        # Bigger Box = Lower Zoom (Zoom Out)
                        # Zoom_New = Zoom_Old / factor
                        if factor > 0.001:
                            new_zoom = self.drag_zoom_start / factor
                            new_zoom = max(0.01, min(100.0, new_zoom))
                            cmd = ChangeComponentCommand(obj, "Camera", "zoom", new_zoom)
                            self.state.undo_stack.push(cmd)
                            cmd.redo()
                    else:
                        cmd = ChangeComponentCommand(obj, "Transform", "scale", [nsx, nsy])
                        self.state.undo_stack.push(cmd)
                        cmd.redo()

            elif self.active_handle == self.HANDLE_ROTATE:
                cx, cy = self.drag_obj_start_pos
                angle_start = math.atan2(self.drag_start.y() - cy, self.drag_start.x() - cx)
                angle_now = math.atan2(wy - cy, wx - cx)
                delta_deg = math.degrees(angle_now - angle_start)
                
                raw_rot = (self.drag_rot_start + delta_deg)
                
                # Angle Snapping (15 degrees)
                if event.modifiers() & Qt.ControlModifier:
                    snap_angle = 15.0
                    raw_rot = round(raw_rot / snap_angle) * snap_angle
                
                new_rot = raw_rot % 360
                
                cmd = ChangeComponentCommand(obj, "Transform", "rotation", new_rot)
                self.state.undo_stack.push(cmd)
                cmd.redo()
            
            self.state.scene_updated.emit()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            
            # Note: We handled undo commands via mergeable commands in mouseMoveEvent
            # So we don't need to push a final command here. 
            # The 'drag_obj_*' state was just for calculation.
            pass
            
            self.panning = False
            self.active_handle = self.HANDLE_NONE
            self.setCursor(Qt.ArrowCursor)

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

    def hit_test(self, wx, wy):
        scene = self.state.current_scene
        if not scene: return None
        # Sort by visual order (High Layers on Top)
        # We want to pick the "Topmost" object, so highest Layer first.
        # Layer: Text(100) > Sprite(0) > Background(-100)
        # Sort key: Layer
        def get_layer(o):
            bg = o.get("components", {}).get("Background")
            if bg: return bg.get("layer", -100)
            sr = o.get("components", {}).get("SpriteRenderer")
            if sr: return sr.get("layer", 0)
            return 0
        
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
                    camera_hits.append(obj)
                    continue
                return obj
        
        # Only return a camera if nothing else was hit
        if camera_hits:
            return camera_hits[0]
        return None

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_R and event.modifiers() == Qt.ControlModifier:
            self.zoom = 1.0
            self.pan_offset = QPointF(0, 0)
            self.update()
        elif event.key() == Qt.Key_Escape:
            self.state.select_object(None)

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

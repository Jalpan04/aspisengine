from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPixmap, QCursor, QPolygonF
from PySide6.QtCore import Qt, QRectF, QPointF
from editor.editor_state import EditorState
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
            sorted_objs = sorted(scene.objects, key=lambda o: 
                o.get("components", {}).get("SpriteRenderer", {}).get("layer", 0))
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
            base_w = 40
            base_h = 40
        
        w = base_w * scale[0]
        h = base_h * scale[1]

        painter.save()
        painter.translate(pos[0], pos[1])
        painter.rotate(rotation)
        
        # Draw Sprite/Box
        if pixmap and not pixmap.isNull():
            tint = sprite_data.get("tint", [255, 255, 255, 255])
            
            # If default white/opaque, draw directly
            if tint == [255, 255, 255, 255] or tint == (255, 255, 255, 255):
                target_rect = QRectF(-w/2, -h/2, w, h)
                painter.drawPixmap(target_rect, pixmap, QRectF(pixmap.rect()))
            else:
                # Create tinted buffer
                buffer = QPixmap(pixmap.size())
                buffer.fill(Qt.transparent)
                
                p = QPainter(buffer)
                p.drawPixmap(0, 0, pixmap)
                p.setCompositionMode(QPainter.CompositionMode_Multiply)
                p.fillRect(buffer.rect(), QColor(*tint))
                p.end()
                
                target_rect = QRectF(-w/2, -h/2, w, h)
                painter.drawPixmap(target_rect, buffer, QRectF(buffer.rect()))
            # Debug: Draw border around sprite to see if it's there
            # painter.setPen(QColor(255, 0, 255))
            # painter.setBrush(Qt.NoBrush)
            # painter.drawRect(target_rect)
        else:
            if is_selected:
                painter.setBrush(QBrush(QColor(70, 70, 90)))
                painter.setPen(QPen(QColor(100, 120, 160), 1/self.zoom))
            else:
                painter.setBrush(QBrush(QColor(50, 50, 50)))
                painter.setPen(QPen(QColor(70, 70, 70), 1/self.zoom))
            painter.drawRect(QRectF(-w/2, -h/2, w, h))
            
            painter.setPen(QColor(120, 120, 120))
            painter.setFont(QFont("Segoe UI", 8))
            painter.drawText(QRectF(-w/2, -h/2, w, h), Qt.AlignCenter, obj.get("name", "?")[:8])

        # Draw Camera Gizmo
        camera_data = obj.get("components", {}).get("Camera")
        if camera_data:
            cw = camera_data.get("width", 800.0)
            ch = camera_data.get("height", 600.0)
            
            painter.setPen(QColor(255, 255, 0)) # Yellow
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(QRectF(-cw/2, -ch/2, cw, ch))
            
            # Draw "Camera" label
            scale_factor = 1.0 / self.zoom if self.zoom else 1.0
            painter.save()
            painter.scale(scale_factor, scale_factor)
            painter.setPen(QColor(255, 255, 0))
            painter.drawText(QRectF(-cw/2/scale_factor, -ch/2/scale_factor - 20, 100, 20), Qt.AlignLeft, "Camera")
            painter.restore()

        # Draw Selection Handles (in rotated local space)
        if is_selected:
            self.draw_handles_local(painter, w, h)
            
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
                # Simple translation works regardless of rotation
                transform["position"] = [
                    self.drag_obj_start_pos[0] + dx, 
                    self.drag_obj_start_pos[1] + dy
                ]
            
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
                    # Clamp factor to avoid crazy values
                    factor = max(0.01, min(100.0, factor))
                    
                    nsx = self.drag_scale_start[0] * factor
                    nsy = self.drag_scale_start[1] * factor
                    
                    # Hard limit on scale to prevent floating point explosion
                    nsx = max(0.01, min(1000.0, nsx))
                    nsy = max(0.01, min(1000.0, nsy))
                    
                    transform["scale"] = [nsx, nsy]

            elif self.active_handle == self.HANDLE_ROTATE:
                cx, cy = self.drag_obj_start_pos
                angle_start = math.atan2(self.drag_start.y() - cy, self.drag_start.x() - cx)
                angle_now = math.atan2(wy - cy, wx - cx)
                delta_deg = math.degrees(angle_now - angle_start)
                transform["rotation"] = (self.drag_rot_start + delta_deg) % 360
            
            self.state.scene_loaded.emit()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
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
        for obj in reversed(scene.objects):
            if not obj.get("active", True): continue
            
            cx, cy, w, h, rotation = self.get_obj_geometry(obj)
            
            # Hit test in local space
            lx, ly = self.rotate_point(wx, wy, cx, cy, -rotation)
            dx = abs(lx - cx)
            dy = abs(ly - cy)
            
            if dx <= w/2 and dy <= h/2:
                return obj
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

# Aspis Engine - API Reference

Complete component and scripting reference for Aspis Engine v1.0 Beta.

## Table of Contents
- [Core Components](#core-components)
- [Physics Components](#physics-components)
- [Rendering Components](#rendering-components)
- [Scripting API](#scripting-api)
- [Input System](#input-system)
- [Scene Management](#scene-management)

---

## Core Components

### Transform
Every GameObject has a Transform. Controls position, rotation, and scale.

**Properties:**
- `position`: `[x, y]` - World position in pixels
- `rotation`: `float` - Rotation in degrees (0-360)
- `scale`: `[x, y]` - Scale multiplier (1.0 = normal size)

**Example:**
```python
transform = game_object.get_component("Transform")
transform.position = [100, 200]
transform.rotation = 45
transform.scale = [2.0, 2.0]  # Double size
```

---

## Physics Components

### RigidBody
Enables physics simulation and movement.

**Properties:**
- `mass`: `float` - Object mass (0 = static/immovable)
- `drag`: `float` - Air resistance (0 = none, higher = more drag)
- `use_gravity`: `bool` - Apply gravity force
- `restitution`: `float` - Bounciness (0 = no bounce, 1 = full bounce)
- `friction`: `float` - Surface friction (0 = ice, 1 = sticky)
- `fixed_rotation`: `bool` - Prevent rotation from physics
- `velocity`: `[vx, vy]` - Current velocity in pixels/second

**Static vs Dynamic:**
- **Static** (mass = 0): Never moves, infinite mass (floors, walls)
- **Dynamic** (mass > 0): Moves and collides with physics

**Example:**
```python
rb = game_object.get_component("RigidBody")
rb.velocity = [200, 0]  # Move right at 200 px/s
rb.use_gravity = True
rb.restitution = 0.5  # Medium bounce
```

### BoxCollider
Rectangular collision shape.

**Properties:**
- `width`: `float` - Collider width in pixels
- `height`: `float` - Collider height in pixels
- `offset`: `[x, y]` - Position offset from Transform

**Example:**
```python
{
  "BoxCollider": {
    "width": 64,
    "height": 64,
    "offset": [0, 0]
  }
}
```

### CircleCollider
Circular collision shape.

**Properties:**
- `radius`: `float` - Circle radius in pixels
- `offset`: `[x, y]` - Position offset from Transform

**Example:**
```python
{
  "CircleCollider": {
    "radius": 32,
    "offset": [0, 0]
  }
}
```

---

## Rendering Components

### Camera
Defines the viewport and rendering area. **Required** - at least one per scene.

**Properties:**
- `zoom`: `float` - Camera zoom level (1.0 = normal, 2.0 = 2x zoom)
- `background_color`: `[r, g, b]` - RGB 0-255

**Example:**
```python
{
  "Camera": {
    "zoom": 1.0,
    "background_color": [30, 30, 30]
  }
}
```

### SpriteRenderer
Renders a colored rectangle or image.

**Properties:**
- `color`: `[r, g, b, a]` - RGBA 0-255
- `image_path`: `string` - Path to image file (relative to project root)
- `layer`: `int` - Render order (higher = drawn on top)

**Example - Solid Color:**
```python
{
  "SpriteRenderer": {
    "color": [255, 0, 0, 255],  # Red
    "layer": 0
  }
}
```

**Example - Image:**
```python
{
  "SpriteRenderer": {
    "image_path": "assets/player.png",
    "layer": 1
  }
}
```

### TextRenderer
Renders text on screen.

**Properties:**
- `text`: `string` - Text content
- `font_size`: `int` - Font size in points
- `color`: `[r, g, b]` - RGB 0-255
- `layer`: `int` - Render order

**Example:**
```python
{
  "TextRenderer": {
    "text": "Score: 0",
    "font_size": 24,
    "color": [255, 255, 255],
    "layer": 10
  }
}
```

---

## Scripting API

### Script Base Class
All gameplay scripts inherit from `Script`.

**Lifecycle Methods:**

#### `start(self)`
Called once when the script initializes (first frame).

```python
def start(self):
    self.health = 100
    print("Player spawned!")
```

#### `update(self, delta_time)`
Called every frame. `delta_time` = seconds since last frame.

```python
def update(self, delta_time):
    self.timer += delta_time
    if self.timer > 5.0:
        self.explode()
```

**Script Properties:**

- `self.game_object`: Reference to the parent GameObject
- `self.transform`: Shortcut to Transform component

**Component Access:**

```python
# Get a component
rb = self.game_object.get_component("RigidBody")
sprite = self.game_object.get_component("SpriteRenderer")

# Check if component exists
if rb:
    rb.velocity = [100, 0]
```

**Example Script:**
```python
from runtime.api import Script, Input, Time

class EnemyAI(Script):
    def start(self):
        self.speed = 100
        self.direction = 1  # 1 = right, -1 = left
    
    def update(self, delta_time):
        # Simple patrol AI
        self.transform.position[0] += self.speed * self.direction * delta_time
        
        # Turn around at edges
        if self.transform.position[0] > 800:
            self.direction = -1
        elif self.transform.position[0] < 0:
            self.direction = 1
```

---

## Input System

### Input Class
Static class for keyboard input.

**Methods:**

#### `Input.get_key(key_name)`
Returns `True` while key is held down.

```python
if Input.get_key("space"):
    print("Space is held")
```

#### `Input.get_key_down(key_name)`
Returns `True` only on the frame the key was pressed (not held).

```python
if Input.get_key_down("space"):
    self.jump()  # Only jump once per press
```

**Key Names:**
- Letters: `"a"`, `"b"`, ..., `"z"`
- Arrows: `"left"`, `"right"`, `"up"`, `"down"`
- Special: `"space"`, `"return"`, `"escape"`, `"shift"`, `"ctrl"`
- Numbers: `"0"`, `"1"`, ..., `"9"`

**Example - Player Movement:**
```python
def update(self, delta_time):
    speed = 200
    
    if Input.get_key("a"):
        self.transform.position[0] -= speed * delta_time
    if Input.get_key("d"):
        self.transform.position[0] += speed * delta_time
    
    if Input.get_key_down("space"):
        self.jump()
```

---

## Scene Management

### Scene File Format
Scenes are stored as JSON files.

**Structure:**
```json
{
  "name": "MainLevel",
  "objects": [
    {
      "id": "unique_id_123",
      "name": "Player",
      "components": {
        "Transform": {
          "position": [100, 100],
          "rotation": 0,
          "scale": [1, 1]
        },
        "SpriteRenderer": {
          "color": [255, 0, 0, 255]
        },
        "BoxCollider": {
          "width": 64,
          "height": 64
        },
        "RigidBody": {
          "mass": 1.0,
          "use_gravity": true
        }
      }
    }
  ]
}
```

### Loading Scenes (Runtime)
Currently scenes are loaded via File → Open in the editor. Programmatic scene switching coming in v1.1.

---

## Time System

### Time Class
Access time-related information.

**Properties:**
- `Time.delta_time`: `float` - Seconds since last frame
- `Time.time`: `float` - Total seconds since game start

**Example - Frame-rate Independent Movement:**
```python
def update(self, delta_time):
    # Move 100 pixels per second (consistent on any FPS)
    self.transform.position[0] += 100 * delta_time
```

---

## Best Practices

### Performance Tips
1. **Cache Component References** in `start()`:
   ```python
   def start(self):
       self.rb = self.game_object.get_component("RigidBody")
   
   def update(self, delta_time):
       self.rb.velocity = [100, 0]  # Faster than get_component every frame
   ```

2. **Use `get_key_down()` for actions**, not `get_key()`:
   ```python
   # Good - fires once
   if Input.get_key_down("space"):
       self.shoot()
   
   # Bad - fires 60 times per second while held
   if Input.get_key("space"):
       self.shoot()
   ```

3. **Static objects must have mass = 0** for best performance

### Physics Tips
- **High speeds?** Objects may tunnel through thin walls. Use thicker colliders or lower speeds.
- **Jittery movement?** Use `velocity` for physics objects, not direct `position` changes.
- **Object stuck?** Check for overlapping colliders at spawn.

### Common Patterns

**Destroy Object (remove from scene):**
```python
# Not yet supported in v1.0 - mark as inactive instead
self.game_object.active = False  # Coming in v1.1
```

**Find Other Objects:**
```python
# Not yet supported - use references set in editor
# Coming in v1.1: GameObject.find("ObjectName")
```

---

## Version History

**v1.0 Beta** (Current)
- Initial release
- Core physics and rendering
- Basic scripting API
- Project management system

**Coming in v1.1**
- Scene switching at runtime
- GameObject.find() / destroy()
- Audio system
- Particle effects
- Tilemap support

---

For more examples, see the `samples/` folder or visit the [GitHub repository](https://github.com/yourusername/aspis).

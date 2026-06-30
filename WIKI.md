# Aspis Engine Wiki

Welcome to the official wiki for the Aspis Engine—a 2D game engine built on Pygame, Pymunk, and PySide6. This guide details the engine architecture, rendering systems, physics systems, prebaked native components, and project deployment tools.

---

## Table of Contents
1. [Architecture Overview](#1-architecture-overview)
2. [Scene and Prefab System](#2-scene-and-prefab-system)
3. [Physics Engine (Pymunk)](#3-physics-engine-pymunk)
4. [Dynamic Lighting & Shadows](#4-dynamic-lighting--shadows)
5. [Scripting API](#5-scripting-api)
6. [Prebaked Native Scripts](#6-prebaked-native-scripts)
7. [Editor Interface](#7-editor-interface)
8. [Standalone Game Exporter](#8-standalone-game-exporter)

---

## 1. Architecture Overview

Aspis Engine uses a hybrid architecture that splits responsibilities between a PySide6-based Editor tool and a Pygame-based Game Loop runtime.

```
                  +--------------------------+
                  |  PySide6 Editor Interface |
                  +-------------+------------+
                                |  Edits Scene Configs
                                v
                  +-------------+------------+
                  |     Scene JSON Schema     |
                  +-------------+------------+
                                |  Runs Launcher
                                v
                  +-------------+------------+
                  |  Pygame Runtime GameLoop  |
                  +-------------+------------+
                   /            |           \
                  v             v            v
           [Physics]       [Lighting]    [Scripts]
           (Pymunk)       (Real-Time)    (Sandboxed)
```

- **Editor Mode**: Form-driven desktop application managing scene serialization, project assets, hierarchy layout, and component configuration.
- **Game Runtime**: Reads scene JSON specifications and boots into a fixed-timestep update loop managing sub-stepped physics calculations, dynamic light blending, script lifecycle execution, and sprite rendering.

---

## 2. Scene and Prefab System

### Scene Configuration
Scenes are saved as `.scene.json` files. They contain global settings and a list of active game objects:
- `settings`: Sets general environment values like `background_color` and `ambient_light` (RGBA).
- `objects`: Array of GameObjects, each declared with an `id`, `name`, `prefab` (optional), and component configurations.

### Prefab Templates
To eliminate copy-pasting redundant component blocks, objects can reference template files (such as platforms, crates, or lights) using the `"prefab"` property. The engine loads the prefab components at startup and merges them with any overrides defined directly in the scene JSON.

#### Example Prefab (`prefabs/crate.json`):
```json
{
  "name": "Physics Crate",
  "components": {
    "SpriteRenderer": {
      "sprite_path": "",
      "layer": 3,
      "visible": true,
      "tint": [160, 105, 50, 255]
    },
    "RigidBody": {
      "mass": 2.0,
      "use_gravity": true,
      "friction": 0.7,
      "restitution": 0.05,
      "velocity": [0.0, 0.0],
      "fixed_rotation": true
    },
    "BoxCollider": {
      "size": [55.0, 55.0],
      "offset": [0.0, 0.0],
      "is_trigger": false
    }
  }
}
```

#### Instantiating a Prefab in Scene JSON:
```json
{
  "id": "crate-1-id",
  "name": "Crate A",
  "prefab": "prefabs/crate.json",
  "components": {
    "Transform": {
      "position": [-160.0, 110.0]
    }
  }
}
```

---

## 3. Physics Engine (Pymunk)

Physics calculations are offloaded to Pymunk. The physics system operates on a fixed time update loop (`120 Hz` fixed logic sub-stepping) to maintain stability in stacking scenarios.

### Physics Components
- **RigidBody**:
  - `mass` (float): Dynamic bodies must have a mass > 0. Static bodies are set to 0.
  - `use_gravity` (boolean): Toggle gravity attraction per body.
  - `drag` (float): Applies linear air resistance to velocity.
  - `fixed_rotation` (boolean): Restricts the angular moment of inertia to infinity. Prevents players or crates from tumbling when moving.
  - `restitution` (float): Elasticity/bounciness coefficient (0.0 = no bounce, 1.0 = perfect bounce).
  - `friction` (float): Friction coefficient (0.0 = ice, 1.0 = heavy grip).
- **BoxCollider**:
  - `size` (2-element array): Width and height of the box collider box in pixels.
  - `offset` (2-element array): Local offset relative to transform position.
- **CircleCollider**:
  - `radius` (float): Radius of the circular physics shell.

---

## 4. Dynamic Lighting & Shadows

The lighting system uses a visibility polygon calculation to compute real-time shadows.

```
       [Light Source]
            *
           / \
          /   \
  =======*     *=======  <- [Collider Obstacle]
  \     /       \     /
   \   /         \   /
    \ /  [Shadow] \ /
     v             v
```

### Components
- **LightSource**:
  - `type` (string): Set to `"point"` (radial gradient) or `"spot"` (conical light matching rotation).
  - `color` (RGBA array): Color tint of the light source.
  - `radius` (float): Distance limit of light emission in pixels.
  - `intensity` (float): Light brightness scaling factor.
  - `cast_shadows` (boolean): Toggle if static/dynamic box/circle colliders block rays.

### Composite Pass
1. **Background Pass**: Draws ambient lighting map using `ambient_light` color.
2. **Raycasting**: Traces paths from the light source center to all vertices of colliders within the light radius to build a visibility polygon mask.
3. **Shadow Masking**: Multiplies the visibility polygon with the light gradient.
4. **Compositing**: Blits light surfaces using `BLEND_RGBA_ADD` onto the background light map, which is then multiplied (`BLEND_RGBA_MULT`) with the main background layer.

---

## 5. Scripting API

Game logic is implemented by inheriting from `runtime.api.Script`.

### Script Lifecycle Methods
- `start(self)`: Executed once when the runtime boots up or when the object is instantiated.
- `update(self, dt)`: Executed every logic loop iteration. `dt` is the elapsed delta time.
- `on_collision_enter(self, other)`: Callback triggered when the collider collides with another game object.

### Injected Helper Methods
Inside any class inheriting from `Script`, the following runtime bindings are available:
- `self.instantiate(prefab_path, position, rotation)`: Spawns a prefab clone into the active scene.
- `self.destroy(game_object)`: Queues a game object for deletion.
- `self.load_scene(scene_name)`: Loads a scene config file relative to the project root.
- `self.play_sound(path)`: Plays a sound file once.
- `self.find_object(name)`: Returns the first GameObject matching the name query.
- `self.find_objects_with_tag(tag)`: Returns a list of all GameObjects matching the tag query.
- `self.set_anim_parameter(name, value)`: Updates animator parameters for state transition checks.
- `self.get_anim_parameter(name)`: Returns current parameter value.

---

## 6. Prebaked Native Scripts

The engine packages standard gameplay actions natively to avoid manual Python file authoring:

### `CameraFollow`
Focuses the camera on a target game object, utilizing smooth interpolation (lerping) to move.
- `target_name` (string): Name of target to track (e.g. `"Knight Player"`).
- `smooth_speed` (float): Interpolation rate multiplier.
- `offset_x` / `offset_y` (float): Offset coordinates from the target's center.

### `AutoRestart`
Monitors the Y-coordinate of a target entity and reloads the current scene if they fall off.
- `target_name` (string): Name of the player object.
- `scene_path` (string): Target scene path to load on restart.
- `fall_threshold` (float): World coordinate Y-limit threshold.
- `restart_delay` (float): Duration in seconds to wait before reloading.

### `SideScrollPlayer`
Executes standard 2D physics-based movements.
- `move_speed` (float): Horizontal running speed force.
- `jump_force` (float): Upward velocity impulse.

---

## 7. Editor Interface

Run the editor interface using:
```bash
python editor/app.py
```

### Key Areas
- **Viewport**: Visualizes active colliders, rendering layers, and object placements.
- **Hierarchy Panel**: Lists all game objects in the scene. Click to select.
- **Inspector Panel**: Exposes components of selected game objects (Transform, SpriteRenderer, LightSource, Script properties) for real-time value editing.
- **Project Manager**: Browse scene configurations, assets, and prefabs.

---

## 8. Standalone Game Exporter

The editor features a built-in game compiler. Clicking the **Export** menu next to File opens the dialog:

- **Asynchronous Compiler Stream**: Displays compiler output logs inside a terminal console in real-time.
- **Build Exclusions**: Strips unused external libraries (kivy, OpenCV, Matplotlib, tests, examples) from compilation.
- **Success Actions**: Upon completion, the Build button converts into a **Close** action. Buttons for **Run Game** (which runs the detached EXE) and **Open Folder** (which displays the build folder in Windows Explorer) are revealed.
- **Lightweight Builds**: Leverages binary collection optimization to package critical SDL/Pymunk DLLs while keeping output standalone size clean.

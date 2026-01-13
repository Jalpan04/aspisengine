# Aspis Engine

![Aspis Engine logo](aspis.png)

**The Lightweight Python Game Engine**

Aspis Engine is a modern, cross-platform 2D game engine built for rapid prototyping and flexibility. Powered by Python 3, PySide6, and Pygame, it offers a familiar and powerful environment for developers to create 2D games without the overhead of massive commercial engines.

## Download

**Want the standalone executable?**
Open **[`index.html`](index.html)** in your browser to access the download page and get the latest version of **Aspis Engine (Windows x64)**.

## Features

### Visual Editor

* **Scene Composition**: Drag-and-drop hierarchy management.
* **Inspector**: Real-time property editing for all components.
* **Asset Browser**: Built-in file management for scripts, sprites, and scenes.
* **Gizmos**: Visual aids for colliders and transforms.

### Python Scripting

* **Native Python**: Write game logic in standard Python files (`.py`).
* **Hot-Reloading**: Edit scripts while the editor runs (limited support).
* **API**: Simple, intuitive API for `start()`, `update(dt)`, and component access.

### Entity-Component-System (ECS)

* **Flexible Design**: Compose complex behaviors by attaching simple, single-purpose components.
* **Performance**: Logic is decoupled from data, allowing for optimized processing.

### Physics Engine

* **Pymunk Integration**: Robust 2D rigid body physics.
* **Collision Detection**: Box and Circle colliders with continuous collision detection (CCD).
* **Dynamics**: Gravity, friction, restitution (bounciness), and drag.

### Rendering

* **Sprite Renderer**: High-performance 2D sprite rendering with tinting and layering.
* **Text Rendering**: Dynamic text support with caching optimization.
* **Camera System**: Zoomable, movable 2D cameras with smooth tracking.

## Getting Started (Source)

If you prefer to run from source or contribute to the engine:

1. **Clone the repository**.
2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Editor**:

   ```bash
   python editor/app.py
   ```

4. **Run a Scene Directly**:

   ```bash
   python main.py --run-scene stress_test/scenes/02_interaction.scene.json
   ```

## Documentation & Demos

* **Stress Tests**: Check the `stress_test/scenes/` folder for comprehensive examples of engine features (physics, hierarchy, text, etc.).
* **Source Code**: The codebase is modular and documented, serving as the primary reference for advanced users.

---
*Open Source (MIT). Powered by Python, PySide6, and Pygame.*

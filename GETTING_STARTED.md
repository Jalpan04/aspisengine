# Getting Started with Aspis Engine

Welcome to **Aspis Engine** - a minimalist Python-based 2D game engine for rapid prototyping and development.

## Installation

1. Download `AspisEngine.exe` from the [Releases](https://github.com/Jalpan04/aspis-engine/releases) page
2. Double-click to launch - no installation required!
3. First launch may take 5-10 seconds as files unpack

## Your First Project

### Step 1: Create a New Project

1. Launch `AspisEngine.exe`
2. The **Aspis Hub** will appear
3. Click **"NEW PROJECT"**
4. Enter a project name (e.g., "MyFirstGame")
5. Choose a folder location
6. Click OK

The engine creates this structure:
```
MyFirstGame/
├── assets/     # Images, sounds, etc.
├── scenes/     # Your game scenes (.scene.json)
└── scripts/    # Python gameplay scripts
```

### Step 2: Understanding the Editor

The editor has 4 main panels:

**Left: Hierarchy** - Lists all objects in your scene  
**Right: Inspector** - Properties of the selected object  
**Center: Canvas** - Visual scene editor with grid  
**Bottom: Project** - Your project's files

### Step 3: Create Your First Scene

1. **Add a Camera** (required for rendering)
   - Right-click in Hierarchy → "Create Empty"
   - Name it "MainCamera"
   - Click "Add Component" → Camera
   - Set Background Color to your preference

2. **Add a Player Object**
   - Create Empty → Name it "Player"
   - Add Component → SpriteRenderer
     - Set Color to red (or pick an image from Assets)
   - Add Component → BoxCollider (for physics)
   - Add Component → RigidBody
     - Mass: 1.0
     - Use Gravity: true

3. **Add Ground**
   - Create Empty → Name it "Ground"
   - Move it to Y: 200 (use Inspector)
   - Add Component → SpriteRenderer (set gray color)
   - Transform: Scale to 20, 1 (wide platform)
   - Add Component → BoxCollider
   - Add Component → RigidBody
     - Mass: 0 (static object)
     - Use Gravity: false

### Step 4: Add Player Movement (Scripting)

1. Click Player in Hierarchy
2. Add Component → Script
3. Click "Create New Script"
4. Name it `player_controller.py`
5. The script editor opens

Paste this code:

```python
from runtime.api import Script, Input

class PlayerController(Script):
    def __init__(self):
        self.speed = 200
        self.jump_force = 500
    
    def update(self, delta_time):
        # Get RigidBody component
        rb = self.game_object.get_component("RigidBody")
        if not rb:
            return
        
        # Horizontal movement
        if Input.get_key("a") or Input.get_key("left"):
            rb.velocity[0] = -self.speed
        elif Input.get_key("d") or Input.get_key("right"):
            rb.velocity[0] = self.speed
        else:
            rb.velocity[0] *= 0.9  # Friction
        
        # Jump
        if Input.get_key_down("space") or Input.get_key_down("w"):
            # Simple jump (check if grounded in real game)
            rb.velocity[1] = -self.jump_force
```

6. Save the script (Ctrl+S)
7. The script is now attached to Player

### Step 5: Save and Test

1. **File → Save Scene** (or Ctrl+S)
2. Save as `main.scene.json` in your `scenes/` folder
3. Click the **Play** button (top toolbar)
4. Your game window opens!
5. Use **A/D** or **Arrow Keys** to move
6. Press **Space** or **W** to jump

Press **ESC** to close the game window.

## Common Controls

**Editor:**
- **Pan Camera**: Middle mouse drag or Space + Drag
- **Zoom**: Mouse wheel
- **Delete Object**: Delete key
- **Undo**: Ctrl+Z
- **Redo**: Ctrl+Shift+Z
- **Save Scene**: Ctrl+S
- **Play Game**: Click Play button or F5

**In-Game:**
- Defined by your scripts (see above example)
- ESC always closes the game window

## Next Steps

### Add More Objects
- Create enemies, collectibles, obstacles
- Use prefabs for reusable objects

### Import Assets
1. Copy image files (PNG) into `assets/` folder
2. Refresh Asset Browser (bottom panel)
3. Drag image onto SpriteRenderer component

### Physics Tips
- **Static objects** (floors, walls): Mass = 0
- **Dynamic objects** (player, enemies): Mass > 0
- **Restitution**: 0 = no bounce, 1 = full bounce
- **Friction**: 0 = ice, 1 = sticky

### Advanced Features
- **Multiple Scenes**: File → New Scene, switch between levels
- **Prefabs**: Save common objects for reuse
- **Component Stacking**: Add multiple scripts to one object

## Troubleshooting

**Game won't start?**
- Ensure you have a Camera in the scene
- Save the scene before playing

**Physics acting weird?**
- Check RigidBody mass values
- Static objects should have mass = 0
- Enable "Use Gravity" only for falling objects

**Script errors?**
- Check the console output in terminal
- Verify script inherits from `Script` class
- Check component names are exact (case-sensitive)

## Community & Support

- **Documentation**: [Full API Reference](./API_REFERENCE.md)
- **GitHub Issues**: Report bugs and request features
- **Examples**: Check the `samples/` folder in source

---

**Ready to build your game?** Start experimenting and share your creations with the community!

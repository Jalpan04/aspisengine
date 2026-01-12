# Social Media Announcements - Aspis Engine v1.0 Beta

Ready-to-post announcement templates for various platforms.

---

## Twitter/X Announcement

### Version 1 (Short & Sweet)
```
🎮 Aspis Engine v1.0 Beta is LIVE!

A brutalist Python-based 2D game engine built for rapid prototyping.

✨ Visual editor with project hub
⚙️ Physics engine (120Hz precision)
🐍 Python scripting API
📦 Single-file executable

Download: https://github.com/Jalpan04/aspis/releases

#gamedev #indiedev #python #gameengine #opensource
```

### Version 2 (Technical)
```
Shipped Aspis Engine v1.0 Beta! 🚀

Built entirely in Python:
- PySide6 editor
- Pymunk physics (120Hz sub-stepping)
- Pygame runtime
- Component-based architecture

Perfect for game jams & prototypes.

⬇️ https://github.com/Jalpan04/aspis

#Python #GameDev #OpenSource
```

### Version 3 (Visual)
```
After months of development...

Aspis Engine v1.0 Beta is here! 🎉

• Brutalist dark theme 🖤
• Drag-and-drop editor
• Built-in physics
• One ~200MB exe

Get it: github.com/Jalpan04/aspis

What will YOU build? 👀

#GameEngine #IndieGameDev
```

---

## Reddit Posts

### r/gamedev
**Title:** `[Release] Aspis Engine v1.0 Beta - Python-Based 2D Game Engine`

```markdown
Hey r/gamedev!

I'm excited to share the first beta release of **Aspis Engine** - a 2D game engine I've been building with Python.

## What is it?

A lightweight, brutalist game engine designed for **rapid prototyping** and **game jams**. Think of it as a simpler, Python-powered alternative to Unity/Godot for 2D games.

## Key Features

**Editor:**
- Visual scene editor with hierarchy & inspector
- Project hub for managing multiple games
- Component-based architecture
- Asset browser for organizing files
- Full undo/redo system

**Runtime:**
- Physics engine (Pymunk) with 120Hz sub-stepping
- Python scripting with simple start()/update() lifecycle
- Input handling (keyboard)
- Sprite rendering & text

**Distribution:**
- Single-file executable (~200MB)
- Portable projects with standard folder structure
- No installation required

## Why Python?

I wanted something that:
1. Is easy to extend and modify
2. Has a minimal learning curve for scripting
3. Can be rapidly iterated on
4. Is truly open source

## Screenshots

[Link to screenshots - upload to imgur or similar]

## Download & Docs

- **GitHub:** https://github.com/Jalpan04/aspis
- **Download:** https://github.com/Jalpan04/aspis/releases
- **Getting Started:** Full tutorial in the docs

## Current Limitations (Beta)

This is v1.0 Beta, so:
- Windows only (Linux/Mac coming in v1.1)
- No audio system yet
- Scene switching limited to editor

## Feedback Welcome!

I'd love to hear your thoughts, bug reports, and feature requests. This is my first public release, so any feedback helps!

**What would you use this for?** Game jams? Prototyping? Learning?

---

**Tech Stack:** Python 3.13, PySide6, Pygame, Pymunk  
**License:** MIT
```

### r/Python
**Title:** `[Project] Built a 2D game engine entirely in Python - Aspis Engine v1.0 Beta`

```markdown
I've spent the last few months building a 2D game engine using pure Python, and I'm excited to share the first beta release!

## The Stack

- **PySide6** (Qt for Python) - Visual editor UI
- **Pygame** - 2D rendering and runtime
- **Pymunk** - Physics simulation
- **PyInstaller** - Single-file executable packaging

## What It Does

Aspis Engine is a component-based 2D game engine with:

1. **Visual Editor**
   - Scene hierarchy and inspector panels
   - Drag-and-drop canvas
   - Project management hub
   - Asset browser

2. **Physics System**
   - Gravity, friction, collisions
   - Rigid bodies with 120Hz sub-stepping
   - Box and circle colliders

3. **Python Scripting**
   - Simple `Script` base class
   - `start()` and `update()` lifecycle
   - Component access via `get_component()`

4. **Distribution**
   - PyInstaller builds a single ~200MB exe
   - Projects are portable folders

## Why I Built This

I wanted to create something that:
- Makes 2D game prototyping **fast**
- Is **fully open source** and hackable
- Has a **low barrier to entry** (it's just Python!)
- Can be used for **teaching game dev concepts**

## Example Code

Creating a player controller is simple:

```python
from runtime.api import Script, Input

class PlayerController(Script):
    def start(self):
        self.speed = 200
    
    def update(self, delta_time):
        rb = self.game_object.get_component("RigidBody")
        
        if Input.get_key("a"):
            rb.velocity[0] = -self.speed
        elif Input.get_key("d"):
            rb.velocity[0] = self.speed
```

## Links

- **GitHub:** https://github.com/Jalpan04/aspis
- **Download:** https://github.com/Jalpan04/aspis/releases
- **Documentation:** In the repo

## Challenges & Learnings

Building this taught me a lot about:
- Qt/PySide6 architecture
- Physics engine integration
- PyInstaller bundling issues (DLL hell!)
- Component-based design patterns

## What's Next?

v1.1 will add:
- Audio system
- Linux/Mac builds
- Tilemap support
- Particle effects

**Feedback, questions, and contributions welcome!** 🚀

---

**License:** MIT  
**Python Version:** 3.13+
```

### r/IndieGaming
**Title:** `Made a brutalist 2D game engine for rapid prototyping - Free & Open Source`

```markdown
Just released **Aspis Engine v1.0 Beta** - a Python-based 2D game engine perfect for game jams and quick prototypes!

🎮 **Why it's useful:**
- Visual editor (no code needed for scene setup)
- Built-in physics
- Python scripting (super easy to learn)
- Single exe file (~200MB, portable)
- Free & MIT licensed

🎨 **Design Philosophy:**
Brutalist UI - no distractions, just tools. Dark theme with sharp rectangles and dull cyan accents.

📦 **Perfect for:**
- Game jams (rapid iteration)
- Prototyping ideas
- Learning game dev
- Creating simple 2D games

**Download:** https://github.com/Jalpan04/aspis/releases  
**Docs:** Full tutorial included

**What kind of games would you make with this?** I'd love to see what the community builds! 🚀
```

---

## Discord / Communities

### General Announcement
```
@everyone Aspis Engine v1.0 Beta is out! 🎉

A brutalist 2D game engine built with Python, perfect for game jams and rapid prototyping.

**Features:**
✅ Visual editor
✅ Physics engine
✅ Python scripting
✅ Single-file executable
✅ Free & open source

**Download:** https://github.com/Jalpan04/aspis/releases

Try it out and let me know what you think!
```

---

## Dev.to / Hashnode Blog Post

**Title:** `I Built a 2D Game Engine in Python - Here's What I Learned`

```markdown
# I Built a 2D Game Engine in Python - Here's What I Learned

After several months of development, I'm excited to announce the release of **Aspis Engine v1.0 Beta** - a brutalist 2D game engine built entirely with Python.

[Screenshot of editor]

## Why Another Game Engine?

With Unity, Godot, and GameMaker already available, why create another engine? Here's my reasoning:

1. **Python-First Design** - Everything is hackable and modifiable
2. **Learning Tool** - Simplifies game dev concepts
3. **Rapid Prototyping** - Perfect for game jams
4. **Open Source** - Truly free, MIT licensed
5. **Personal Challenge** - I wanted to understand game engine architecture

## The Architecture

### Tech Stack
- **PySide6** (Qt) for the editor UI
- **Pygame** for rendering
- **Pymunk** for physics
- **PyInstaller** for distribution

### Component System

Aspis uses an Entity-Component-System (ECS) inspired architecture:

```python
# Every game object is a collection of components
game_object = {
    "Transform": {"position": [x, y], "rotation": 0, "scale": [1, 1]},
    "SpriteRenderer": {"color": [255, 0, 0, 255]},
    "BoxCollider": {"width": 64, "height": 64},
    "RigidBody": {"mass": 1.0, "use_gravity": True}
}
```

Scripts inherit from a base `Script` class:

```python
class PlayerController(Script):
    def start(self):
        self.speed = 200
    
    def update(self, delta_time):
        # Game logic here
        pass
```

## Biggest Challenges

### 1. Physics Precision

Getting stable physics was tricky. Solution: 120Hz sub-stepping.

### 2. PyInstaller DLL Hell

Bundling PySide6 and Pygame into one executable was painful. Solved by using single-file mode with `--onefile`.

### 3. Path Resolution

Runtime needed to find scripts when frozen. Created a `shared/paths.py` utility to handle `sys._MEIPASS`.

### 4. Editor Performance

Qt's scene editor could lag with many objects. Optimized by caching references and using viewport culling.

## What I Learned

1. **Game engines are HARD** - Immense respect for Unity/Godot teams
2. **Python is viable** - With proper architecture, Python works for real tools
3. **UI/UX matters** - Even for dev tools, good design improves workflow
4. **Documentation is crucial** - Without it, no one will use your tool

## Current Features (v1.0 Beta)

✅ Visual scene editor  
✅ Project management hub  
✅ Physics simulation  
✅ Python scripting API  
✅ Component-based architecture  
✅ Undo/redo system  
✅ Single-file executable  

## Roadmap

**v1.1:**
- Audio system
- Linux/Mac builds
- Tilemap support
- Particle effects

**v1.2+:**
- Visual scripting
- Animation system
- Multiplayer networking

## Try It Out!

- **GitHub:** https://github.com/Jalpan04/aspis
- **Download:** https://github.com/Jalpan04/aspis/releases
- **Docs:** Full getting started guide included

## Feedback Welcome!

This is my first public release. If you try it out, I'd love to hear:
- What worked well
- What was confusing
- What features you'd like

Drop a comment or open an issue on GitHub!

---

**License:** MIT  
**Built with:** Python 3.13, PySide6, Pygame, Pymunk
```

---

## Post-Launch Timeline

**Day 1:**
- [ ] Post on Twitter/X (Version 1)
- [ ] Post on r/gamedev
- [ ] Post on r/Python
- [ ] Share in relevant Discord servers

**Day 2:**
- [ ] Post on r/IndieGaming
- [ ] Tweet progress update / screenshots
- [ ] Respond to all comments

**Day 3:**
- [ ] Write Dev.to blog post
- [ ] Share blog post on Twitter
- [ ] Post in Hacker News (if appropriate)

**Week 1:**
- [ ] Monitor GitHub issues
- [ ] Respond to feedback
- [ ] Plan v1.1 features based on requests

---

**Tips for Maximum Reach:**

1. **Include visuals** - Screenshots, GIFs, or short video clips
2. **Time your posts** - Post on Reddit/HN during peak hours (US morning)
3. **Engage with comments** - Respond to every question/feedback
4. **Cross-post strategically** - Wait 24h between similar subreddit posts
5. **Use hashtags wisely** - Don't spam, use 3-5 relevant tags

---

**Ready to announce?** Start with Twitter and r/gamedev, then expand! 🚀

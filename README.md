# Aspis Engine

![Logo](logo.png)

**A brutalist Python-based 2D game engine for rapid prototyping and development.**

[![Version](https://img.shields.io/badge/version-1.0%20Beta-blue)](https://github.com/yourusername/aspis/releases)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.13-blue)](https://www.python.org/)

---

## What is Aspis Engine?

Aspis is a **lightweight, brutalist 2D game engine** built with Python. It features:

- **Visual Editor** with hierarchy, inspector, and asset browser
- **Physics Engine** powered by Pymunk (gravity, collision, rigid bodies)
- **Component System** for modular game object design
- **Python Scripting** for gameplay logic
- **Project Hub** for managing multiple games
- **Single-File Distribution** - one ~200MB exe, no installation

Perfect for **game jams**, **prototypes**, and **learning game development**.

---

## Quick Start

### Download & Launch

1. Download `AspisEngine.exe` from [Releases](https://github.com/yourusername/aspis/releases/latest)
2. Double-click to run (first launch takes 5-10 seconds)
3. Create your first project!

### 5-Minute Tutorial

```
1. Click "NEW PROJECT" → Name it "MyGame"
2. Add a Camera (right-click Hierarchy → Create Empty)
3. Add a Player (Create Empty → Add SpriteRenderer + BoxCollider + RigidBody)  
4. Add Ground (Create Empty → Set mass to 0, disable gravity)
5. Click PLAY ▶ to test
```

**Full Tutorial:** [Getting Started Guide](GETTING_STARTED.md)

---

## Features

### Editor
- **Project Hub**: Manage multiple game projects with search and recent history
- **Visual Scene Editor**: Drag-drop canvas with grid snapping  
- **Component Inspector**: Real-time property editing
- **Asset Browser**: Import PNG images, manage project files
- **Undo/Redo**: Full history for all edits

### Runtime
- **Physics**: Gravity, friction, restitution, collisions (Pymunk-based)
- **Rendering**: Sprite rendering, text, layered drawing (Pygame-based)
- **Scripting**: Python classes with `start()` and `update()` lifecycle
- **Input**: Keyboard support with `get_key()` and `get_key_down()`
- **Precision**: 120Hz physics sub-stepping for stability

### Developer Experience
- **Fast Iteration**: Hot-reload scripts, instant play-testing
- **Clean UI**: Dark brutalist theme, no distractions
- **Standalone**: One executable, portable projects
- **Open Source**: Modify, extend, learn from the code

---

## Screenshots

*Coming soon - show editor, hub, and game examples*

---

## Documentation

- **[Getting Started Guide](GETTING_STARTED.md)** - Step-by-step first project tutorial
- **[API Reference](API_REFERENCE.md)** - Complete component and scripting docs
- **[Examples](samples/)** - Demo projects (coming soon)

---

## System Requirements

**Minimum:**
- Windows 10/11 (64-bit)
- 4GB RAM
- 500MB disk space

**Recommended:**
- Windows 11
- 8GB RAM
- Dedicated GPU for 60 FPS+

*Linux/Mac support planned for v1.1*

---

## Roadmap

**v1.0 Beta** (Current)
- Core editor and physics
- Project management system
- Single-file executable

**v1.1** (Planned)
- Audio system (music + SFX)
- Particle effects
- Tilemap support
- GameObject.find() / destroy()
- Runtime scene switching
- Linux/Mac builds

**v1.2+** (Future)
- Animation system
- Visual scripting
- Built-in asset store
- Multiplayer networking

See [ROADMAP.md](ROADMAP.md) for details.

---

## Community

- **Discord**: [Join the server](https://discord.gg/yourlink) (coming soon)
- **GitHub Issues**: [Report bugs](https://github.com/yourusername/aspis/issues)
- **itch.io**: [Download and rate](https://yourname.itch.io/aspis)
- **Twitter**: [@AspisEngine](https://twitter.com/aspisengine) (coming soon)

---

## Contributing

Aspis Engine is open source! Contributions welcome:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to your branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## Building from Source

```bash
# Clone repository
git clone https://github.com/yourusername/aspis.git
cd aspis

# Install dependencies
pip install -r requirements.txt

# Run editor
python main.py

# Build executable
pyinstaller aspis_onefile.spec
```

**Requirements:** Python 3.13+, pip

---

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## Credits

**Created by:** [Your Name]

**Built with:**
- [Python 3.13](https://www.python.org/)
- [PySide6](https://wiki.qt.io/Qt_for_Python) (Qt for Python)
- [Pygame](https://www.pygame.org/) (Rendering)
- [Pymunk](http://www.pymunk.org/) (Physics)
- [PyInstaller](https://www.pyinstaller.org/) (Packaging)

**Inspired by:** Unity, GameMaker, Godot, and the brutalist design movement.

---

## Star History

If you find Aspis Engine useful, consider starring the repo! ⭐

[![Star History](https://img.shields.io/github/stars/yourusername/aspis?style=social)](https://github.com/yourusername/aspis/stargazers)

---

**Ready to build your game?** [Download Aspis Engine](https://github.com/yourusername/aspis/releases/latest) and start creating! 🎮

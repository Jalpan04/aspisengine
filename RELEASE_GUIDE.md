# GitHub Release Guide - Aspis Engine v1.0 Beta

Quick reference for pushing code and creating your first release.

---

## Step 1: Push Code to GitHub

**Important:** Make sure you're in the project directory and have Git configured.

```bash
cd "d:/python projects/gameengine"

# Check if git is initialized
git status

# If not initialized, run:
# git init

# Check current remote
git remote -v

# If remote doesn't exist or is wrong, set it:
git remote remove origin  # Remove if exists
git remote add origin https://github.com/Jalpan04/aspis.git

# Stage all files
git add .

# Create .gitignore to exclude build files
echo "build/
dist/
*.pyc
__pycache__/
*.spec
*.ico
logo.png
.vscode/
.idea/" > .gitignore

# Stage .gitignore
git add .gitignore

# Commit
git commit -m "v1.0 Beta Release - Aspis Engine

Features:
- Visual editor with project hub
- Physics engine (120Hz sub-stepping)
- Python scripting API
- Component-based architecture
- Single-file executable (~200MB)
- Comprehensive documentation"

# Push to main branch
git push -u origin main

# If branch is different (e.g., master):
# git push -u origin master
```

**Note:** If you get authentication errors, you may need to authenticate with GitHub CLI or Personal Access Token.

---

## Step 2: Create GitHub Release

### Via GitHub Web Interface:

1. Go to: https://github.com/Jalpan04/aspis/releases
2. Click **"Create a new release"** or **"Draft a new release"**
3. Fill in the details:

**Tag version:** `v1.0-beta`

**Release title:** `Aspis Engine v1.0 Beta - First Public Release`

**Description:** (Copy this)

```markdown
# 🎮 Aspis Engine v1.0 Beta

The first public beta release of Aspis Engine - a brutalist Python-based 2D game engine designed for rapid prototyping and game jams.

![Logo](https://raw.githubusercontent.com/Jalpan04/aspis/main/logo.png)

## ✨ What's New

This is the **initial release** featuring:

### Editor
✅ **Project Hub** - Manage multiple game projects with search functionality  
✅ **Visual Scene Editor** - Drag-and-drop canvas with hierarchy and inspector  
✅ **Component System** - Transform, RigidBody, Colliders, Renderers, Scripts  
✅ **Asset Browser** - Import and manage project files  
✅ **Undo/Redo** - Full history for all editor actions  

### Runtime
✅ **Physics Engine** - Powered by Pymunk with 120Hz sub-stepping  
✅ **Python Scripting** - Simple API with start() and update() lifecycle  
✅ **Input System** - Keyboard support with get_key() and get_key_down()  
✅ **Rendering** - Sprite rendering, text, and layered drawing  

### Distribution
✅ **Single-File Executable** - ~200MB, no installation required  
✅ **Portable Projects** - Standard folder structure (assets, scenes, scripts)  
✅ **Custom Branding** - Professional dark theme with dull cyan accents  

## 📥 Download

### Windows (64-bit)
Download the executable below and double-click to launch. First run may take 5-10 seconds.

**File:** `AspisEngine-v1.0-beta-windows.exe` (~200MB)

## 📚 Documentation

- **[Getting Started Guide](https://github.com/Jalpan04/aspis/blob/main/GETTING_STARTED.md)** - Step-by-step tutorial for your first project
- **[API Reference](https://github.com/Jalpan04/aspis/blob/main/API_REFERENCE.md)** - Complete component and scripting documentation
- **[Distribution Guide](https://github.com/Jalpan04/aspis/blob/main/DISTRIBUTION.md)** - Instructions for sharing your games

## 💻 System Requirements

**Minimum:**
- Windows 10/11 (64-bit)
- 4GB RAM
- 500MB disk space

**Recommended:**
- Windows 11
- 8GB RAM
- Dedicated GPU for 60+ FPS

## ⚠️ Known Limitations (Beta)

This is a beta release. Known limitations:
- **Windows only** - Linux/Mac support coming in v1.1
- **No audio system** - Sound effects and music planned for v1.1
- **Scene switching** - Currently limited to editor only
- **GameObject lifecycle** - find() and destroy() not yet implemented

## 🐛 Report Issues

Found a bug or have a feature request?  
👉 [Open an issue on GitHub](https://github.com/Jalpan04/aspis/issues)

## 🚀 Quick Start

```
1. Download AspisEngine.exe
2. Double-click to launch
3. Click "NEW PROJECT"
4. Add Camera + Player + Ground
5. Click PLAY ▶ to test!
```

Full tutorial in the [Getting Started Guide](https://github.com/Jalpan04/aspis/blob/main/GETTING_STARTED.md).

## 🙏 Feedback Welcome!

This is the first public release. Your feedback helps improve Aspis Engine!

- Star the repo if you find it useful ⭐
- Share your projects on social media with #AspisEngine
- Join discussions in GitHub Issues

---

**Built with:** Python 3.13 • PySide6 • Pygame • Pymunk  
**License:** MIT  
**Version:** 1.0 Beta (Build 2026.01.12)
```

4. **Attach the executable:**
   - Click "Attach binaries by dropping them here or selecting them"
   - Upload: `d:/python projects/gameengine/dist/AspisEngine.exe`
   - Rename it to: `AspisEngine-v1.0-beta-windows.exe` during upload

5. **Options:**
   - ☑ Check "Set as a pre-release" (since it's beta)
   - ☐ Leave "Set as the latest release" unchecked initially

6. Click **"Publish release"**

Your release is now live at: https://github.com/Jalpan04/aspis/releases/tag/v1.0-beta

---

## Step 3: Verify Release

1. Visit https://github.com/Jalpan04/aspis/releases
2. Confirm the release appears
3. Test downloading the executable
4. Verify file size (~200MB) and it runs

---

## Troubleshooting

**"Authentication failed"**
- Use GitHub CLI: `gh auth login`
- Or create Personal Access Token: Settings → Developer Settings → Personal Access Tokens

**"Large file warning"**
- GitHub allows files up to 100MB in repos, but 2GB in releases
- AspisEngine.exe (~200MB) is fine for release attachments

**"Failed to push"**
- Check internet connection
- Verify remote URL: `git remote -v`
- Try: `git push --force origin main` (if safe)

---

**Next:** Post announcements on social media! See ANNOUNCEMENTS.md for templates.

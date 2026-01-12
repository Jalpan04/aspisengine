# Distribution Guide - Aspis Engine v1.0 Beta

Instructions for uploading Aspis Engine to GitHub Releases and itch.io.

---

## GitHub Release Setup

### Prerequisites
- GitHub account
- Repository created: `github.com/yourusername/aspis`
- Git installed locally

### Step 1: Push Code to GitHub

```bash
cd "d:/python projects/gameengine"

# Initialize git (if not already)
git init

# Add remote (replace with your username)
git remote add origin https://github.com/yourusername/aspis.git

# Add files
git add .

# Commit
git commit -m "v1.0 Beta Release - Initial Launch"

# Push to GitHub
git push -u origin main
```

### Step 2: Create a Release

1. Go to your repository on GitHub
2. Click **"Releases"** (right sidebar)
3. Click **"Create a new release"**

**Tag version:** `v1.0-beta`  
**Release title:** `Aspis Engine v1.0 Beta - First Release`

**Description:**
```markdown
# Aspis Engine v1.0 Beta

The first beta release of Aspis Engine - a brutalist Python-based 2D game engine.

## What's Included
- Visual editor with project hub
- Physics engine (gravity, collisions, rigid bodies)
- Python scripting system
- Sample scenes for testing

## Features
✅ Project management hub  
✅ Visual scene editor  
✅ Component-based architecture  
✅ Physics simulation (120Hz sub-stepping)  
✅ Python scripting API  
✅ Undo/Redo system  
✅ Single-file executable (~200MB)

## Download & Install
1. Download `AspisEngine.exe` below
2. Double-click to launch (first run takes 5-10 seconds)
3. Create a new project and start building!

## Documentation
- [Getting Started Guide](https://github.com/yourusername/aspis/blob/main/GETTING_STARTED.md)
- [API Reference](https://github.com/yourusername/aspis/blob/main/API_REFERENCE.md)

## System Requirements
- Windows 10/11 (64-bit)
- 4GB RAM minimum
- 500MB disk space

## Known Issues
- Linux/Mac not yet supported (coming in v1.1)
- No audio system yet
- Scene switching limited to editor only

## Feedback
Report bugs or request features: [GitHub Issues](https://github.com/yourusername/aspis/issues)
```

4. Click **"Attach binaries"** and drag:
   - `dist/AspisEngine.exe` (rename to `AspisEngine-v1.0-beta-windows.exe`)
   - `logo.png` (optional, for branding)

5. Check **"This is a pre-release"** (since it's beta)

6. Click **"Publish release"**

---

## itch.io Setup

### Step 1: Create itch.io Account
1. Go to [itch.io](https://itch.io)
2. Sign up or log in
3. Go to [Dashboard](https://itch.io/dashboard)

### Step 2: Create New Project

1. Click **"Create new project"**

**Metadata:**
- **Title:** Aspis Engine
- **Project URL:** `yourname.itch.io/aspis`
- **Classification:** Tool
- **Kind of project:** Downloadable
- **Pricing:** Free (or "Name your own price")

**Description:**
```
Aspis Engine is a brutalist 2D game engine built with Python. Perfect for game jams, rapid prototyping, and learning game development.

FEATURES:
• Visual editor with drag-and-drop scene building
• Physics engine with gravity, friction, and collisions
• Python scripting for gameplay logic
• Project hub to manage multiple games
• Single-file executable - no installation required

PERFECT FOR:
→ Game jams (quick iteration)
→ Prototyping ideas
→ Learning game development
→ Indie developers who love Python

DOWNLOAD & START:
1. Download AspisEngine.exe
2. Double-click to launch
3. Create your first project!

Documentation and tutorials included in the download.
```

**Cover Image:** Use your logo.png (resize to 630x500px recommended)

**Screenshots:** 
- Project Hub screenshot
- Editor with sample scene
- Game running (if you have examples)

**Tags:**
- game-engine
- game-development
- tool
- 2d
- python
- physics
- open-source
- brutalism

### Step 3: Upload Files

1. Scroll to **"Uploads"** section
2. Click **"Upload files"**
3. Drag `AspisEngine.exe`
4. **Display name:** "Aspis Engine v1.0 Beta (Windows)"
5. **Kind:** Executable
6. Check **"This file will be played in the browser"** → NO (it's downloadable)

### Step 4: Additional Files (Optional)

Upload as separate files:
- `GETTING_STARTED.pdf` (convert .md to PDF)
- `API_REFERENCE.pdf` (convert .md to PDF)
- `samples.zip` (if you create demo projects)

### Step 5: Community Settings

**Comments:** Enabled  
**Ratings:** Enabled  
**Devlog:** Optional (consider writing release notes)

### Step 6: Publish

1. Click **"Save & view page"**
2. Review your page
3. Click **"Edit game" → "Visibility & access"**
4. Set **Visibility:** Public
5. Click **"Save"**

Your game is now live! Share the link: `yourname.itch.io/aspis`

---

## Post-Launch Promotion

### Social Media Announcement Template

**Twitter/X:**
```
🎮 Aspis Engine v1.0 Beta is here!

A brutalist 2D game engine built with Python.
Perfect for game jams & rapid prototyping.

✨ Visual editor
⚙️ Physics engine  
🐍 Python scripting
📦 Single exe file

Download: [your link]

#gamedev #indiedev #python #gameengine
```

**Reddit (r/gamedev, r/python):**
```
Title: [Release] Aspis Engine v1.0 Beta - Python-based 2D Game Engine

I've been working on a lightweight 2D game engine called Aspis Engine, and I'm excited to share the first beta release!

**What is it?**
A brutalist game engine built with Python, featuring a visual editor, physics simulation, and a simple component system.

**Key Features:**
- Visual scene editor with hierarchy and inspector
- Physics engine (Pymunk-based)
- Python scripting API
- Project management hub
- Single-file executable (~200MB, no installation)

**Who is it for?**
Perfect for game jams, rapid prototyping, or anyone who loves Python and wants to make 2D games quickly.

**Download:** [GitHub / itch.io link]
**Documentation:** Included

I'd love feedback! This is a beta, so let me know what works and what doesn't.
```

### YouTube Video Ideas
1. "Aspis Engine - Quick Overview (2 minutes)"
2. "Making a simple game in Aspis Engine (10 minutes)"
3. "How I built a game engine with Python"

---

## Update Checklist

Before publishing:
- [ ] Test the executable on a clean Windows machine
- [ ] Verify all documentation links work
- [ ] Update GitHub username in all docs
- [ ] Add MIT license file
- [ ] Create CONTRIBUTING.md
- [ ] Test download size (should be ~200MB)
- [ ] Take screenshots for itch.io and GitHub
- [ ] Write release notes
- [ ] Plan post-launch announcements

---

## Support & Analytics

**GitHub:**
- Monitor Issues for bug reports
- Watch Stars for popularity tracking
- Check Releases download count

**itch.io:**
- Dashboard shows downloads, views, ratings
- Enable analytics for traffic sources
- Respond to comments

**Feedback Channels:**
- GitHub Issues (bugs/features)
- itch.io comments (general feedback)
- Discord (if you create one)

---

**Ready to launch?** Follow these steps and your engine is live! 🚀

Good luck with the release!

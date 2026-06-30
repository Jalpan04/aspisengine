# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['D:\\python projects\\gameengine\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('D:\\python projects\\gameengine\\runtime', 'runtime'), ('D:\\python projects\\gameengine\\shared', 'shared'), ('D:/python projects/gameengine/scenes\\config.json', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PySide6', 'tkinter', 'matplotlib', 'editor', 'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets', 'shiboken6'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='scenes',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\Users\\acer\\Desktop\\logo.ico'],
)

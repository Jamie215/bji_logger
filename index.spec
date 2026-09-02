# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for BJI Logger.
# Builds a native one-folder bundle on whatever OS PyInstaller runs on
# (Windows .exe / macOS .app). PyInstaller cannot cross-compile, so the
# GitHub Actions workflow runs this on both windows-latest and macos-latest.

import sys

block_cipher = None

# The app uses Flask-SocketIO with async_mode="gevent" and gevent
# monkey-patching. PyInstaller's static analysis misses the async driver
# and a few gevent/engineio pieces that are imported by name at runtime,
# so they must be declared explicitly or the frozen app crashes on launch.
hidden_imports = [
    "engineio.async_drivers.gevent",
    "engineio.async_drivers.gevent_uwsgi",
    "gevent",
    "geventwebsocket",
    "geventwebsocket.handler",
    "dns",
    "dns.resolver",
    "dash_bootstrap_components",
    "plotly",
    "pandas",
    "serial",
]

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets')],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Windows uses .ico; macOS expects .icns and ignores/errors on .ico, so
# only pass the icon on Windows.
exe_icon = 'BJI_Logger_icon.ico' if sys.platform == 'win32' else None

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='BJI_Logger',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=exe_icon,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='BJI_Logger',
)

# On macOS, wrap the collected output in a proper .app bundle so users get
# a double-clickable application rather than a bare Unix executable.
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='BJI_Logger.app',
        icon=None,
        bundle_identifier='ca.uwo.fhs.bji-logger',
    )

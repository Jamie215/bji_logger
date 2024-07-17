import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but some might need fine-tuning
build_exe_options = {
    "include_files": ["assets/"],
    "build_exe": "BJI_Logger",
    "packages": ['engineio','socketio','flask_socketio','threading']
}

# Base can be "Win32GUI" if you're building a GUI application on Windows
base = None
if sys.platform == "win32":
    base = "Win32GUI"

executables = [
    Executable(
        "index.py",
        base=base,
        icon="BJI_Logger_icon.ico"
    )
]

setup(
    name="BJI_Logger",
    version="2.6",
    description="BJI CORK Project Data Application",
    options={"build_exe": build_exe_options},
    executables=executables
)

# Contain Dash app and Flask Server
import os
import sys
from dash import Dash
import dash_bootstrap_components as dbc
from flask_socketio import SocketIO

# Resolve the assets folder relative to the app itself rather than the current
# working directory. When frozen with PyInstaller the app can be launched from
# anywhere (e.g. double-clicked), so os.getcwd() is not the app's location.
# PyInstaller unpacks bundled data (see datas in index.spec) under sys._MEIPASS.
if getattr(sys, "frozen", False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))
assets_path = os.path.join(base_path, "assets")

# Use external style sheets
external_stylesheets = [
    "https://fonts.googleapis.com/css?family=Roboto:300,400,500,700&display=swap",
    dbc.themes.LITERA,
    dbc.icons.FONT_AWESOME,
    "assets/style.css"
]

# Initialize the app
app = Dash(__name__, external_stylesheets=external_stylesheets, assets_folder=assets_path, suppress_callback_exceptions=True)
server = app.server
socketio = SocketIO(server, async_mode="gevent")
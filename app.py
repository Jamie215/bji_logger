"""
Import Libraries
"""
import atexit

import os
import signal

from dash import Dash
import dash_bootstrap_components as dbc

import arduino

# Use external style sheets
external_stylesheets = [
    "https://fonts.googleapis.com/css?family=Roboto:300,400,500,700&display=swap",
    dbc.themes.LITERA,
    "https://use.fontawesome.com/releases/v5.8.1/css/all.css",
    "assets/style.css"
]

# Initialize the app
app = Dash(__name__, external_stylesheets=external_stylesheets, assets_folder=os.getcwd()+'/assets/', suppress_callback_exceptions=True)
server = app.server

@server.route("/shutdown", methods=["POST"])
def shutdown():
    """
    Shut down the process when the user exists from the browser
    """
    print("Server shutting down...")
    os.kill(os.getpid(), signal.SIGINT)
    return "Server shutting down..."

def clean_up():
    """
    Clean up existing resources
    """
    print("Cleaning up")
    if hasattr(arduino, "arduino_serial"):
        arduino.disconnect_arduino()
        print("Arduino serial connection closed")

atexit.register(clean_up)

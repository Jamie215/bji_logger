"""
Import Libraries
"""
import atexit
import os
import logging
import json

from dash import Dash
import dash_bootstrap_components as dbc
from flask import request, jsonify
from flask_socketio import SocketIO

import arduino

# Use external style sheets
external_stylesheets = [
    "https://fonts.googleapis.com/css?family=Roboto:300,400,500,700&display=swap",
    dbc.themes.LITERA,
    "https://use.fontawesome.com/releases/v5.8.1/css/all.css",
    "assets/style.css"
]

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# Initialize the app
app = Dash(__name__, external_stylesheets=external_stylesheets, assets_folder=os.getcwd()+'/assets/', suppress_callback_exceptions=True)
server = app.server
socketio = SocketIO(server)

@server.route("/log", methods=["POST"])
def log():
    data = request.get_json()
    logging.info(f"Client log: {data['message']}")
    return jsonify(success=True)

@server.route("/emit_event", methods=["POST"])
def emit_event():
    if request.content_type == 'text/plain;charset=UTF-8':
        data = request.get_data(as_text=True)
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            return "Invalid JSON", 400
    else:
        data = request.get_json()

    event = data.get("event")
    if event == "page_refreshed":
        socketio.emit("page_refreshed")
        logging.info("Emitting page_refreshed event from beacon")
    elif event == "window_closed":
        socketio.emit("window_closed")
        logging.info("Emitting window_closed event from beacon")
        os._exit(0)
    return jsonify(success=True)

@server.route("/shutdown", methods=["POST"])
def shutdown():
    """
    Shut down the process when the user exists from the browser
    """
    logging.info("Shutdown request received")
    print("Server shutting down...")
    func = request.environ.get('werkzeug.server.shutdown')
    if func:
        func()
    return "Server shutting down..."

@socketio.on("connect")
def handle_connect():
    logging.info("Client connected")

@socketio.on("disconnect")
def handle_disconnect():
    logging.info("Client disconnected")

def clean_up():
    """
    Clean up existing resources
    """
    print("Cleaning up")
    if hasattr(arduino, "arduino_serial"):
        arduino.disconnect_arduino()
        print("Arduino serial connection closed")

atexit.register(clean_up)

if __name__ == "__main__":
    socketio.run(server, port=8050)

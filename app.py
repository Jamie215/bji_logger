"""
Import Libraries
"""
import atexit
import os
import logging
from threading import Timer

from dash import Dash
import dash_bootstrap_components as dbc
from flask import request, jsonify, render_template_string
from flask_socketio import SocketIO
from engineio.async_drivers import gevent

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
socketio = SocketIO(server, async_mode="gevent")

heartbeat_timeout = None

def reset_heartbeat_timer():
    """
    Reset the heartbeat timer
    """
    global heartbeat_timeout
    if heartbeat_timeout:
        heartbeat_timeout.cancel()
    # Set the heartbeat timer to 300 seconds (5 min)
    heartbeat_timeout = Timer(300, notify_server_timeout)
    heartbeat_timeout.start()

def notify_server_timeout():
    """
    Prepare to shut down as no heartbeat received
    """
    logging.info("No heartbeat received. Preparing to shut down server.")
    socketio.emit("server_shutdown_warning")
    # Give 10 seconds for the client to handle the warning
    Timer(10, shutdown_server).start()

def shutdown_server():
    """
    Shut down the server when the user exists from the browser based on heartbeat timer
    """
    logging.info("No heartbeat received; shutting down server.")
    os._exit(0)

@server.route("/heartbeat", methods=["POST"])
def heartbeat():
    """
    Receive heartbeat to determine the interface is still active
    """
    logging.info("Received heartbeat")
    reset_heartbeat_timer()
    return "", 204

@server.route("/timeout")
def timeout():
    """
    Navigate to timeout page
    """
    print("Session has timed out")
    return render_template_string("""
            <html>
                <head><title>Server Terminated</title></head>
                <body>
                    <<h1>BJI IMU Application Terminated</h1>
                    <p> The server has terminated due to inactivity. Please close this tab and relaunch the application.</p>
                </body>
            </html>
        """)

@server.route("/log", methods=["POST"])
def log():
    """
    For logging purposes
    """
    data = request.get_json()
    logging.info(f"Client log: {data['message']}")
    return jsonify(success=True)

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
    reset_heartbeat_timer()
    socketio.run(server, port=8050, allow_unsafe_werkzeug=True)

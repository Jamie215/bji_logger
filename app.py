from dash import Dash
import dash_bootstrap_components as dbc

# Use external style sheets
external_stylesheets = [
    'https://fonts.googleapis.com/css?family=Roboto:300,400,500,700&display=swap',
    dbc.themes.LITERA,
    'https://use.fontawesome.com/releases/v5.8.1/css/all.css',
    '/assets/style.css'
]

# Initialize the Dash app
app = Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
server = app.server


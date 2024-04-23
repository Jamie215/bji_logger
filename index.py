from dash import dcc, html, Input, Output, State, callback_context
import dash
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import webbrowser
from threading import Timer
import datetime
import pytz
import os
import json

# Import local files
from app import app
from data_analysis_page import layout as data_analysis_layout
import arduino

# Store modal's history for "previous" navigation
modal_history = []

# Set modal content for body and footer
def set_modal_content(initialize=False, selected_dt=None, download=False, not_connected=False, error=None, footer_view="None"):

    # Generate modal body content
    status_msg = []
    if initialize:
        status_msg = [
                        html.Div("Please set the date and time for device initialization.", className="mb-2"),
                        dbc.Button("Close", id='close-modal', style={"display":"None"}),
                    ]
    elif not_connected:
        status_msg = [
                        html.Div("Arduino not found! Check the Arduino connection and try again.", className="mb-2"),
                        html.Div(
                                        [
                                            dbc.Button("Re-Initialize", id="re-initialize-btn", className='initialize-button'),
                                            dbc.Button("Close", id="close-modal", outline=True, color="secondary", style={'margin-left': '10px'}),
                                        ],
                                        style={'text-align':'center'})
                    ]
    elif selected_dt:
        status_msg = [
                        html.I(className="fas fa-check-circle initiate-success"),
                        dbc.Row(html.Div(["The device has been initialized for ",
                                          html.Span(selected_dt, style={'color': 'CornFlowerBlue', 'font-weight':'bold'}),
                                          " and powered down. It will be counting steps in the next powerup. Please disconnect the device."
                                          ])),
                        html.Div(
                                    [
                                        dbc.Button("Re-Initialize", id="re-initialize-btn", outline=True, color="secondary"),
                                        dbc.Button("Close", id="close-modal", className="initialize-button", style={'margin-left': '10px'}),
                                    ],
                                    style={'text-align':'center'}
                        )
                    ]
    elif download:
        status_msg = [
                        html.Div("Select from below for downloading appropriate format.", className="mb-2"),
                        dbc.Button("Close", id='close-modal', style={"display":"None"})
                    ]
    elif error:
        status_msg = [
                        html.I(className="fas fa-times-circle initiate-fail"),
                        dbc.Row(html.Div(["The initialization has failed due to the following error: ",
                                          html.Span(error, style={'color':'Coral', 'font-weight':'bold'}),
                                          " If you want to continue initializing the device, click the Re-Initiate button."
                                        ])),
                        html.Div(
                                        [
                                            dbc.Button("Re-Initialize", id="re-initialize-btn", className='initialize-button'),
                                            dbc.Button("Close", id="close-modal", outline=True, color="secondary", style={'margin-left': '10px'}),
                                        ],
                                        style={'text-align':'center'})
                        
                    ]
    else:
        status_msg = [html.Div("Please connect Arduino to computer.", className="mb-2"),
                      dbc.Button("Close", id='close-modal', style={"display":"None"})]

    curr_date = datetime.datetime.now()


    initialize_view = [
                        dbc.Row([
                            dbc.Col(
                                html.Div([
                                    html.Label("Date", 
                                               className="dropdown-label",
                                               style={'display':'none'} if not initialize else {}),
                                    dcc.DatePickerSingle(
                                        id='date-picker',
                                        min_date_allowed=curr_date.date(),
                                        max_date_allowed=curr_date.date() + datetime.timedelta(days=60),
                                        initial_visible_month=curr_date.date(),
                                        date=curr_date.date(),
                                        style={'display': 'none'} if not initialize else {}
                                    ),
                                ]), 
                                width=6,
                            ),
                            dbc.Col(
                                html.Div([
                                    html.Label("Hour (24)",
                                               className="dropdown-label",
                                               style={'display': 'none'} if not initialize else {}),
                                    dcc.Dropdown(
                                        id='hour',
                                        options=[{'label': f'{i:02d}', 'value': i} for i in range(24)],
                                        value=curr_date.hour,
                                        style={'display': 'none'} if not initialize else {'width': '100px', 'display': 'inline-block'}
                                    )
                                ]), 
                                width=3,
                            ),
                            dbc.Col(
                                html.Div([
                                    html.Label("Minute",
                                               className="dropdown-label",
                                               style={'display': 'none'} if not initialize else {}),
                                    dcc.Dropdown(
                                        id='minute',
                                        options=[{'label': f'{i:02d}', 'value': i} for i in range(60)],
                                        value=curr_date.minute,
                                        style={'display': 'none'} if not initialize else {'width': '100px', 'display': 'inline-block'}
                                    )
                                ]),                                     
                                width=3,
                            )
                        ])
                    ]
    
    download_view = [
                        html.Div([
                                    dbc.Button("Download .RAW Data", 
                                            id="download-raw", 
                                            className="ms-2 download-button",
                                            style={'display': 'none'} if not download else {}),
                                    dbc.Button("Download .CSV Data", 
                                            id="download-read", 
                                            className="ms-2 download-button",
                                            style={'display': 'none'} if not download else {}),
                                ], className="flex-container"),
                        dcc.Download(id="download-data"),
                    ]
    
    # Generate modal footer content
    if footer_view == "None":
        if not_connected:
            modal_footer = dbc.ModalFooter(
                            dbc.Row([
                                dbc.Col(
                                    html.I(className="fas fa-exclamation-circle disclaimer-msg"),
                                    width=1,
                                    align='top'
                                ),
                                dbc.Col(
                                    html.Div("Exiting this pop-up will terminate the Arduino connection process!", className="disclaimer-msg"),
                                    width=11,
                                    align='center'
                                ),
                                dbc.Col([
                                    dbc.Button("Previous", id="previous-modal", style={'display':'none'}),
                                    dbc.Button("Connect", id="connect-modal", style={'display':'none'}),
                                    dbc.Button("Initialize", id="initialize-btn", style={'display':'none'}),
                                    dbc.Button("Re-Initialize", id="re-initialize-btn", style={'display':'none'})
                                ], 
                                width=0,
                                align='center')
                            ])
                        )
        else:

            modal_footer = dbc.ModalFooter([
                                dbc.Button("Previous", id="previous-modal", style={'display':'none'}),
                                dbc.Button("Connect", id="connect-modal", style={'display':'none'}),
                                dbc.Button("Initialize", id="initialize-btn", style={'display':'none'}),
                                dbc.Button("Re-Initialize", id="re-initialize-btn", style={'display':'none'})
                            ], style={'height':'0px'})

    elif footer_view == "Modal Start":
        modal_footer = dbc.ModalFooter(
                            dbc.Row([
                                dbc.Col(
                                    html.I(className="fas fa-exclamation-circle disclaimer-msg"),
                                    width=1,
                                    align='top'
                                ),
                                dbc.Col(
                                    html.Div("Exiting this pop-up will terminate the Arduino connection process!", className="disclaimer-msg"),
                                    width=8,
                                    align='center'
                                ),
                                dbc.Col([
                                    dbc.Button("Previous", id="previous-modal", style={'display':'none'}),
                                    dbc.Button("Connect", id="connect-modal", color='success', className="ms-auto"),
                                    dbc.Button("Initialize", id="initialize-btn", style={'display':'none'}),
                                    dbc.Button("Re-Initialize", id="re-initialize-btn", style={'display':'none'})
                                ], 
                                width=3,
                                align='center')
                            ])
                        )
    elif footer_view == "Initialize":
        modal_footer = dbc.ModalFooter(
                            dbc.Row([
                                dbc.Col(
                                    html.I(className="fas fa-exclamation-circle disclaimer-msg"),
                                    width=1,
                                    align='center'
                                ),
                                dbc.Col(
                                    html.Div("Exiting this pop-up will terminate the Arduino connection process!", className="disclaimer-msg"),
                                    width=5,
                                    align='center',
                                ),
                                dbc.Col([
                                    dbc.Button("Previous", id="previous-modal", outline=True, color="secondary", style={'margin-left': '10px', 'margin-right': '10px'}),
                                    dbc.Button("Connect", id="connect-modal", style={'display':'none'}),
                                    dbc.Button("Initialize", id="initialize-btn", className="initialize-button"),
                                    dbc.Button("Re-Initialize", id="re-initialize-btn", style={'display':'none'})
                                ],
                                width=6,
                                align='center')
                            ]), 
                            style={'height': '90px'}
                        )        

    return  [
                dbc.ModalBody(status_msg + initialize_view + download_view, id='modal-body'),
                modal_footer
            ]

# Declare Index page layout
def index_layout():
    return html.Div([
                        dbc.Button(
                            "Initialize Device",
                            id='open-initialize-modal',
                            color='primary',
                            outline=True,
                            className='m-2 page-button',
                        ),
                        dbc.Button(
                            "Data Download",
                            id='open-download-modal',
                            color='primary',
                            outline=True,
                            className='m-2 page-button',
                        ),
                        dbc.Button(
                            "Data Analysis",
                            href='/data-analysis',
                            color='primary',
                            outline=True,
                            className='m-2 page-button',
                        ),
                        dbc.Modal(
                                    [dbc.ModalHeader("Action")] + set_modal_content(),
                                    id="action-modal", 
                                    centered=True, 
                                    is_open=False
                    )],
                    style={'height': '80vh'},
                    className='flex-container')

app.layout = html.Div([
                        dcc.Location(id='url', refresh=False),
                        dbc.NavbarSimple(
                                brand="CORK DATA APPLICATION",
                                color='cornflowerblue',
                                dark=True,
                                fluid=True,
                        ),
                        dcc.Store(id='action-modal-open-state', data=json.dumps({'is_open': False})),
                        html.Div(id="action-modal-status"),
                        html.Div(id='page-content')
                    ])

@app.callback(
        [Output("action-modal", 'is_open'),
         Output("action-modal", 'children'),
         Output("action-modal-open-state", 'data')],
        [Input('open-initialize-modal', 'n_clicks'),
         Input('re-initialize-btn', 'n_clicks'),
         Input('open-download-modal', 'n_clicks'),
         Input('previous-modal', 'n_clicks'),
         Input('connect-modal', 'n_clicks'),
         Input('initialize-btn', 'n_clicks'),
         Input('close-modal', 'n_clicks'), 
        ],
        [State('action-modal', 'is_open'),
          State("action-modal", "children"),
          State("action-modal-open-state", 'data'),
          State('date-picker', 'date'),
          State('hour', 'value'),
          State('minute', 'value')],
          prevent_initial_call=True)
def toggle_action_modal(init_click, re_init_click, dl_click, previous_click, connect_click, init_btn_click, close_click, is_open, curr_children, json_data, date, hour, minute):
    ctx = callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Action Type 1: "Initialize" button triggered from the index page
    if any([x is not None for x in [init_click, re_init_click, dl_click, previous_click, connect_click, init_btn_click, close_click]]):
        if triggered_id in ['open-initialize-modal','re-initialize-btn']:
            modal_content = [dbc.ModalHeader("Initialize Arduino", className="modal-header-text")] + set_modal_content(footer_view="Modal Start")
            return True, modal_content, json.dumps({'is_open': True})
        
        # Action Type 2: "Download" button triggered from the index page
        elif triggered_id == "open-download-modal":
            modal_content = [dbc.ModalHeader("Download Data", className="modal-header-text")] + set_modal_content(footer_view="Modal Start")
            return True, modal_content, json.dumps({'is_open': True})
        
        # Action Type 3: "Previous" button triggered from the modal
        elif triggered_id == "previous-modal":
            # Disconnect the serial connection if one exists
            if arduino.arduino_serial:
                arduino.disconnect_arduino()

            # Render previous modal content in DOM
            prev_content = modal_history.pop()
            return True, prev_content, json.dumps({'is_open': True})
        
        # Action Type 4: "Connect" button triggered from the modal
        elif triggered_id == "connect-modal":
            # Update the past modal content as we prepare new modal view
            modal_history.append(curr_children)
            arduino_status = arduino.get_device_status()
            if arduino_status:
                if "Error" in str(arduino_status):
                    updated_children = [curr_children[0]] + set_modal_content(error=arduino_status)
                    return True, updated_children, json.dumps({'is_open': True})
            if arduino.arduino_serial:
                # Action Type 4-1: The "Connect" button was for "Initialization"
                if "Initialize Arduino" in str(curr_children):
                    if arduino_status == b"FIRST_POWERON" or arduino_status == b"DATA_FILE_EXISTS":
                        updated_children = [curr_children[0]] + set_modal_content(initialize=True, footer_view="Initialize")
                        return True, updated_children, json.dumps({'is_open': True})
                # Action Type 4-2: The "Connect" button was for "Download"
                elif "Download Data" in str(curr_children):
                    if arduino_status == b"FIRST_POWERON":
                        updated_children = [
                                                curr_children[0],
                                                dbc.ModalBody("First time initiating the device! No data available"),
                                                curr_children[2]
                                            ]
                        return True, updated_children, json.dumps({'is_open': True})
                    elif arduino_status == b"DATA_FILE_EXISTS":
                        updated_children = [curr_children[0]] + set_modal_content(download=True)
                        return True, updated_children, json.dumps({'is_open': True})
            # Action Type 4-3: Arduino serial connection is not made
            else:
                updated_children = [curr_children[0]] + set_modal_content(not_connected=True)
                return True, updated_children, json.dumps({'is_open': True})
            
        # Action Type 5: "Initialize" button triggered from the button    
        elif triggered_id == "initialize-btn":
            # Update the past modal content as we prepare new modal view
            modal_history.append(curr_children)

            # Convert selected date and time to epoch time
            selected_datetime = datetime.datetime.strptime(date, '%Y-%m-%d')
            selected_datetime = selected_datetime.replace(hour=int(hour), minute=int(minute))
            
            timezone = pytz.timezone("UTC")

            selected_datetime = timezone.localize(selected_datetime)
            epoch_time = int(selected_datetime.astimezone(pytz.utc).timestamp())

            # Send initialization command to Arduino
            arduino_error = arduino.initialize_arduino(epoch_time)
            if not arduino_error:
                formatted_dt = selected_datetime.strftime('%A, %B %d at %I:%M %p')
                updated_children = [curr_children[0]] + set_modal_content(selected_dt=formatted_dt)
                return True, updated_children, json.dumps({'is_open': True})
            else:
                updated_children = [curr_children[0]] + set_modal_content(error=arduino_status)
                return True, updated_children, json.dumps({'is_open': True})
        
        elif triggered_id == "close-modal":
            return False, dash.no_update, json.dumps({'is_open': False})

    return is_open, dash.no_update, json_data

@app.callback(
        Output("download-data", "data"),
        [Input("download-raw", "n_clicks"),
         Input("download-read", "n_clicks")],
         prevent_initial_call=True)
def download_data(raw_click, read_click):
    ctx = callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    USER_FILES_DIR = os.getcwd()

    if triggered_id == "download-raw":
        file_name = "IMUDATA_Raw.raw"
        file_path = os.path.join(USER_FILES_DIR, file_name)
        arduino.download_file(file_path)
        return dcc.send_bytes(lambda buffer: buffer.write(open(file_path, 'rb').read()), file_name)
    elif triggered_id == "download-read":
        file_name = "IMUData_Readable.csv"
        file_path = os.path.join(USER_FILES_DIR, file_name)
        arduino.download_file(file_path, True)
        return dcc.send_bytes(lambda buffer: buffer.write(open(file_path, 'rb').read()), file_name)
    raise PreventUpdate

@app.callback(
        Output("action-modal-status", 'children'),
        Input("action-modal-open-state", 'data'),
        prevent_initial_call=True
)
def manage_arduino_connection(json_data):
    data = json.loads(json_data)
    if data and not data['is_open']:
        arduino.disconnect_arduino()
        print("Arduino serial connection disconnected")
        return None
    raise PreventUpdate
     
@app.callback(Output('page-content', 'children'),
              [Input('url','pathname')])
def display_page(pathname):
    if pathname == '/data-analysis':
        return data_analysis_layout
    else:
        return index_layout()

def open_browser():
    webbrowser.open_new("http://127.0.0.1:8050/")

# Main
if __name__ == '__main__':
    Timer(1, open_browser).start()
    app.run_server(debug=False)
"""
Import Libraries
"""
import base64
import io
import os
from datetime import datetime, timedelta

from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px

from app_instance import app

# Define the layout of the app
data_analysis_layout = html.Div([
    dbc.Container(
        [
            # Act as a global variable for the data used for plotting
            html.Div(id="read-data", style={"display":"none"}),
            dcc.Store(id="raw-data"),
            dcc.Store(id="selected-data"),
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Upload(
                            id="upload-data",
                            children= html.Div(
                                [
                                    html.I(className="fas fa-upload"),
                                    " Drag and Drop",
                                    html.Br(),
                                    "or",
                                    html.Br(),
                                    html.A("Select CSV File to View Data")
                                ],
                                className="upload-text"
                            ),
                            multiple=False,
                            className="upload-box"
                        ),
                        width=8,
                    ),
                    dbc.Col(
                        html.Div(id="content-patientinfo", className="content-patientinfo"),
                        width=4,
                    )
                ],
                className="row flex-container",
                style={"margin-bottom": "15px"}
            ),
            dbc.Row(
                dbc.Col(
                    html.Div(
                        [
                            dbc.Button(
                                [html.I(className="fas fa-file-pdf"), " Download Page (PDF)"],
                                id="download-pdf-btn",
                                color="primary",
                                outline=True,
                                className="me-2",
                                disabled=True,
                            ),
                            dbc.Button(
                                [html.I(className="fas fa-file-csv"), " Download Values (CSV)"],
                                id="download-values-btn",
                                color="primary",
                                outline=True,
                                disabled=True,
                            ),
                            dcc.Download(id="download-values-csv"),
                            html.Div(id="pdf-print-dummy", style={"display": "none"}),
                        ],
                        className="export-bar",
                        style={"text-align": "right"},
                    ),
                    width=12,
                ),
                className="row",
                style={"margin-bottom": "10px"},
            ),
            dbc.Row(
                dbc.Col(
                    [
                        html.H4("Total Collected Period", className="color-main"),
                        html.Div(id="content-collected-period"),
                        html.H6("Select Time Range", className="color-sub"),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Label("Date Range:"),
                                        html.Br(),
                                        dcc.DatePickerRange(
                                            id="date-picker-range",
                                            display_format="YYYY-MM-DD"
                                        )
                                    ],
                                    width=5
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Start Hour:"),
                                        dcc.Dropdown(id="start-hour-dropdown", clearable=False)
                                    ],
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Start Minute:"),
                                        dcc.Dropdown(id="start-minute-dropdown", clearable=False)
                                    ],
                                ),
                                dbc.Col(),
                                dbc.Col(
                                    [
                                        html.Label("End Hour:"),
                                        dcc.Dropdown(id="end-hour-dropdown", clearable=False)
                                    ],
                                ),
                                dbc.Col(
                                    [
                                        html.Label("End Minute:"),
                                        dcc.Dropdown(id="end-minute-dropdown", clearable=False)
                                    ],
                                ),
                                dbc.Col(
                                    [
                                        dbc.Button("Download", id="download-csv-btn"),
                                        dcc.Download(id="download-df-csv"),
                                        dcc.Loading(
                                            id="loading-download",
                                            type="circle",
                                            children=[
                                                html.Div(id="download-status")
                                            ]
                                        ),
                                    ],
                                )
                            ],
                            className="flex-container",
                        ),                      
                        html.Br(),
                        html.H6("Set Active Steps:", className="color-sub", style={"margin-top":"5px"}),
                        dcc.Slider(1, 100,
                            step=None,
                            marks={
                                1: "1",
                                10: "10",
                                20: "20",
                                30: "30",
                                40: "40",
                                50: "50",
                                60: "60",
                                70: "70",
                                80: "80",
                                90: "90",
                                100: "100"
                            },
                            value=1,
                            id="active-step-slider",
                            className="active-step-slider"
                        ),
                    ],
                    width=12,
                    style={"text-align":"left"}
                ),
                className="row",
                style={"margin-bottom": "10px"}
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H4("Total Steps", className="color-main", style={"text-align":"left"}),
                            html.Div(id="content-total-steps", className="color-sub", style={"text-align":"left"}),
                            html.H4("Active Steps", className="color-main", style={"margin-top":"5px","text-align":"left"}),
                            html.Div(id="content-active-steps", className="content-totalinfo")
                        ],
                        width=5,
                        className="white-background-2",
                    ),
                    dbc.Col(
                        [
                            html.H4("Total Minutes", className="color-main", style={"text-align":"left"}),
                            html.Div(id="content-total-minutes", className="color-sub", style={"text-align":"left"}),
                            html.H4("Active Minutes", className="color-main", style={"margin-top":"5px", "text-align":"left"}),
                            html.Div(id="content-active-minutes", className="content-totalinfo")
                        ],
                        width=5,
                        className="white-background-2",
                    )
                ],
                className="row flex-container",
                style={"margin-bottom":"10px", "justify-content":"space-around", "overflow": "hidden"}
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H4("Step Counts Over Time", className="color-main"),
                            dbc.Tabs(
                                id="graph-tab-scatter",
                                children=[
                                    dbc.Tab(label="Original - Every 5 Min", tab_id= "scatter-raw"),
                                    dbc.Tab(label="Hourly Aggregated", tab_id= "scatter-hourly"),
                                    dbc.Tab(label="Daily Aggregated", tab_id= "scatter-daily")
                                ],
                                active_tab="scatter-raw",
                            ),
                            html.Div(id="tab-content-scatter", className="graph-section")
                        ],
                        width=12
                    )
                ],
                className="row",
                style={"margin-bottom": "10px"}
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H4("Weekly Breakdown", className="color-main"),
                            html.Div(id="content-sunburst", className="white-background-2")
                        ],
                        width=4,
                    ),
                    dbc.Col(
                        [
                            html.H4("Step Count Distribution", className="color-main"),
                            dbc.Tabs(
                                id="graph-tab-boxwhisker",
                                children=[
                                    dbc.Tab(label="Throughout the Day (Over Hours)", tab_id="boxwhisker-hourly"),
                                    dbc.Tab(label="Throughout the Week (Over Days)", tab_id="boxwhisker-daily"),
                                    dbc.Tab(label="Throughout the Collected Period (Over Each Week of Months)", tab_id="boxwhisker-monthly")
                                ],
                                active_tab="boxwhisker-hourly",
                            ),
                            html.Div(id="tab-content-boxwhisker", className="graph-section")
                        ],
                        width=8
                    )
                ],
                className="row"
            ),
            dbc.Row(
                dbc.Col(
                    [
                        html.H4("Comments", className="color-main"),
                        dcc.Textarea(
                            id="comment-box",
                            placeholder="Enter any notes or observations about this participant's data...",
                            className="comment-box",
                            style={"width": "100%", "height": "120px"},
                        ),
                    ],
                    width=12,
                ),
                className="row",
                style={"margin-top": "10px", "margin-bottom": "10px"},
            )
        ],
        fluid=True,
        style={"padding": "40px"}
    )
])

# Create/Read the data for entire dashboard
@app.callback(
        Output("raw-data", "data"),
        Output("date-picker-range", "start_date"),
        Output("date-picker-range", "end_date"),
        Output("start-hour-dropdown", "value"),
        Output("start-minute-dropdown", "value"),
        Output("end-hour-dropdown", "value"),
        Output("end-minute-dropdown", "value"),
        [Input("upload-data", "contents")],
        [State("upload-data", "filename")]
)
def read_data(contents, filename):
    """
    Read the CSV file that was generated from the application

    contents: data of interest
    filename: name of the csv file
    """
    if contents is None:
        # Create dummy data (For demo purposes)
        # df = pd.DataFrame(
        #     {"timestamp": np.arange(datetime(2024,2,1,0,0,0), datetime(2024,5,30,23,59,0), timedelta(minutes=5))}
        # )

        # x = np.arange(0,df.size)
        # def f(x):
        #     tmp = np.sin(0.01*x) + np.random.normal(size=len(x))*25
        #     tmp[tmp<0] = 0
        #     return tmp.round()
        # df["steps"] = f(x)
        return None, None, None, None, None, None, None
    else:
        _, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)
        if "csv" in filename:
            df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
            if df.columns[0] == "timestamp" and df.columns[1] == "steps":
                pass  # CSV has header row
            else:
                df = pd.read_csv(io.StringIO(decoded.decode("utf-8")), names=["timestamp", "steps"])
        else:
            return None, None, None, None, None, None, None

        df["timestamp"] = pd.to_datetime(df["timestamp"])
    
    if df.empty: return None, None, None, None, None, None, None

    start_date = df["timestamp"].min().strftime("%Y-%m-%d")
    end_date = df["timestamp"].max().strftime("%Y-%m-%d")

    start_hour = df["timestamp"].min().strftime("%H")
    start_min = df["timestamp"].min().strftime("%M")
    end_hour = df["timestamp"].max().strftime("%H")
    end_min = df["timestamp"].max().strftime("%M")

    return (df.to_json(date_format="iso", orient="split"), start_date, end_date, 
            start_hour, start_min, end_hour, end_min)

@app.callback(
    Output("start-hour-dropdown", "options"),
    Output("end-hour-dropdown", "options"),
    [Input("date-picker-range", "start_date"),
     Input("date-picker-range", "end_date")]
)
def update_hour_options(start_hour, end_hour):
    """
    Callback for the hour option of the date parsing feature

    start_hour: hour of start datetime
    end_date: hour of end datetime
    """
    hours = [{"label": str(hour).zfill(2), "value": str(hour).zfill(2)} for hour in range(24)]
    return hours, hours

@app.callback(
    Output("start-minute-dropdown", "options"),
    Output("end-minute-dropdown", "options"),
    [Input("date-picker-range", "start_date"),
     Input("date-picker-range", "end_date")]
)
def update_minute_options(start_min, end_min):
    """
    Callback for the minute option of the date parsing feature
    
    start_min: minute of start datetime
    end_min: minute of end datetime
    """
    minutes = [{"label": str(minute).zfill(2), "value": str(minute).zfill(2)} for minute in range(0, 60, 5)]
    return minutes, minutes

@app.callback(
    Output("selected-data", "data"),
    [Input("date-picker-range", "start_date"),
     Input("date-picker-range", "end_date"),
     Input("start-hour-dropdown", "value"),
     Input("start-minute-dropdown", "value"),
     Input("end-hour-dropdown", "value"),
     Input("end-minute-dropdown", "value")],
    [State("raw-data", "data")]
)
def update_selected_data(start_date, end_date, start_hour, start_minute, end_hour, end_minute, raw_data):
    """
    Parse the data based on the provided datetime range

    start_date: selected start date for the data
    end_date: selected end date for the data
    start_hour: selected start hour for the data
    start_minute: selected start minute for the data
    end_hour: selected end hour for the data
    end_minute: selected end minute for the data
    raw_data: full raw json input
    """
    if raw_data is None:
        return None

    df = pd.read_json(io.StringIO(raw_data), orient="split")

    try:
        start_dt = f"{start_date} {start_hour}:{start_minute}:00"
        end_dt = f"{end_date} {end_hour}:{end_minute}:59"
        start_dt = datetime.strptime(start_dt, "%Y-%m-%d %H:%M:%S")
        end_dt = datetime.strptime(end_dt, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        selected_df = df
    else:
        selected_df = df.loc[(df["timestamp"] >= start_dt) & (df["timestamp"] <= end_dt)]

    return selected_df.to_json(date_format="iso", orient="split")

@app.callback(
        Output("download-csv-btn", "disabled"),
        Input("upload-data", "contents")
)
def toggle_download_button(upload_data):
    """
    Enable download button only when upload data is available

    upload_data: data uploaded to the interface
    """
    if upload_data is None: return True

    return False

@app.callback(
    Output("download-df-csv", "data"),
    Output("download-status", "children"),
    [Input("upload-data", "filename"),
     Input("download-csv-btn", "n_clicks")],
    State("selected-data", "data"),
    prevent_initial_call=True
)
def download_csv(filename, n_clicks, selected_data):
    """
    Download the parsed data as a csv

    filename: original filename
    n_clicks: click instance of download-csv-btn
    selected_data: parsed data
    """
    if selected_data is None: return None, None

    if filename and n_clicks:
        try:
            df = pd.read_json(io.StringIO(selected_data), orient="split")
            file_status = html.Div("Complete", style={"color": "mediumseagreen", "margin-left": "15px"})
            base_uid = filename.split("_")[0]
        except Exception as e:
            print(f"Following exception triggered: {e}")
            return None, html.Div("Error", style={"color": "indianred", "margin-left": "15px"})
        else:
            file_name = f"{base_uid}_parsed_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
            # Browser download only — the user chooses where it lands.
            return (
                dcc.send_data_frame(df.to_csv, file_name, index=False, header=False),
                file_status
            )
    return None, None

# Enable the export buttons only when data has been uploaded
@app.callback(
    Output("download-pdf-btn", "disabled"),
    Output("download-values-btn", "disabled"),
    Input("upload-data", "contents")
)
def toggle_export_buttons(upload_data):
    """
    Enable the PDF and values-CSV download buttons only when data is uploaded

    upload_data: data uploaded to the interface
    """
    if upload_data is None:
        return True, True

    return False, False

# Trigger the browser's print dialog so the whole page can be saved as a PDF
app.clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks) {
            window.print();
        }
        return "";
    }
    """,
    Output("pdf-print-dummy", "children"),
    Input("download-pdf-btn", "n_clicks"),
    prevent_initial_call=True
)

@app.callback(
    Output("download-values-csv", "data"),
    Input("download-values-btn", "n_clicks"),
    [State("selected-data", "data"),
     State("raw-data", "data"),
     State("active-step-slider", "value"),
     State("upload-data", "filename"),
     State("comment-box", "value")],
    prevent_initial_call=True
)
def download_values(n_clicks, selected_data, raw_data, active_steps_defn, filename, comment):
    """
    Download all values shown in the interface as a summary CSV

    n_clicks: "Download Values (CSV)" button click instance
    selected_data: json wrapped Arduino data (currently displayed range)
    raw_data: full raw json input
    active_steps_defn: active step threshold set by the slider
    filename: original uploaded filename
    comment: text entered in the comment box
    """
    if not n_clicks or selected_data is None:
        return None

    df = pd.read_json(io.StringIO(selected_data), orient="split")
    if df.empty:
        return None
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Metrics shown across the interface
    total_steps = int(df["steps"].sum())
    total_min = round((df["timestamp"].iloc[-1] - df["timestamp"].iloc[0]).total_seconds() / 60)
    threshold = active_steps_defn
    active_step = int(df[df["steps"] >= threshold]["steps"].sum())
    active_min = int(len(df[df["steps"] >= threshold]) * 5)

    max_idx = df["steps"].idxmax()
    max_val = int(df["steps"].loc[max_idx])
    max_ts = df["timestamp"].loc[max_idx].strftime("%Y-%m-%d %H:%M")
    mean_val = round(float(df["steps"].mean()), 2)

    selected_start = df["timestamp"].iloc[0].strftime("%Y-%m-%d %H:%M")
    selected_end = df["timestamp"].iloc[-1].strftime("%Y-%m-%d %H:%M")

    # UID / device version parsed from the filename
    uid, device = "", ""
    if filename:
        parts = filename.split("_")
        uid = parts[0]
        if len(parts) > 1:
            device = parts[1].rsplit(".", 1)[0]

    # Full collected period from the raw data
    collected_start, collected_end = "", ""
    if raw_data:
        raw_df = pd.read_json(io.StringIO(raw_data), orient="split")
        if not raw_df.empty:
            raw_df["timestamp"] = pd.to_datetime(raw_df["timestamp"])
            collected_start = raw_df["timestamp"].iloc[0].strftime("%Y-%m-%d %H:%M")
            collected_end = raw_df["timestamp"].iloc[-1].strftime("%Y-%m-%d %H:%M")

    summary = pd.DataFrame(
        [
            ("UID", uid),
            ("Device Version", device),
            ("Collected Period Start", collected_start),
            ("Collected Period End", collected_end),
            ("Selected Range Start", selected_start),
            ("Selected Range End", selected_end),
            ("Active Step Threshold", threshold),
            ("Total Steps", total_steps),
            ("Total Minutes", total_min),
            ("Active Steps", active_step),
            ("Active Minutes", active_min),
            ("Max Steps", max_val),
            ("Max Steps Timestamp", max_ts),
            ("Mean Steps (per 5 min)", mean_val),
            ("Comments", (comment or "").replace("\r", " ").replace("\n", " ").strip()),
        ],
        columns=["Metric", "Value"]
    )

    export_name = f"{uid or 'data'}_summary_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
    return dcc.send_data_frame(summary.to_csv, export_name, index=False)

def aggregate_data(df, unit):
    """
    Aggregate data for graphs

    df: dataframe containing arduino data
    unit: specified unit of time for aggregation
    """
    # Abbreviation mappings for days and months
    day_abbreviations = {
        "Monday": "Mon", "Tuesday": "Tue", "Wednesday": "Wed",
        "Thursday": "Thu", "Friday": "Fri", "Saturday": "Sat", "Sunday": "Sun"
    }
    month_abbreviations = {
        "January": "Jan", "February": "Feb", "March": "Mar", "April": "Apr",
        "May": "May", "June": "Jun", "July": "Jul", "August": "Aug",
        "September": "Sep", "October": "Oct", "November": "Nov", "December": "Dec"
    }

    if unit == "hour":
        grouped = df.resample("h", on="timestamp").steps
        df_new = grouped.sum()
        # Untracked bins (device off) become NaN, not 0, so they are never
        # mistaken for a real zero-step reading.
        df_new[grouped.count() == 0] = np.nan
        df_new = df_new.to_frame().reset_index()
        df_new["hour"] = df_new["timestamp"].dt.hour
    else:
        grouped = df.resample("D", on="timestamp").steps
        df_new = grouped.sum()
        df_new[grouped.count() == 0] = np.nan
        df_new = df_new.to_frame().reset_index()
        df_new["day"] = df_new["timestamp"].dt.day
        df_new["day_of_week"] = df_new["timestamp"].dt.weekday
        if unit == "month":
            df_new["day_of_week"] = df_new["timestamp"].dt.day_name()
            df_new["month"] = df_new["timestamp"].dt.month_name()
            df_new["month"] = df_new["month"].map(month_abbreviations)
            df_new["day_of_week"] = df_new["day_of_week"].map(day_abbreviations)

    return df_new


# Any gap between consecutive readings longer than this is treated as an
# untracked period: the line breaks across it instead of bridging two
# tracked stretches (e.g. the seam between two merged datasets).
GAP_THRESHOLD = pd.Timedelta("10min")

def break_gaps(df):
    """
    Insert a single NaN-valued point in the middle of each untracked gap so a
    line plot breaks across it rather than drawing a straight line between the
    last reading before the gap and the first reading after it.
    """
    d = df.sort_values("timestamp").reset_index(drop=True)
    diffs = d["timestamp"].diff()
    gap_idx = [i for i in d.index if pd.notna(diffs.iloc[i]) and diffs.iloc[i] > GAP_THRESHOLD]
    if not gap_idx:
        return d

    inserts = []
    for i in gap_idx:
        prev_t = d["timestamp"].iloc[i - 1]
        curr_t = d["timestamp"].iloc[i]
        inserts.append({"timestamp": prev_t + (curr_t - prev_t) / 2, "steps": np.nan})

    out = pd.concat([d, pd.DataFrame(inserts)], ignore_index=True)
    return out.sort_values("timestamp").reset_index(drop=True)

# Display data information used in graphs
@app.callback(
        Output("content-patientinfo", "children"),
        [Input("upload-data", "filename"),
         Input("raw-data", "data")]
)
def update_patient_info(filename, raw_data):
    """
    Display the patient participant information as indicated on the filename

    filename: name of the provided csv file
    raw_data: full raw json input
    """
    if raw_data is None: return None

    df = pd.read_json(io.StringIO(raw_data), orient="split")
    # Handle cases where input data is empty
    if df.empty:
        parts = filename.split("_")
        patient_id = parts[0]
        device_version = parts[1].rsplit(".", 1)[0]

        return [
            html.H4("Basic Information", className="color-main", style={"margin-top":"10px", "margin-bottom":"15px"}),
            html.H5(f"UID: {patient_id}", className="color-sub"),
            html.H5(f"Device Version: {device_version}", className="color-sub", style={"margin-bottom":"15px"}),
            html.H5("* Note: The selected data file is empty", className="color-sub")
        ]

    # Dummy data doesn"t need filename parsing
    if df["timestamp"].iloc[0] == datetime(2024,2,1,0,0,0):
        return [
            html.H4("Basic Information", className="color-main", style={"margin-top":"10px", "margin-bottom":"15px"}),
            html.H5("The graphs are currently randomly generated", className="color-sub")
        ]

    # Extract from filename
    if filename:
        try:
            parts = filename.split("_")
            patient_id = parts[0]
            device_version = parts[1].rsplit(".", 1)[0]
        except IndexError:
            # Filenames that are not following the convention
            return [
                html.H4("Basic Information", className="color-main", style={"margin-top":"10px", "margin-bottom":"15px"}),
                html.H5(f"File Name: {filename}", className="color-sub")
            ]
        else:
            return [
                html.H4("Basic Information", className="color-main", style={"margin-top":"10px", "margin-bottom":"15px"}),
                html.H5(f"UID: {patient_id}", className="color-sub"),
                html.H5(f"Device Version: {device_version}", className="color-sub", style={"margin-bottom":"15px"})
            ]

    return [html.H4("Basic Information Unavailable")]

# Display collected period of the data
@app.callback(
        Output("content-collected-period", "children"),
        [Input("raw-data", "data")]
)
def update_collected_period(raw_data):
    """
    Display the collected period of the full raw data

    raw_data: full raw json input
    """
    if raw_data is None: return None

    df = pd.read_json(io.StringIO(raw_data), orient="split")

    # Handle cases where the input data is empty
    if df.empty:
        return dbc.Row(
            dbc.Col(
                html.Div("No Data Available", className="flex-container")
            )
        )

    collected_period = (str(df["timestamp"].iloc[0].strftime("%b. %d, %I:%M %p")) + 
        " - " + str(df["timestamp"].iloc[-1].strftime("%b. %d, %I:%M %p")))

    return html.H5(collected_period, className="color-sub", style={"text-align":"left"})

# Display total steps in the used data
@app.callback(
        Output("content-total-steps", "children"),
        [Input("selected-data", "data")]
)
def update_total_steps(selected_data):
    """
    Display total steps of the displaying data

    selected_data: json wrapped Arduino data
    """
    if selected_data is None: return None

    df = pd.read_json(io.StringIO(selected_data), orient="split")
    # Handle cases where the input data is empty
    if df.empty:
        return dbc.Row(
            dbc.Col(
                html.Div("No Data Available", className="flex-container")
            )
        )

    total_steps = df["steps"].sum()

    return [
        html.Span(total_steps, style={"font-weight":"bold", "font-size":"40px"}),
        html.Span(" Steps", style={"margin-left": "5px", "font-size":"18px"})
    ]

# Display total minutes in the used data
@app.callback(
        Output("content-total-minutes", "children"),
        [Input("selected-data", "data")]
)
def update_total_minutes(selected_data):
    """
    Display total minutes of the displaying data

    selected_data: json wrapped Arduino data
    """
    if selected_data is None: return None

    df = pd.read_json(io.StringIO(selected_data), orient="split")
    # Handle cases where the input data is empty
    if df.empty:
        return dbc.Row(
            dbc.Col(
                html.Div("No Data Available", className="flex-container")
            )
        )

    total_min = round((df["timestamp"].iloc[-1]-df["timestamp"].iloc[0]).total_seconds() / 60)

    return [
        html.Span(total_min, style={"font-weight":"bold", "font-size":"40px"}),
        html.Span(" Min.", style={"margin-left": "5px", "font-size":"18px"})
    ]

# Display active steps in the used data
@app.callback(
        Output("content-active-steps", "children"),
        [Input("selected-data", "data"),
         Input("active-step-slider", "value")]
)
def update_active_steps(selected_data, active_steps_defn):
    """
    Display active steps related to the displaying data

    selected_data: json wrapped Arduino data
    active_steps_defn: active steps definition set by user
    """
    if selected_data is None: return None

    df = pd.read_json(io.StringIO(selected_data), orient="split")
    # Handle cases where the input data is empty
    if df.empty:
        return dbc.Row(
            dbc.Col(
                html.Div("No Data Available", className="flex-container")
            )
        )

    unit_active_steps = active_steps_defn
    active_step = df[df["steps"] >= unit_active_steps]["steps"].sum()
    inactive_step = df[df["steps"] < unit_active_steps]["steps"].sum()

    fig_active_steps = go.Figure(go.Pie(
        labels=["Active Steps", "Inactive Steps"],
        values=[active_step, inactive_step],
        hole=0.7,
        hoverinfo="label+percent+value",
        textinfo="none",
        marker=dict(colors= px.colors.sequential.GnBu[5:7])
    ))

    fig_active_steps.update_layout(
        annotations=[
            dict(
                text=f"<span style='color:midnightblue'><b><span style='font-size:40px'>{active_step}</span></b><br><br>Steps</span>",
                x=0.5,
                y=0.5,
                font_size=18,
                showarrow=False,
                align="center"
            )
        ],
        autosize=True,
        paper_bgcolor="white",
        plot_bgcolor="white",
        uniformtext={"minsize":16, "mode":"hide"},
        showlegend=False,
        hoverlabel={"bgcolor":"white", "font_size":16, "font_family":"Roboto"},
        margin=dict(l=10, r=10, t=10, b=10)
    )

    return dcc.Graph(figure=fig_active_steps, style={"height": "100%", "width": "100%"})

# Display active minutes in the used data
@app.callback(
        Output("content-active-minutes", "children"),
        [Input("selected-data", "data"),
         Input("active-step-slider", "value")]
)
def update_active_minutes(selected_data, active_steps_defn):
    """
    Display active minutes related to the displaying data

    selected_data: json wrapped Arduino data
    active_steps_defn: active step definition set by the user
    """
    if selected_data is None: return None

    df = pd.read_json(io.StringIO(selected_data), orient="split")
    # Handle cases where the input data is empty
    if df.empty:
        return dbc.Row(
            dbc.Col(
                html.Div("No Data Available", className="flex-container")
            )
        )

    unit_active_steps = active_steps_defn
    active_min = len(df[df["steps"] >= unit_active_steps]) * 5
    inactive_min = len(df[df["steps"] < unit_active_steps]) * 5

    fig_active_mins = go.Figure(go.Pie(
            labels=["Active Mins", "Inactive Mins"],
            values=[active_min, inactive_min],
            hole=0.7,
            hoverinfo="label+percent+value",
            textinfo="none",
            marker=dict(colors=px.colors.sequential.GnBu[3:5])
        ))

    fig_active_mins.update_layout(
        annotations=[
            dict(
                text=f"<span style='color:midnightblue'><b><span style='font-size:40px'>{active_min}</span></b><br><br>Min</span>",
                x=0.5,
                y=0.5,
                font_size=18,
                showarrow=False,
                align="center"
            )
        ],
        autosize=True,
        paper_bgcolor="white",
        plot_bgcolor="white",
        uniformtext={"minsize":16, "mode":"hide"},
        showlegend=False,
        hoverlabel={"bgcolor":"white", "font_size":16, "font_family":"Roboto"},
        margin=dict(l=10, r=10, t=10, b=10)
    )

    return dcc.Graph(figure=fig_active_mins, style={"height": "100%", "width": "100%"})

# Visualize full data
@app.callback(
        Output("tab-content-scatter", "children"),
        [Input("graph-tab-scatter", "active_tab"),
         Input("selected-data", "data")]
)
def update_scatter(selected_value, selected_data):
    """
    Display a scatter plot based on the selected_data

    selected_value = selected timeframe
    selected_data = json wrapped Arduino data
    """
    if selected_data is None:
        return dbc.Row(
            dbc.Col(
                html.Div("No Data Available", className="flex-container")
            )
        )

    df = pd.read_json(io.StringIO(selected_data), orient="split")
    # Handle cases where the input data is empty
    if df.empty:
        return dbc.Row(
            dbc.Col(
                html.Div("No Data Available", className="flex-container")
            )
        )

    if selected_value =="scatter-hourly":
        # Aggregate data by hour
        df_new = aggregate_data(df, "hour")
        unit_of_time = "hour"

    elif selected_value == "scatter-daily":
        # Aggregate data by day
        df_new = aggregate_data(df, "day")
        unit_of_time = "day"

    else:
        # Break the raw line across any untracked gaps instead of bridging them.
        df_new = break_gaps(df)
        unit_of_time = "5 minutes"

    if df_new.empty:
        return dbc.Row(
            dbc.Col(
                html.Div("No Data Available", className="flex-container")
            )
        )

    # Plot the aggregated data. connectgaps=False keeps NaN (untracked) periods
    # as breaks in the line rather than joining across them.
    plot = go.Figure()
    plot.add_trace(go.Scatter(x=df_new["timestamp"], y=df_new["steps"],
                              mode="lines+markers", connectgaps=False))
    plot.update_layout(xaxis_title="Date", yaxis_title="Steps", xaxis_tickangle=45)

    # Calculate basic information
    try:
        df_new = df_new.reset_index()
        max_index = df_new["steps"].idxmax()
        max_val = df_new["steps"].iloc[max_index]
        max_timestamp = df_new["timestamp"].iloc[max_index].strftime("%b. %d, %I:%M %p")
        mean_val = round(df_new["steps"].mean(), 2)
    except (IndexError, ValueError, KeyError) as e:
        # For error catching
        print(f"Error calculating basic information: {e}")
        max_val, max_timestamp, mean_val = 0, "N/A", 0

    time_min = df_new["timestamp"].min()
    time_max = df_new["timestamp"].max()
    time_range = [time_min, time_max]

    plot.update_layout(
        xaxis={"range": time_range},
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
        paper_bgcolor="white",
        hoverlabel={"bgcolor": "white",
                    "font_size": 16,
                    "font_family": "Roboto"}
    )
    plot.update_traces(marker_color="mediumaquamarine", line_color="lightseagreen")

    return dbc.Row(
        [
            dbc.Col(dcc.Graph(figure=plot), width=12),
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader("Graph Information", className="card-title"),
                    dbc.CardBody(
                        [
                            html.Ul([
                                html.Li([
                                    "A maximum of ",
                                    html.Strong(str(max_val)),
                                    f" steps were taken at {max_timestamp}."
                                ]),
                                html.Li([
                                    "A mean of ",
                                    html.Strong(str(mean_val)),
                                    f" steps were taken every {unit_of_time} throughout this period."
                                ])
                            ])
                        ],
                        className="card-body"
                    )
                ]),
                width=12
            )
        ],
        className="flex-container"
    )

# Visualize the aggregated data with sunburst graph
@app.callback(
        Output("content-sunburst", "children"),
        [Input("selected-data", "data")]
)
def update_sunburst(selected_data):
    """
    Display a sunburst chart based on the selected_data

    selected_data: json wrapped Arduino data
    """
    if selected_data is None:
        return dbc.Row(
            dbc.Col(
                html.Div("No Data Available", className="flex-container")
            )
        )

    df = pd.read_json(io.StringIO(selected_data), orient="split")
    # Handle cases where the input data is empty
    if df.empty:
        return dbc.Row(
            dbc.Col(
                html.Div("No Data Available", className="flex-container")
            )
        )
    df_new = aggregate_data(df, "month")
    df_sunburst = df_new.groupby(["month", "day_of_week"]).agg({"steps":"sum"}).reset_index()
    num_months = len(df_sunburst.month.unique())

    fig = px.sunburst(
        df_sunburst,
        path=["month", "day_of_week"],
        values="steps",
        color="month",
        color_discrete_sequence=px.colors.sequential.GnBu[5:5+num_months],
        custom_data=["month", "day_of_week", "steps"]
    )
    fig.update_traces(
        insidetextfont={"color":"white"},
        hovertemplate="<b>%{customdata[0]}</b> - %{customdata[1]}<br>" +
                  "%{customdata[2]} Steps<br>"
    )
    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin={"l":10, "r":10, "t":20, "b":10},
        uniformtext={"minsize":18, "mode":"hide"},
        hoverlabel={"bgcolor":"white", "font_size":16, "font_family":"Roboto"}
    )

    return dcc.Graph(figure=fig)

# Visualize the aggregated data with box & whisker plots
@app.callback(
        Output("tab-content-boxwhisker", "children"),
        [Input("graph-tab-boxwhisker", "active_tab"),
         Input("selected-data", "data")]
)
def update_boxwhisker(selected_value, selected_data):
    """
    Display a box & whisker chart based on the selected_data

    selected_value: selected timeframe to view
    selected_data: json wrapped Arduino data
    """
    if selected_data is None: return None

    df = pd.read_json(io.StringIO(selected_data), orient="split")
    # Handle cases where the input data is empty
    if df.empty:
        return dbc.Row(
            dbc.Col(
                html.Div("No Data Available", className="flex-container")
            )
        )
    traces = []

    if selected_value == "boxwhisker-hourly":
        # Aggregate data by hour
        df_new = aggregate_data(df, "hour")
        num_categories = df_new["hour"].nunique()
        color_scale = px.colors.sequential.Agsunset # or Cividis
        colors = {
            hour: color_scale[int(np.floor(idx / num_categories * (len(color_scale) - 1)))]
                for idx, hour in enumerate(sorted(df_new["hour"].unique()))
        }
        hour_labels = [
            "12AM", "1AM", "2AM", "3AM", "4AM", "5AM", "6AM", "7AM", "8AM", "9AM", "10AM", "11AM",
            "12PM", "1PM", "2PM", "3PM", "4PM", "5PM", "6PM", "7PM", "8PM", "9PM", "10PM", "11PM"
        ]

        for hr in sorted(df_new["hour"].unique()):
            # Plot the box & whisker plot of hourly aggregated data
            trace = go.Box(
                y=df_new[df_new["hour"]==hr]["steps"].values,
                name=hour_labels[hr],
                boxpoints="outliers",
                marker_color=colors[hr],
                marker={"outliercolor":"rgba(219, 64, 82, 0.6)",
                        "line":{"outliercolor":"rgba(219, 64, 82, 0.6)",
                                "outlierwidth":2}
                }
            )
            traces.append(trace)

        plot = go.Figure(traces)
        plot.update_layout(xaxis_title="Hour of the Day", yaxis_title="Steps", showlegend=False)
    elif selected_value == "boxwhisker-daily":
        # Aggregate data by day
        df_new = aggregate_data(df, "day")
        num_categories = df_new["day_of_week"].nunique()
        color_scale = px.colors.sequential.Agsunset
        colors = {day: color_scale[int(np.floor(idx / num_categories * (len(color_scale) - 1)))]
                    for idx, day in enumerate(sorted(df_new["day_of_week"].unique()))}
        day_labels = ["Mon", "Tue", "Wed", "Thurs", "Fri", "Sat", "Sun"]

        for day in sorted(df_new["day_of_week"].unique()):
            # Plot the box & whisker plot of daily aggregated data
            trace = go.Box(
                y=df_new[df_new["day_of_week"]==day]["steps"].values,
                name=day_labels[day],
                boxpoints="outliers",
                marker_color=colors[day],
                marker={"outliercolor":"rgba(219, 64, 82, 0.6)",
                        "line":{"outliercolor":"rgba(219, 64, 82, 0.6)",
                                "outlierwidth":2}
                }
            )
            traces.append(trace)

        plot = go.Figure(traces)
        plot.update_layout(xaxis_title="Day of the Week", yaxis_title="Steps", showlegend=False)
    else:
        # Aggregate data by month
        df_new = aggregate_data(df, "month")
        num_categories = df_new["month"].nunique()
        color_scale = px.colors.sequential.Agsunset
        colors = {month: color_scale[int(np.floor(idx / num_categories * (len(color_scale) - 1)))]
                    for idx, month in enumerate(df_new["month"].unique())}

        for month in df_new["month"].unique():
            # Plot the box & whisker plot of daily aggregated data
            trace = go.Box(
                y=df_new[df_new["month"]==month]["steps"].values,
                name=month,
                boxpoints="outliers",
                marker_color=colors[month],
                marker={"outliercolor":"rgba(219, 64, 82, 0.6)",
                        "line":{"outliercolor":"rgba(219, 64, 82, 0.6)",
                                "outlierwidth":2}
                }
            )
            traces.append(trace)

        plot = go.Figure(traces)
        plot.update_layout(xaxis_title="Month", yaxis_title="Steps", showlegend=False)

    plot.update_layout(
        margin={"l":20, "r":20, "t":20, "b":20},
        paper_bgcolor="white",
        hoverlabel={"bgcolor":"white", "font_size":16, "font_family":"Roboto"}
    )

    return dbc.Row(
        dbc.Col(
            dcc.Loading(
                id="loading-1",
                type="default",
                children=[dcc.Graph(figure=plot, id="plot")]
            )
        ),
        className="flex-container"
    )

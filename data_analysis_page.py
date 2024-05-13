"""
Import Libraries
"""
import base64
import io
from datetime import datetime, timedelta

from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px

from app import app

# Define the layout of the app
layout = html.Div([
    dbc.Container(
        [
            # Act as a global variable for the data used for plotting
            html.Div(id="read-data", style={"display":"none"}),
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
                style={"margin-bottom": "10px"}
            ),
            dbc.Row(
                dbc.Col(
                    [
                        html.H4("Collected Period", className="color-main"),
                        html.Div(id="content-collected-period"),
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
                                    dbc.Tab(label="Throughout the Week (Over Days)", tab_id="boxwhisker-daily")
                                ],
                                active_tab="boxwhisker-hourly",
                            ),
                            html.Div(id="tab-content-boxwhisker", className="graph-section")
                        ],
                        width=8
                    )
                ],
                className="row"
            )
        ],
        fluid=True,
        style={"padding": "40px"}
    )
])

# Create/Read the data for entire dashboard
@app.callback(
        Output("read-data", "children"),
        [Input("upload-data", "contents")],
        [State("upload-data", "filename")]
)
def read_data(contents, filename):
    """
    Read the CSV file that was generated from the application

    contents: data within
    filename: name of the csv file
    """
    if contents is None:
        # Create dummy data (For demo purposes)
        df = pd.DataFrame(
            {"timestamp": np.arange(datetime(2024,2,1,0,0,0), datetime(2024,5,30,23,59,0), timedelta(minutes=5))}
        )
        x = np.arange(0,df.size)
        def f(x):
            tmp = np.sin(0.01*x) + np.random.normal(size=len(x))*25
            tmp[tmp<0] = 0
            return tmp.round()
        df["steps"] = f(x)
    else:
        _, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)
        if "csv" in filename:
            df=pd.read_csv(io.StringIO(decoded.decode("utf-8")), names=["timestamp","steps"])
        else:
            return None

        df["timestamp"] = pd.to_datetime(df["timestamp"])

    return df.to_json(date_format="iso", orient="split")

def aggregate_data(df, unit):
    """
    Aggregate data for graphs

    df: dataframe containing arduino data
    unit: specified unit of time for aggregation
    """
    if unit == "hour":
        df_new = df.resample("h", on="timestamp").steps.sum()
        df_new = df_new.to_frame().reset_index()
        df_new["hour"] = df_new["timestamp"].dt.hour
    else:
        df_new = df.resample("D", on="timestamp").steps.sum()
        df_new = df_new.to_frame().reset_index()
        df_new["day"] = df_new["timestamp"].dt.day
        df_new["day_of_week"] = df_new["timestamp"].dt.weekday

        if unit == "month":
            df_new["day_of_week"] = df_new["timestamp"].dt.day_name()
            df_new["month"] = df_new["timestamp"].dt.month_name()

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

            df_new["month"] = df_new["month"].map(month_abbreviations)
            df_new["day_of_week"] = df_new["day_of_week"].map(day_abbreviations)
            
    return df_new

# Display data information used in graphs
@app.callback(
        Output("content-patientinfo", "children"),
        [Input("upload-data", "filename"),
         Input("read-data", "children")]
)
def update_patient_info(filename, json_data):
    """
    Display the patient participant information as indicated on the filename

    filename: name of the provided csv file
    json_data: json wrapped Arduino data
    """
    if json_data is None: return None

    df = pd.read_json(io.StringIO(json_data), orient="split")

    # Dummy data doesn"t need filename parsing
    if df["timestamp"].iloc[0] == datetime(2024,2,1,0,0,0):
        return [
            html.H4("Basic Information", className="color-main", style={"margin-top":"10px", "margin-bottom":"15px"}),
            html.H5("The graphs are currently randomly generated", className="color-sub")
        ]
    # Extract from filename
    else:
        if filename:
            # TODO: Confirm filename style (i.e., IMUData_Readable_UID_DeviceType)
            parts = filename.split("_")
            patient_id = parts[2]
            device_type = parts[3].split(".")[0]

            return [
                html.H4("Basic Information", className="color-main", style={"margin-top":"10px", "margin-bottom":"15px"}),
                html.H5(f"UID: {patient_id}", className="color-sub"),
                html.H5(f"Device Type: {device_type}", className="color-sub", style={"margin-bottom":"15px"})
            ]

        return [html.H4("Basic Information Unavailable")]

# Display collected period of the data
@app.callback(
        Output("content-collected-period", "children"),
        [Input("read-data", "children")]
)
def update_collected_period(json_data):
    """
    Display collected period of the displaying data

    json_data: json wrapped Arduino data
    """
    if json_data is None: return None

    df = pd.read_json(io.StringIO(json_data), orient="split")
    collected_period = (str(df["timestamp"].iloc[0].strftime("%b. %d, %I:%M %p")) + 
                    " - " + str(df["timestamp"].iloc[-1].strftime("%b. %d, %I:%M %p")))

    return html.H5(collected_period, className="color-sub",
                   style={"text-align":"left"})

# Display total steps in the used data
@app.callback(
        Output("content-total-steps", "children"),
        [Input("read-data", "children")]
)
def update_total_steps(json_data):
    """
    Display total steps of the displaying data

    json_data: json wrapped Arduino data
    """
    if json_data is None: return None

    df = pd.read_json(io.StringIO(json_data), orient="split")

    total_steps = df["steps"].sum()

    return [
        html.Span(total_steps, style={"font-weight":"bold", "font-size":"40px"}),
        html.Span(" Steps", style={"margin-left": "5px", "font-size":"18px"})
    ]

# Display total minutes in the used data
@app.callback(
        Output("content-total-minutes", "children"),
        [Input("read-data", "children")]
)
def update_total_minutes(json_data):
    """
    Display total minutes of the displaying data

    json_data: json wrapped Arduino data
    """
    if json_data is None: return None

    df = pd.read_json(io.StringIO(json_data), orient="split")

    total_min = round((df["timestamp"].iloc[-1]-df["timestamp"].iloc[0]).total_seconds() / 60)

    return [
        html.Span(total_min, style={"font-weight":"bold", "font-size":"40px"}),
        html.Span(" Min.", style={"margin-left": "5px", "font-size":"18px"})
    ]

# Display active steps in the used data
@app.callback(
        Output("content-active-steps", "children"),
        [Input("read-data", "children"),
         Input("active-step-slider", "value")]
)
def update_active_steps(json_data, active_steps_defn):
    """
    Display active steps related to the displaying data

    json_data: json wrapped Arduino data
    """
    if json_data is None: return None

    df = pd.read_json(io.StringIO(json_data), orient="split")

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
                align='center'
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

    return dcc.Graph(figure=fig_active_steps, style={'height': '100%', 'width': '100%'})

# Display active minutes in the used data
@app.callback(
        Output("content-active-minutes", "children"),
        [Input("read-data", "children"),
         Input("active-step-slider", "value")]
)
def update_active_minutes(json_data, active_steps_defn):
    """
    Display active minutes related to the displaying data

    json_data: json wrapped Arduino data
    """
    if json_data is None: return None

    df = pd.read_json(io.StringIO(json_data), orient="split")

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
                align='center'
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

    return dcc.Graph(figure=fig_active_mins, style={'height': '100%', 'width': '100%'})

# Visualize full data
@app.callback(
        Output("tab-content-scatter", "children"),
        [Input("graph-tab-scatter", "active_tab"),
         Input("read-data", "children")]
)
def update_scatter(selected_value, json_data):
    """
    Display a scatter plot based on the json_data

    selected_value = selected timeframe
    json_data = json wrapped Arduino data
    """
    if json_data is None: return None

    df = pd.read_json(io.StringIO(json_data), orient="split")

    if selected_value =="scatter-hourly":
        # Aggregate data by hour
        df_new = aggregate_data(df, "hour")
        unit_of_time = "hour"

        # Plot the hourly aggregated data
        plot = go.Figure()
        plot.add_trace(go.Scatter(x=df_new["timestamp"], y = df_new["steps"], mode="lines+markers"))
        plot.update_layout(xaxis_title="Date", yaxis_title="Steps", xaxis_tickangle=45)

        # Calculate basic information
        max_index = df_new[["steps"]].idxmax().steps
        max_val = df_new["steps"].iloc[max_index]
        max_timestamp = df_new["timestamp"].iloc[max_index].strftime("%b. %d, %I:%M %p")
        mean_val = round(df_new["steps"].mean(), 2)

    elif selected_value == "scatter-daily":
        # Aggregate data by day
        df_new = aggregate_data(df, "day")
        unit_of_time = "day"

        # Plot the daily aggregated data
        plot = go.Figure()
        plot.add_trace(go.Scatter(x=df_new["timestamp"], y = df_new["steps"], mode="lines+markers"))
        plot.update_layout(xaxis_title="Date", yaxis_title="Steps", xaxis_tickangle=45)
        # For Histogram
        # plot = px.histogram(df_day, x="timestamp", y="steps", nbins=df_day.shape[0])
        # plot.update_layout(xaxis_title="Date",
        #                     yaxis_title="Steps",
        #                     bargap=0.2,
        #                     xaxis_tickangle=45)

        # Calculate basic information
        max_index = df_new[["steps"]].idxmax().steps
        max_val = df_new["steps"].iloc[max_index]
        max_timestamp = df_new["timestamp"].iloc[max_index].strftime("%b. %d")
        mean_val = round(df_new["steps"].mean(), 2)

    else:
        df_new = df
        unit_of_time = "5 minutes"

        plot = go.Figure()
        plot.add_trace(go.Scatter(x=df_new["timestamp"], y=df_new["steps"], mode="lines+markers"))
        plot.update_layout(xaxis_title="Date", yaxis_title="Steps", xaxis_tickangle=45)

        # Calculate basic information
        max_index = df_new[["steps"]].idxmax().steps
        max_val = df_new["steps"].iloc[max_index]
        max_timestamp = df_new["timestamp"].iloc[max_index].strftime("%b. %d, %I:%M %p")
        mean_val = round(df_new["steps"].mean(), 2)

    plot.update_layout(
        xaxis={"range":[df_new["timestamp"].min(), df_new["timestamp"].max()]},
        margin={"l":20, "r":20, "t":20, "b":20},
        paper_bgcolor="white",
        hoverlabel={"bgcolor":"white",
                    "font_size":16,
                    "font_family":"Roboto"}
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
        [Input("read-data", "children")]
)
def update_sunburst(json_data):
    """
    Display a sunburst chart based on the json_data

    json_data: json wrapped Arduino data
    """
    if json_data is None: return None

    df = pd.read_json(io.StringIO(json_data), orient="split")
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
         Input("read-data", "children")]
)
def update_boxwhisker(selected_value, json_data):
    """
    Display a box & whisker chart based on the json_data

    selected_value: selected timeframe to view
    json_data: json wrapped Arduino data
    """
    if json_data is None: return None

    df = pd.read_json(io.StringIO(json_data), orient="split")
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
    else:
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

    plot.update_layout(
        margin={"l":20, "r":20, "t":20, "b":20},
        paper_bgcolor="white",
        hoverlabel={"bgcolor":"white", "font_size":16, "font_family":"Roboto"}
    )

    # TODO: Revisit the bottom code
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

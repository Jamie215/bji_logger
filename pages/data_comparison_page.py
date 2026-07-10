"""
Data Comparison page

Compare two or more datasets (same participant across periods, or different
participants) as a set of length-robust, rate/trend/profile views. Each
uploaded file becomes a labelled "series" tagged with the participant UID and
its own date span parsed from the data. Nothing assumes the files are equal
length or line up as clean quarters.
"""
import base64
import io
import re
from datetime import datetime

from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px

from app_instance import app

# Distinct, stable colours so a series keeps the same colour across every chart.
SERIES_COLORS = px.colors.qualitative.Dark24

# Ratio of longest-to-shortest span above which a note reminds the reader to
# lean on per-day rates rather than raw totals for a fair comparison.
DISPARITY_THRESHOLD = 2.0

# ---------------------------------------------------------------------------
# Pure helpers (no Dash dependencies) so they can be tested in isolation
# ---------------------------------------------------------------------------

def read_series_csv(contents):
    """
    Decode one uploaded file into a timestamp/steps dataframe.

    contents: base64 "data:...," string from a dcc.Upload
    """
    _, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)
    df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
    if df.columns[0] == "timestamp" and df.columns[1] == "steps":
        pass  # CSV has a header row
    else:
        # Headerless (the app exports headerless CSVs); keep every row.
        df = pd.read_csv(io.StringIO(decoded.decode("utf-8")), names=["timestamp", "steps"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df


def parse_filename(fname):
    """
    Extract (participant_id, quarter, device) from the naming convention
    Subject{pid}_{quarter}.{device}.csv (e.g. Subject109_1.1.csv). Any part
    that does not match (e.g. a merged export) comes back as None so callers
    degrade gracefully.
    """
    stem = fname or ""
    if stem.lower().endswith(".csv"):
        stem = stem[:-4]
    parts = stem.split("_")
    raw_id = parts[0] if parts and parts[0] else stem
    match = re.search(r"(\d+)", raw_id)
    pid = match.group(1) if match else (raw_id or "?")

    quarter = device = None
    if len(parts) > 1:
        seg = parts[1].split(".")
        if seg and seg[0].isdigit():
            quarter = int(seg[0])
        if len(seg) > 1 and seg[1].isdigit():
            device = int(seg[1])
    return pid, quarter, device


def parse_series(contents_list, filenames_list):
    """
    Turn the uploaded files into a chronologically ordered list of series dicts:
    {pid, quarter, device, label, start, end, data(json)}. Labels are concise
    and context-aware: just the quarter (Q1) when every file is the same
    participant, otherwise the participant too (P109 Q1).
    """
    raw = []
    for contents, fname in zip(contents_list or [], filenames_list or []):
        try:
            df = read_series_csv(contents)
        except Exception as e:
            print(f"Could not read {fname}: {e}")
            continue
        if df.empty:
            continue
        pid, quarter, device = parse_filename(fname)
        raw.append({
            "pid": pid, "quarter": quarter, "device": device, "df": df,
            "start": df["timestamp"].min(), "end": df["timestamp"].max(),
        })

    if not raw:
        return []

    single_participant = len({r["pid"] for r in raw}) == 1

    series = []
    for r in raw:
        qpart = f"Q{r['quarter']}" if r["quarter"] is not None else None
        if single_participant:
            label = qpart or f"P{r['pid']}"
        else:
            label = f"P{r['pid']}" + (f" {qpart}" if qpart else "")
        series.append({
            "pid": r["pid"],
            "quarter": r["quarter"],
            "device": r["device"],
            "label": label,
            "start": r["start"].isoformat(),
            "end": r["end"].isoformat(),
            "data": r["df"].to_json(orient="split", date_format="iso"),
        })

    # Order chronologically by start.
    series.sort(key=lambda s: s["start"])

    # Ensure labels are unique (e.g. two devices within the same quarter).
    seen = {}
    for s in series:
        base = s["label"]
        if base in seen:
            seen[base] += 1
            suffix = f"d{s['device']}" if s["device"] is not None else str(seen[base])
            s["label"] = f"{base} ({suffix})"
        else:
            seen[base] = 1
    return series


def load_series(series_list):
    """Return [(series_dict, dataframe), ...] with parsed timestamps."""
    out = []
    for s in series_list:
        df = pd.read_json(io.StringIO(s["data"]), orient="split")
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        out.append((s, df))
    return out


def series_color(index):
    """Stable colour for the series at position `index`."""
    return SERIES_COLORS[index % len(SERIES_COLORS)]


def days_with_data(df):
    """Number of distinct calendar days that actually have readings."""
    return int(df["timestamp"].dt.floor("D").nunique())


def span_days(df):
    """Calendar span of a series, inclusive, in days."""
    return int((df["timestamp"].max() - df["timestamp"].min()).days) + 1


def resample_with_gaps(df, freq):
    """
    Resample steps at `freq` (e.g. "D", "h"). Bins with no underlying rows
    become NaN (device off / not worn) rather than 0, so a genuine 0-step
    reading and "no data" are never conflated.
    """
    grouped = df.set_index("timestamp").resample(freq)["steps"]
    totals = grouped.sum()
    counts = grouped.count()
    totals[counts == 0] = np.nan
    return totals


def trajectory(df, align, freq_days=7):
    """
    Per-day average of the `steps` column within fixed-width bins.

    align: "calendar" -> x is the absolute date of each bin start
           "elapsed"  -> x is days since this series' own start
    Returns (x_values, y_values).
    """
    d = df[["timestamp", "steps"]].copy()
    start = d["timestamp"].min()
    d["bin"] = ((d["timestamp"] - start).dt.days // freq_days)

    grp = d.groupby("bin")
    total = grp["steps"].sum()
    ndays = grp["timestamp"].apply(lambda s: s.dt.floor("D").nunique())
    rate = total / ndays.replace(0, np.nan)

    if align == "elapsed":
        x = [int(b) * freq_days for b in rate.index]
    else:
        x = [start + pd.Timedelta(days=int(b) * freq_days) for b in rate.index]
    return x, list(rate.values)


def hour_of_day_profile(df):
    """Average steps during each hour of day on a typical recorded day."""
    d = df[["timestamp", "steps"]].copy()
    n_days = days_with_data(df) or 1
    total = d.groupby(d["timestamp"].dt.hour)["steps"].sum()
    return total / n_days


def day_of_week_profile(df):
    """Average total steps on each weekday (0=Mon .. 6=Sun)."""
    d = df[["timestamp", "steps"]].copy()
    weekday = d["timestamp"].dt.weekday
    date = d["timestamp"].dt.floor("D")
    total = d.groupby(weekday)["steps"].sum()
    ndays = date.groupby(weekday).nunique()
    return total / ndays.replace(0, np.nan)


def series_metrics(df, threshold):
    """Per-series summary metrics (rate-normalised where relevant)."""
    n_days = days_with_data(df) or 1
    total_steps = int(df["steps"].sum())
    active_intervals = int((df["steps"] >= threshold).sum())
    return {
        "span_days": span_days(df),
        "days_with_data": days_with_data(df),
        "total_steps": total_steps,
        "steps_per_day": round(total_steps / n_days, 1),
        "active_min_per_day": round(active_intervals * 5 / n_days, 1),
        "active_pct": round(100 * active_intervals / len(df), 1) if len(df) else 0.0,
        "mean_5min": round(float(df["steps"].mean()), 2) if len(df) else 0.0,
    }


def disparity_ratio(loaded):
    """Longest-to-shortest span ratio across series (1.0 if <2 series)."""
    if len(loaded) < 2:
        return 1.0
    spans = [span_days(df) for _, df in loaded]
    return max(spans) / max(1, min(spans))


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

data_comparison_layout = html.Div([
    dbc.Container(
        [
            dcc.Store(id="comparison-series"),
            html.H3("Data Comparison", className="color-main"),
            html.Div(
                "Upload two or more data files to compare — the same participant "
                "across periods, or different participants."
                "Comparisons use per-day rates and length-robust profiles.",
                className="color-sub",
                style={"margin-bottom": "15px"},
            ),

            dcc.Upload(
                id="comparison-upload",
                children=html.Div([
                    html.I(className="fas fa-upload"),
                    " Drag and Drop or ",
                    html.A("Select Files"),
                ]),
                multiple=True,
                className="upload-box mb-2",
            ),
            html.Div(id="comparison-file-status", className="mb-2"),
            html.Div(id="comparison-banner", className="mb-2"),

            html.H6("Set Active Steps:", className="color-sub", style={"margin-top": "5px"}),
            dcc.Slider(
                1, 100, step=None,
                marks={i: str(i) for i in [1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]},
                value=1, id="comparison-active-slider", className="active-step-slider",
            ),

            # Metrics matrix
            dbc.Row(
                dbc.Col([
                    html.H4("Summary Metrics", className="color-main"),
                    html.Div(id="comparison-metrics", className="white-background-2"),
                ], width=12),
                className="row", style={"margin-bottom": "10px"},
            ),

            # Direct comparison plot (shared calendar axis)
            dbc.Row(
                dbc.Col([
                    html.H4("Step Counts Over Time", className="color-main"),
                    dbc.Tabs(
                        id="comparison-direct-tab",
                        children=[
                            dbc.Tab(label="Daily", tab_id="direct-daily"),
                            dbc.Tab(label="Hourly", tab_id="direct-hourly"),
                            dbc.Tab(label="Original - Every 5 Min", tab_id="direct-raw"),
                        ],
                        active_tab="direct-daily",
                    ),
                    html.Div(id="comparison-direct", className="graph-section"),
                ], width=12),
                className="row", style={"margin-bottom": "10px"},
            ),

            # Trend / trajectory (weekly-binned active minutes per day)
            dbc.Row(
                dbc.Col([
                    html.H4("Active Minutes Trend Over Time", className="color-main"),
                    dbc.Row(
                        dbc.Col([
                            html.Label("Align by:", style={"margin-right": "10px"}),
                            dcc.RadioItems(
                                id="comparison-align",
                                options=[
                                    {"label": " Calendar date", "value": "calendar"},
                                    {"label": " Elapsed time", "value": "elapsed"},
                                ],
                                value="calendar",
                                labelStyle={"display": "inline-block", "margin-right": "15px"},
                                inputStyle={"margin-right": "4px"},
                            ),
                        ], width=12),
                        className="row",
                        style={"margin-bottom": "5px"},
                    ),
                    html.Div(id="comparison-trend", className="graph-section"),
                ], width=12),
                className="row", style={"margin-bottom": "10px"},
            ),

            # Profiles
            dbc.Row(
                [
                    dbc.Col([
                        html.H4("Activity by Hour of Day", className="color-main"),
                        html.Div(id="comparison-tod", className="graph-section"),
                    ], width=6),
                    dbc.Col([
                        html.H4("Activity by Day of Week", className="color-main"),
                        html.Div(id="comparison-dow", className="graph-section"),
                    ], width=6),
                ],
                className="row", style={"margin-bottom": "10px"},
            ),

            # Distribution + active minutes per day
            dbc.Row(
                [
                    dbc.Col([
                        html.H4("Daily Step Distribution", className="color-main"),
                        html.Div(id="comparison-dist", className="graph-section"),
                    ], width=6),
                    dbc.Col([
                        html.H4("Active Minutes per Day", className="color-main"),
                        html.Div(id="comparison-activity", className="graph-section"),
                    ], width=6),
                ],
                className="row", style={"margin-bottom": "10px"},
            ),

            # Comments + export
            dbc.Row(
                dbc.Col([
                    html.H4("Comments", className="color-main"),
                    dcc.Textarea(
                        id="comparison-comment-box",
                        placeholder="Enter any notes or observations about this comparison...",
                        className="comment-box",
                        style={"width": "100%", "height": "120px"},
                    ),
                    html.Div(
                        [
                            dbc.Button(
                                [html.I(className="fas fa-file-pdf"), " Download Page (PDF)"],
                                id="comparison-pdf-btn", color="primary", outline=True,
                                className="me-2", disabled=True,
                            ),
                            dbc.Button(
                                [html.I(className="fas fa-file-csv"), " Download Values (CSV)"],
                                id="comparison-values-btn", color="primary", outline=True,
                                disabled=True,
                            ),
                            dcc.Download(id="comparison-values-csv"),
                            html.Div(id="comparison-pdf-dummy", style={"display": "none"}),
                        ],
                        style={"margin-top": "10px", "text-align": "right"},
                        className="export-bar",
                    ),
                ], width=12),
                className="row", style={"margin-top": "10px", "margin-bottom": "10px"},
            ),
        ],
        fluid=True,
        style={"padding": "40px"},
    )
])


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

def _no_data(msg="Upload two or more files to compare."):
    return dbc.Row(dbc.Col(html.Div(msg, className="flex-container")))


def _prepared(series):
    """Load the stored series into (series_dict, dataframe) pairs."""
    return load_series(series)


@app.callback(
    Output("comparison-series", "data"),
    Output("comparison-file-status", "children"),
    Output("comparison-align", "value"),
    Input("comparison-upload", "contents"),
    State("comparison-upload", "filename"),
    prevent_initial_call=True,
)
def store_series(contents, filenames):
    """Parse uploads into series, list them, and auto-pick the align mode."""
    if not contents:
        return None, None, "calendar"

    series = parse_series(contents, filenames)
    if not series:
        return None, html.Div("No valid data files found.",
                              style={"color": "indianred", "margin-left": "15px"}), "calendar"

    items = []
    for i, s in enumerate(series):
        start = pd.to_datetime(s["start"]).strftime("%b %d, %Y")
        end = pd.to_datetime(s["end"]).strftime("%b %d, %Y")
        detail = f"Participant {s['pid']}"
        if s["quarter"] is not None:
            detail += f", Quarter {s['quarter']}"
        if s["device"] is not None:
            detail += f", Device {s['device']}"
        items.append(html.Li([
            html.Span("● ", style={"color": series_color(i)}),
            html.B(s["label"]),
            html.Span(f"  — {detail}  ({start} → {end})", className="color-sub"),
        ]))

    pids = {s["pid"] for s in series}
    if len(pids) == 1:
        heading = f"Participant {next(iter(pids))} — {len(series)} series loaded:"
    else:
        heading = f"{len(series)} series loaded across {len(pids)} participants:"

    status = html.Div([
        html.Div(heading,
                 style={"color": "steelblue", "font-weight": "bold", "margin-left": "15px"}),
        html.Ul(items),
    ])

    # Auto-pick: calendar when it's one participant, elapsed when comparing people.
    align = "calendar" if len(pids) == 1 else "elapsed"

    return series, status, align


@app.callback(
    Output("comparison-banner", "children"),
    Output("comparison-pdf-btn", "disabled"),
    Output("comparison-values-btn", "disabled"),
    Input("comparison-series", "data"),
)
def update_banner(series):
    """Guardrail banners + enable exports once there is data."""
    if not series:
        return None, True, True

    loaded = load_series(series)
    msgs = []

    pids = {s["pid"] for s in series}
    if len(pids) > 1:
        msgs.append(html.Div(
            f"Comparing {len(pids)} different participants.",
            style={"color": "steelblue"}))

    ratio = disparity_ratio(loaded)
    if ratio >= DISPARITY_THRESHOLD:
        msgs.append(html.Div(
            f"Datasets differ substantially in length (×{ratio:.1f}); "
            "per-day rates give the fairest comparison.",
            style={"color": "darkorange"}))

    if len(series) < 2:
        msgs.append(html.Div("Add at least one more file to compare.",
                             style={"color": "indianred"}))

    disabled = len(series) < 1
    return html.Div(msgs, style={"margin-left": "15px"}), disabled, disabled


@app.callback(
    Output("comparison-metrics", "children"),
    [Input("comparison-series", "data"),
     Input("comparison-active-slider", "value")],
)
def update_metrics(series, threshold):
    """Per-series summary metrics table."""
    if not series:
        return _no_data()

    loaded = _prepared(series)

    header = ["Series", "Total Days with Data", "Total Steps", "Avg Steps/Day", "Avg Active Min/Day"]

    rows = []
    for i, (s, df) in enumerate(loaded):
        m = series_metrics(df, threshold)
        rows.append(html.Tr([
            html.Td([html.Span("● ", style={"color": series_color(i)}), s["label"]]),
            html.Td(m["days_with_data"]),
            html.Td(m["total_steps"]),
            html.Td(m["steps_per_day"]),
            html.Td(m["active_min_per_day"]),
        ]))

    return dbc.Table(
        [html.Thead(html.Tr([html.Th(h) for h in header])), html.Tbody(rows)],
        bordered=False, hover=True, responsive=True, striped=True,
    )


@app.callback(
    Output("comparison-direct", "children"),
    [Input("comparison-series", "data"),
     Input("comparison-direct-tab", "active_tab")],
)
def update_direct(series, active_tab):
    """Overlaid step-counts on a shared calendar axis, gaps preserved."""
    if not series:
        return _no_data()

    loaded = _prepared(series)
    fig = go.Figure()

    for i, (s, df) in enumerate(loaded):
        color = series_color(i)
        if active_tab == "direct-raw":
            fig.add_trace(go.Scatter(
                x=df["timestamp"], y=df["steps"], mode="lines",
                name=s["label"], line={"color": color},
            ))
        else:
            freq = "h" if active_tab == "direct-hourly" else "D"
            resampled = resample_with_gaps(df, freq)
            fig.add_trace(go.Scatter(
                x=resampled.index, y=resampled.values, mode="lines+markers",
                name=s["label"], line={"color": color},
                connectgaps=False,
            ))

    fig.update_layout(
        xaxis_title="Date", yaxis_title="Steps",
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
        paper_bgcolor="white",
        hoverlabel={"bgcolor": "white", "font_size": 14, "font_family": "Roboto"},
        legend={"orientation": "h", "y": -0.2},
    )
    return dcc.Graph(figure=fig)


@app.callback(
    Output("comparison-trend", "children"),
    [Input("comparison-series", "data"),
     Input("comparison-align", "value"),
     Input("comparison-active-slider", "value")],
)
def update_trend(series, align, threshold):
    """Weekly-binned active minutes per day over time, one line per series."""
    if not series:
        return _no_data()

    loaded = _prepared(series)
    fig = go.Figure()
    bin_days = 7  # weekly bins

    for i, (s, df) in enumerate(loaded):
        # Weight each interval by active minutes (5 if active, else 0) so the
        # trajectory averages to active minutes per day within each week.
        work = df.copy()
        work["steps"] = np.where(work["steps"] >= threshold, 5, 0)
        x, y = trajectory(work, align, bin_days)

        fig.add_trace(go.Scatter(
            x=x, y=list(y), mode="lines+markers", name=s["label"],
            line={"color": series_color(i)}, connectgaps=False,
        ))

    x_title = "Days since start" if align == "elapsed" else "Date"
    fig.update_layout(
        xaxis_title=x_title, yaxis_title="Active min / day",
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
        paper_bgcolor="white",
        hoverlabel={"bgcolor": "white", "font_size": 14, "font_family": "Roboto"},
        legend={"orientation": "h", "y": -0.2},
    )
    return dcc.Graph(figure=fig)


@app.callback(
    Output("comparison-tod", "children"),
    Input("comparison-series", "data"),
)
def update_tod(series):
    """Average steps in each hour of day, overlaid (length-robust)."""
    if not series:
        return _no_data()

    loaded = _prepared(series)
    fig = go.Figure()
    for i, (s, df) in enumerate(loaded):
        prof = hour_of_day_profile(df).reindex(range(24))
        fig.add_trace(go.Scatter(
            x=list(prof.index), y=list(prof.values), mode="lines",
            name=s["label"], line={"color": series_color(i)},
        ))
    fig.update_layout(
        xaxis_title="Hour of Day", yaxis_title="Avg Steps in Hour",
        margin={"l": 20, "r": 20, "t": 20, "b": 20}, paper_bgcolor="white",
        legend={"orientation": "h", "y": -0.2},
    )
    return dcc.Graph(figure=fig)


@app.callback(
    Output("comparison-dow", "children"),
    Input("comparison-series", "data"),
)
def update_dow(series):
    """Average steps on each weekday, overlaid (length-robust)."""
    if not series:
        return _no_data()

    loaded = _prepared(series)
    fig = go.Figure()
    for i, (s, df) in enumerate(loaded):
        prof = day_of_week_profile(df).reindex(range(7))
        fig.add_trace(go.Scatter(
            x=WEEKDAY_LABELS, y=list(prof.values), mode="lines",
            name=s["label"], line={"color": series_color(i)},
        ))
    fig.update_layout(
        xaxis_title="Day of Week", yaxis_title="Avg Steps per Day",
        margin={"l": 20, "r": 20, "t": 20, "b": 20}, paper_bgcolor="white",
        legend={"orientation": "h", "y": -0.2},
    )
    return dcc.Graph(figure=fig)


@app.callback(
    Output("comparison-dist", "children"),
    Input("comparison-series", "data"),
)
def update_dist(series):
    """Distribution of daily step totals, one box per series."""
    if not series:
        return _no_data()

    loaded = _prepared(series)
    fig = go.Figure()
    for i, (s, df) in enumerate(loaded):
        daily = resample_with_gaps(df, "D").dropna()
        fig.add_trace(go.Box(
            y=list(daily.values), name=s["label"],
            marker_color=series_color(i), boxpoints="outliers",
        ))
    fig.update_layout(
        yaxis_title="Steps per Day", showlegend=False,
        margin={"l": 20, "r": 20, "t": 20, "b": 20}, paper_bgcolor="white",
    )
    return dcc.Graph(figure=fig)


@app.callback(
    Output("comparison-activity", "children"),
    [Input("comparison-series", "data"),
     Input("comparison-active-slider", "value")],
)
def update_activity(series, threshold):
    """Average active minutes per day, one bar per series."""
    if not series:
        return _no_data()

    loaded = _prepared(series)
    labels, values, colors = [], [], []
    for i, (s, df) in enumerate(loaded):
        m = series_metrics(df, threshold)
        labels.append(s["label"])
        values.append(m["active_min_per_day"])
        colors.append(series_color(i))

    fig = go.Figure(go.Bar(x=labels, y=values, marker_color=colors))
    fig.update_layout(
        yaxis_title="Active Min / Day",
        margin={"l": 20, "r": 20, "t": 20, "b": 20}, paper_bgcolor="white",
    )
    return dcc.Graph(figure=fig)


# Trigger the browser print dialog so the whole page can be saved as a PDF
app.clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks) { window.print(); }
        return "";
    }
    """,
    Output("comparison-pdf-dummy", "children"),
    Input("comparison-pdf-btn", "n_clicks"),
    prevent_initial_call=True,
)


@app.callback(
    Output("comparison-values-csv", "data"),
    Input("comparison-values-btn", "n_clicks"),
    [State("comparison-series", "data"),
     State("comparison-active-slider", "value"),
     State("comparison-comment-box", "value")],
    prevent_initial_call=True,
)
def download_values(n_clicks, series, threshold, comment):
    """Export the per-series metrics + comment as a CSV."""
    if not n_clicks or not series:
        return None

    loaded = _prepared(series)
    records = []
    for s, df in loaded:
        m = series_metrics(df, threshold)
        records.append({
            "Series": s["label"],
            "Participant": s["pid"],
            "Quarter": s["quarter"] if s["quarter"] is not None else "",
            "Device": s["device"] if s["device"] is not None else "",
            "Start": pd.to_datetime(s["start"]).strftime("%Y-%m-%d %H:%M"),
            "End": pd.to_datetime(s["end"]).strftime("%Y-%m-%d %H:%M"),
            "Days with data": m["days_with_data"],
            "Total steps": m["total_steps"],
            "Steps/day": m["steps_per_day"],
            "Active min/day": m["active_min_per_day"],
            "Active step threshold": threshold,
            "Comment": (comment or "").replace("\r", " ").replace("\n", " ").strip(),
        })

    out = pd.DataFrame(records)
    export_name = f"comparison_summary_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
    return dcc.send_data_frame(out.to_csv, export_name, index=False)

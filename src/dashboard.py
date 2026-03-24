"""
Supply Chain Optimizer — Dash Dashboard
World-class dark industrial design | 3PL Intelligence Platform
Run: python src/dashboard.py
"""

import os, json
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import sys

# BASE defined early so everything can use it
BASE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.join(BASE, '..', 'data', 'processed')
RAW  = os.path.join(BASE, '..', 'data', 'raw')

# Auto-generate route map at startup
try:
    sys.path.insert(0, BASE)
    from route_map import build_route_map
    _assets = os.path.join(BASE, 'assets')
    os.makedirs(_assets, exist_ok=True)
    _map_out = os.path.join(_assets, 'route_map.html')
    if not os.path.exists(_map_out):
        print('Generating route map...')
        build_route_map(output_path=_map_out)
        print('Route map generated')
except Exception as _e:
    print(f'Route map skipped: {_e}')



def load(name):
    path = os.path.join(PROC, name)
    if os.path.exists(path):
        df = pd.read_csv(path)
        if not df.empty:
            return df
    rpath = os.path.join(RAW, name)
    if os.path.exists(rpath):
        df = pd.read_csv(rpath)
        if not df.empty:
            return df
    return pd.DataFrame()

ships   = load("shipments_features.csv")
if ships.empty:
    ships = load("shipments_3yr.csv")

monthly = load("monthly_kpis.csv")
routes  = load("route_performance.csv")
wh_ops  = load("warehouse_ops.csv")
if wh_ops.empty:
    wh_ops = load("warehouse_ops_3yr.csv")

# ── Fallback synthetic data if CSVs not generated yet ─────────────────────────
if monthly.empty:
    months = pd.date_range("2022-01-01", "2024-12-01", freq="MS")
    np.random.seed(42)
    monthly = pd.DataFrame({
        "year":            [d.year  for d in months],
        "month":           [d.month for d in months],
        "total_shipments": np.random.randint(280, 420, len(months)),
        "on_time_rate":    np.random.uniform(74, 95, len(months)).round(1),
        "avg_transit_hrs": np.random.uniform(7, 18,  len(months)).round(2),
        "avg_delay_hrs":   np.random.uniform(0.2, 3.5, len(months)).round(2),
        "total_revenue":   np.random.uniform(380000, 620000, len(months)).round(2),
        "delay_rate":      np.random.uniform(5, 26, len(months)).round(1),
    })

if routes.empty:
    routes = pd.DataFrame([
        {"route_id":"R001","origin":"Johannesburg","destination":"Cape Town",      "distance_km":1400,"total_shipments":680,"efficiency_pct":94,"avg_delay_hrs":0.4,"total_revenue":820000,"delay_rate":6},
        {"route_id":"R002","origin":"Johannesburg","destination":"Durban",         "distance_km":560, "total_shipments":720,"efficiency_pct":78,"avg_delay_hrs":1.8,"total_revenue":410000,"delay_rate":22},
        {"route_id":"R003","origin":"Cape Town",   "destination":"Port Elizabeth", "distance_km":770, "total_shipments":390,"efficiency_pct":88,"avg_delay_hrs":0.9,"total_revenue":510000,"delay_rate":12},
        {"route_id":"R004","origin":"Durban",      "destination":"Bloemfontein",   "distance_km":620, "total_shipments":310,"efficiency_pct":65,"avg_delay_hrs":2.9,"total_revenue":370000,"delay_rate":35},
        {"route_id":"R005","origin":"Johannesburg","destination":"Port Elizabeth",  "distance_km":1060,"total_shipments":440,"efficiency_pct":71,"avg_delay_hrs":2.1,"total_revenue":690000,"delay_rate":29},
        {"route_id":"R006","origin":"Johannesburg","destination":"Bloemfontein",   "distance_km":400, "total_shipments":520,"efficiency_pct":85,"avg_delay_hrs":1.1,"total_revenue":290000,"delay_rate":15},
    ])

# ── Colours ───────────────────────────────────────────────────────────────────
C = {
    "bg":      "#060a0f",
    "surface": "#0a0e14",
    "border":  "#1a2535",
    "accent":  "#e8770a",
    "green":   "#4ade80",
    "blue":    "#60a5fa",
    "purple":  "#a78bfa",
    "red":     "#f87171",
    "text":    "#e2e8f0",
    "muted":   "#64748b",
}

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Share Tech Mono, monospace", color=C["muted"], size=11),
    xaxis=dict(gridcolor="#0f1820", linecolor=C["border"], tickfont=dict(color=C["muted"])),
    yaxis=dict(gridcolor="#0f1820", linecolor=C["border"], tickfont=dict(color=C["muted"])),
    margin=dict(l=40, r=20, t=40, b=40),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=C["muted"])),
    hoverlabel=dict(bgcolor="#0a0e14", bordercolor=C["accent"],
                    font=dict(family="Share Tech Mono", color=C["text"])),
)

# ── Truck SVG ─────────────────────────────────────────────────────────────────
TRUCK_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 60" width="110" height="55">
  <rect x="2" y="14" width="72" height="30" rx="2" fill="#0d1520" stroke="#e8770a" stroke-width="1.5"/>
  <rect x="74" y="20" width="36" height="24" rx="3" fill="#111c2a" stroke="#e8770a" stroke-width="1.5"/>
  <path d="M76 20 Q78 10 95 10 L110 20 Z" fill="#0d1520" stroke="#e8770a" stroke-width="1"/>
  <rect x="96" y="14" width="14" height="10" rx="1" fill="#60a5fa" opacity="0.6"/>
  <rect x="108" y="22" width="4" height="12" rx="1" fill="#e8770a" opacity="0.8"/>
  <line x1="20" y1="14" x2="20" y2="44" stroke="#1a2535" stroke-width="1"/>
  <line x1="38" y1="14" x2="38" y2="44" stroke="#1a2535" stroke-width="1"/>
  <line x1="56" y1="14" x2="56" y2="44" stroke="#1a2535" stroke-width="1"/>
  <circle cx="20"  cy="47" r="7" fill="#060a0f" stroke="#e8770a" stroke-width="2"/>
  <circle cx="20"  cy="47" r="3" fill="#e8770a" opacity="0.6"/>
  <circle cx="50"  cy="47" r="7" fill="#060a0f" stroke="#e8770a" stroke-width="2"/>
  <circle cx="50"  cy="47" r="3" fill="#e8770a" opacity="0.6"/>
  <circle cx="88"  cy="47" r="7" fill="#060a0f" stroke="#e8770a" stroke-width="2"/>
  <circle cx="88"  cy="47" r="3" fill="#e8770a" opacity="0.6"/>
  <circle cx="104" cy="47" r="7" fill="#060a0f" stroke="#e8770a" stroke-width="2"/>
  <circle cx="104" cy="47" r="3" fill="#e8770a" opacity="0.6"/>
  <rect x="73" y="38" width="3" height="8" fill="#e8770a" opacity="0.5"/>
  <rect x="107" y="4" width="3" height="10" rx="1" fill="#4a5568"/>
  <ellipse cx="108.5" cy="4" rx="2" ry="1.5" fill="#e8770a" opacity="0.4"/>
  <rect x="113" y="25" width="4" height="5" rx="1" fill="#fbbf24" opacity="0.9"/>
  <rect x="3" y="15" width="6" height="3" rx="1" fill="#fbbf24" opacity="0.5"/>
</svg>
"""

# ── KPI Card ──────────────────────────────────────────────────────────────────
def kpi_card(label, value, unit, delta_val, delta_label, accent):
    sign   = "▲" if delta_val > 0 else "▼"
    dcolor = C["green"] if delta_val > 0 else C["red"]
    return html.Div([
        html.Div(label, style={
            "fontFamily":"Share Tech Mono,monospace","fontSize":10,
            "color":C["muted"],"letterSpacing":3,"textTransform":"uppercase","marginBottom":8
        }),
        html.Div([
            html.Span(value, style={"fontFamily":"Bebas Neue,sans-serif","fontSize":44,
                                    "color":accent,"lineHeight":"1"}),
            html.Span(unit,  style={"fontFamily":"Share Tech Mono,monospace","fontSize":14,
                                    "color":f"{accent}99","marginLeft":6}),
        ]),
        html.Div(f"{sign} {abs(delta_val)}% {delta_label}", style={
            "fontFamily":"Share Tech Mono,monospace","fontSize":10,"color":dcolor,
            "background":"#0a0e14","border":f"1px solid {dcolor}44",
            "borderRadius":2,"padding":"3px 8px","display":"inline-block","marginTop":8,
        }),
    ], style={
        "background":f"linear-gradient(135deg, {C['surface']}, #111820)",
        "border":f"1px solid {accent}33","borderTop":f"3px solid {accent}",
        "borderRadius":3,"padding":"20px 22px","position":"relative",
        "boxShadow":f"0 4px 20px {accent}11",
    })

# ── Chart Builders ────────────────────────────────────────────────────────────
def make_ontime_chart():
    df = monthly.copy()
    df["period"] = df["year"].astype(str) + "-" + df["month"].astype(str).str.zfill(2)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["period"], y=df["on_time_rate"], name="On-Time %",
        fill="tozeroy", line=dict(color=C["green"], width=2.5),
        fillcolor="rgba(74,222,128,0.08)",
        hovertemplate="<b>%{x}</b><br>On-Time: %{y:.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=df["period"], y=df["delay_rate"], name="Delay %",
        fill="tozeroy", line=dict(color=C["red"], width=2),
        fillcolor="rgba(248,113,113,0.08)",
        hovertemplate="<b>%{x}</b><br>Delay: %{y:.1f}%<extra></extra>",
    ))
    fig.add_hline(y=90, line_dash="dash", line_color=C["accent"],
                  annotation_text="TARGET 90%", annotation_font_color=C["accent"])
    fig.update_layout(**PLOTLY_LAYOUT,
        title=dict(text="DELIVERY PERFORMANCE — 3 YEAR TREND",
                   font=dict(family="Bebas Neue", size=16, color=C["text"]), x=0.01))
    return fig

def make_route_bar():
    df = routes.sort_values("efficiency_pct").copy()
    colors = [C["red"] if e < 75 else C["accent"] if e < 88 else C["green"]
              for e in df["efficiency_pct"]]
    fig = go.Figure(go.Bar(
        x=df["efficiency_pct"],
        y=df["origin"].str[:3] + "→" + df["destination"].str[:3],
        orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        hovertemplate="<b>%{y}</b><br>Efficiency: %{x}%<extra></extra>",
        text=[f"{e}%" for e in df["efficiency_pct"]],
        textposition="outside",
        textfont=dict(family="Share Tech Mono", color=C["text"], size=11),
    ))
    fig.update_layout(**PLOTLY_LAYOUT,
        title=dict(text="ROUTE EFFICIENCY MATRIX",
                   font=dict(family="Bebas Neue", size=16, color=C["text"]), x=0.01),
        xaxis_range=[0, 105])
    return fig

def make_delay_heatmap():
    if not ships.empty and "day_of_week" in ships.columns and "departure_hour" in ships.columns:
        pivot  = ships.groupby(["day_of_week","departure_hour"])["is_delayed"].mean().unstack(fill_value=0)
        z      = pivot.reindex(range(7)).fillna(0).values * 100
        hours_x = list(range(24))
    else:
        np.random.seed(1)
        z = np.random.uniform(5, 35, (7, 24))
        z[0:5, 7:10]  += 12
        z[0:5, 16:19] += 10
        hours_x = list(range(24))

    days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    fig  = go.Figure(go.Heatmap(
        z=z, x=[f"{h:02d}:00" for h in hours_x], y=days,
        colorscale=[[0,"#060a0f"],[0.4,"#1a2535"],[0.7,"#e8770a"],[1,"#f87171"]],
        showscale=True,
        colorbar=dict(tickfont=dict(family="Share Tech Mono", color=C["muted"])),
        hovertemplate="<b>%{y} %{x}</b><br>Delay Rate: %{z:.1f}%<extra></extra>",
    ))
    fig.update_layout(**PLOTLY_LAYOUT,
        title=dict(text="DELAY HEATMAP — DAY × HOUR",
                   font=dict(family="Bebas Neue", size=16, color=C["text"]), x=0.01))
    return fig

def make_warehouse_chart():
    if not wh_ops.empty and "hour" in wh_ops.columns:
        hourly = wh_ops.groupby("hour")["orders_processed"].mean().reset_index()
        hours  = hourly["hour"].tolist()
        orders = hourly["orders_processed"].tolist()
    else:
        hours  = list(range(24))
        orders = [5,4,3,3,4,8,15,55,75,85,95,88,90,100,98,88,78,65,48,35,22,14,8,5]

    capacity_line = [40] * 24
    colors = [C["red"] if o > 40 else C["accent"] if o > 25 else C["blue"] for o in orders]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[f"{h:02d}:00" for h in hours], y=orders,
        marker=dict(color=colors, line=dict(width=0)),
        name="Orders Processed",
        hovertemplate="<b>%{x}</b><br>Orders: %{y:.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=[f"{h:02d}:00" for h in hours], y=capacity_line,
        line=dict(color=C["green"], width=2, dash="dash"),
        name="Capacity Limit",
    ))
    fig.update_layout(**PLOTLY_LAYOUT,
        title=dict(text="WAREHOUSE HOURLY THROUGHPUT",
                   font=dict(family="Bebas Neue", size=16, color=C["text"]), x=0.01),
        barmode="overlay")
    return fig

def make_revenue_area():
    df = monthly.copy()
    df["period"] = df["year"].astype(str) + "-" + df["month"].astype(str).str.zfill(2)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["period"], y=df["total_revenue"] / 1000, name="Revenue (K USD)",
        fill="tozeroy", line=dict(color=C["blue"], width=2.5),
        fillcolor="rgba(96,165,250,0.08)",
        hovertemplate="<b>%{x}</b><br>Revenue: $%{y:.0f}K<extra></extra>",
    ))
    fig.update_layout(**PLOTLY_LAYOUT,
        title=dict(text="MONTHLY REVENUE TREND",
                   font=dict(family="Bebas Neue", size=16, color=C["text"]), x=0.01))
    return fig

def make_scatter_delay():
    fig = go.Figure()
    for _, row in routes.iterrows():
        c = (C["green"] if row["efficiency_pct"] >= 88
             else C["accent"] if row["efficiency_pct"] >= 75
             else C["red"])
        fig.add_trace(go.Scatter(
            x=[row["distance_km"]], y=[row["delay_rate"]],
            mode="markers+text",
            marker=dict(size=row["total_shipments"] / 80, color=c, opacity=0.85,
                        line=dict(width=1, color="#060a0f")),
            text=[f"{row['origin'][:3]}→{row['destination'][:3]}"],
            textfont=dict(family="Share Tech Mono", color=C["text"], size=10),
            textposition="top center",
            name=f"{row['origin']}→{row['destination']}",
            hovertemplate=(
                f"<b>{row['origin']} → {row['destination']}</b><br>"
                f"Distance: {row['distance_km']}km<br>"
                f"Delay Rate: {row['delay_rate']}%<br>"
                f"Shipments: {row['total_shipments']:,}<extra></extra>"
            ),
        ))
    fig.update_layout(**PLOTLY_LAYOUT,
        title=dict(text="DISTANCE vs DELAY RATE (bubble = volume)",
                   font=dict(family="Bebas Neue", size=16, color=C["text"]), x=0.01),
        showlegend=False,
        xaxis_title="Distance (km)", yaxis_title="Delay Rate (%)")
    return fig

def make_feature_importance():
    features_path = os.path.join(BASE, "..", "models", "feature_importance.csv")
    if os.path.exists(features_path):
        fi = pd.read_csv(features_path).head(10)
    else:
        fi = pd.DataFrame({
            "feature":    ["weather_score","traffic_index","route_complexity","driver_experience",
                           "departure_hour","day_of_week","distance_km","is_holiday","weight_kg","month"],
            "importance": [0.24, 0.19, 0.16, 0.14, 0.09, 0.07, 0.05, 0.03, 0.02, 0.01],
        })
    colors = [C["accent"] if i == 0 else C["blue"] for i in range(len(fi))]
    fig = go.Figure(go.Bar(
        x=fi["importance"], y=fi["feature"],
        orientation="h", marker=dict(color=colors),
        hovertemplate="<b>%{y}</b><br>Importance: %{x:.4f}<extra></extra>",
        text=[f"{v:.3f}" for v in fi["importance"]],
        textposition="outside",
        textfont=dict(family="Share Tech Mono", color=C["text"], size=10),
    ))
    fig.update_layout(**PLOTLY_LAYOUT,
        title=dict(text="XGBOOST FEATURE IMPORTANCE",
                   font=dict(family="Bebas Neue", size=16, color=C["text"]), x=0.01))
    return fig

# ── Computed KPIs ─────────────────────────────────────────────────────────────
last3       = monthly.tail(3)
prev3       = monthly.iloc[-6:-3]
avg_ot      = round(last3["on_time_rate"].mean(), 1)
prev_ot     = round(prev3["on_time_rate"].mean(), 1)
ot_delta    = round(avg_ot - prev_ot, 1)
avg_delay   = round(last3["avg_delay_hrs"].mean(), 2)
prev_delay  = round(prev3["avg_delay_hrs"].mean(), 2)
delay_delta = round(((avg_delay - prev_delay) / max(prev_delay, 0.01)) * -100, 1)
total_ships = int(monthly["total_shipments"].sum())
rev_k       = round(monthly["total_revenue"].sum() / 1000, 0)

# ── App Init ──────────────────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="Supply Chain Optimizer | 3PL Intelligence",
)


app.index_string = '''<!DOCTYPE html>
<html>
  <head>{%metas%}<title>{%title%}</title>{%favicon%}{%css%}
  <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Share+Tech+Mono&display=swap" rel="stylesheet">
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{background:#060a0f;color:#e2e8f0;font-family:"Share Tech Mono",monospace}
    ::-webkit-scrollbar{width:4px}
    ::-webkit-scrollbar-thumb{background:#e8770a55}
    .tab-content{animation:fadein 0.35s ease}
    @keyframes fadein{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
    @keyframes pulse{0%,100%{opacity:1}50%{opacity:0.3}}
    @keyframes scanline{0%{top:-2px}100%{top:100vh}}
    .kpi-row{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px}
    .chart-card{background:#0a0e14;border:1px solid #1a2535;border-radius:3px;padding:20px;margin-bottom:20px}
    .grid-2{display:grid;grid-template-columns:1fr 1fr;gap:20px}
    .section-title{font-family:"Bebas Neue",sans-serif;font-size:13px;color:#e8770a;
                   letter-spacing:3px;text-transform:uppercase;margin-bottom:4px}
    .section-sub{font-size:10px;color:#4a5568;letter-spacing:2px;margin-bottom:16px}
    .tab-btn:hover{background:#0d1520 !important;color:#e8770a !important}
  </style>
  </head>
  <body>{%app_entry%}<footer>{%config%}{%scripts%}{%renderer%}</footer></body>
</html>'''

# ── Header ────────────────────────────────────────────────────────────────────
header = html.Div([
    html.Div(style={
        "position":"fixed","top":0,"left":0,"right":0,"height":"2px","zIndex":9999,
        "pointerEvents":"none",
        "background":"linear-gradient(to bottom,transparent,rgba(232,119,10,0.2),transparent)",
        "animation":"scanline 10s linear infinite",
    }),
    html.Div([
        html.Div([
            html.Div([
                html.Div("3PL", style={
                    "width":38,"height":38,"background":"#e8770a","borderRadius":2,
                    "display":"flex","alignItems":"center","justifyContent":"center",
                    "fontSize":16,"fontFamily":"Bebas Neue,sans-serif","color":"#060a0f","fontWeight":"bold",
                }),
                html.Div([
                    html.Div("SUPPLY CHAIN OPTIMIZER", style={
                        "fontFamily":"Bebas Neue,sans-serif","fontSize":22,"letterSpacing":4,"color":"#e2e8f0",
                    }),
                    html.Div("3PL INTELLIGENCE PLATFORM  ·  LOGISTICS ANALYTICS SUITE  ·  v3.0", style={
                        "fontSize":9,"color":"#4a5568","letterSpacing":2,
                    }),
                ]),
            ], style={"display":"flex","alignItems":"center","gap":14}),
        ], style={"display":"flex","alignItems":"center","gap":24}),

        html.Div([
            dcc.Markdown(TRUCK_SVG, dangerously_allow_html=True),
        ], style={"display":"flex","alignItems":"center","justifyContent":"center","flex":1}),

        html.Div([
            html.Div([
                html.Div(style={
                    "width":8,"height":8,"borderRadius":"50%","background":"#4ade80",
                    "animation":"pulse 2s infinite","marginRight":6,"display":"inline-block",
                }),
                html.Span("LIVE", style={"color":"#4ade80","fontSize":10,"letterSpacing":2}),
            ], style={"display":"flex","alignItems":"center","marginBottom":4}),
            html.Div(f"TOTAL SHIPMENTS: {total_ships:,}",
                     style={"fontSize":10,"color":"#4a5568","letterSpacing":1}),
            html.Div(f"REVENUE: ${rev_k:,.0f}K",
                     style={"fontSize":10,"color":"#4a5568","letterSpacing":1}),
        ]),
    ], style={
        "display":"flex","alignItems":"center","justifyContent":"space-between",
        "maxWidth":1600,"margin":"0 auto","padding":"0 32px",
    }),
], style={
    "background":"linear-gradient(90deg,#060a0f,#0a0e14,#060a0f)",
    "borderBottom":"1px solid #e8770a33","height":68,
    "position":"sticky","top":0,"zIndex":100,
})

# ── Nav Tabs ──────────────────────────────────────────────────────────────────
NAV_TABS = [
    ("overview",  "OVERVIEW"),
    ("routes",    "ROUTE ANALYSIS"),
    ("warehouse", "WAREHOUSE"),
    ("ml_model",  "ML MODEL"),
    ("scenario",  "WHAT-IF"),
]

nav = html.Div([
    html.Div([
        html.Button(label, id=f"tab-{tid}", n_clicks=0, className="tab-btn", style={
            "background":"transparent","border":"none","cursor":"pointer","padding":"16px 20px",
            "fontFamily":"Share Tech Mono,monospace","fontSize":11,"letterSpacing":2,
            "color":"#4a5568","transition":"all 0.2s","borderBottom":"2px solid transparent",
        }) for tid, label in NAV_TABS
    ], style={"display":"flex","maxWidth":1600,"margin":"0 auto","padding":"0 32px"}),
    dcc.Store(id="active-tab", data="overview"),
], style={"background":"#0a0e14","borderBottom":"1px solid #1a2535"})

# ── Page Bodies ───────────────────────────────────────────────────────────────
def overview_body():
    return html.Div([
        html.Div([
            kpi_card("ON-TIME DELIVERY",  f"{avg_ot}",          "%",  ot_delta,    "vs prev quarter", C["green"]),
            kpi_card("AVG DELAY",         f"{avg_delay}",        "hrs",delay_delta, "improvement",     C["blue"]),
            kpi_card("TOTAL ROUTES",      f"{len(routes)}",      "",   2.1,         "active",          C["accent"]),
            kpi_card("REVENUE",           f"${rev_k/1000:.1f}M", "",   5.3,         "YoY growth",      C["purple"]),
        ], className="kpi-row"),
        html.Div([dcc.Graph(figure=make_ontime_chart(),  config={"displayModeBar":False})], className="chart-card"),
        html.Div([
            html.Div([dcc.Graph(figure=make_revenue_area(),   config={"displayModeBar":False})], className="chart-card"),
            html.Div([dcc.Graph(figure=make_delay_heatmap(),  config={"displayModeBar":False})], className="chart-card"),
        ], className="grid-2"),
    ])

def routes_body():
    # Check if folium map exists
    map_path = os.path.join(BASE, "assets", "route_map.html")
    map_exists = os.path.exists(map_path)

    return html.Div([
        # ── Folium Interactive Map ─────────────────────────────────────────
        html.Div([
            html.Div("LIVE INTERACTIVE ROUTE MAP", className="section-title"),
            html.Div("SOUTH AFRICA DELIVERY NETWORK · ANIMATED ROUTES · COLOUR = EFFICIENCY",
                     className="section-sub"),
            html.Iframe(
                src="/assets/route_map.html",
                style={
                    "width":        "100%",
                    "height":       "480px",
                    "border":       f"1px solid {C['border']}",
                    "borderRadius": "3px",
                    "display":      "block",
                }
            ) if map_exists else html.Div([
                html.Div("⚠  Route map not generated yet.",
                         style={"color": C["accent"], "fontSize": 12,
                                "fontFamily": "Share Tech Mono,monospace", "marginBottom": 8}),
                html.Div("Run:  python src/route_map.py  to generate the interactive map.",
                         style={"color": C["muted"], "fontSize": 11,
                                "fontFamily": "Share Tech Mono,monospace"}),
            ], style={"padding": 24, "background": "#060a0f",
                      "border": f"1px solid {C['border']}", "borderRadius": 3}),
        ], className="chart-card"),

        # ── Charts Row ─────────────────────────────────────────────────────
        html.Div([
            html.Div([dcc.Graph(figure=make_route_bar(),     config={"displayModeBar":False})],
                     className="chart-card"),
            html.Div([dcc.Graph(figure=make_scatter_delay(), config={"displayModeBar":False})],
                     className="chart-card"),
        ], className="grid-2"),

        # ── Route Performance Table ────────────────────────────────────────
        html.Div([
            html.Div("ROUTE PERFORMANCE TABLE", className="section-title"),
            html.Div("FULL 3PL NETWORK · RANKED BY EFFICIENCY", className="section-sub"),
            html.Table([
                html.Thead(html.Tr([
                    html.Th(col, style={
                        "padding":"10px 14px","color":C["accent"],"fontSize":10,
                        "letterSpacing":2,"borderBottom":f"1px solid {C['border']}",
                        "textAlign":"left",
                    }) for col in ["ROUTE","DISTANCE","SHIPMENTS","EFFICIENCY",
                                   "DELAY RATE","AVG DELAY","REVENUE"]
                ])),
                html.Tbody([
                    html.Tr([
                        html.Td(f"{r['origin'][:3]}→{r['destination'][:3]}",
                                style={"padding":"10px 14px",
                                       "fontFamily":"Bebas Neue,sans-serif",
                                       "fontSize":15,"color":C["text"]}),
                        html.Td(f"{r['distance_km']} km",
                                style={"padding":"10px 14px","color":C["muted"],"fontSize":11}),
                        html.Td(f"{r['total_shipments']:,}",
                                style={"padding":"10px 14px","color":C["muted"],"fontSize":11}),
                        html.Td(html.Div([
                            html.Div(style={
                                "width":  f"{r['efficiency_pct']}%",
                                "height": 6,
                                "background": C["green"] if r["efficiency_pct"] >= 88
                                              else C["accent"] if r["efficiency_pct"] >= 75
                                              else C["red"],
                                "borderRadius": 2,
                            }),
                            html.Span(f"{r['efficiency_pct']}%", style={
                                "marginLeft": 8, "fontSize": 11,
                                "color": C["green"] if r["efficiency_pct"] >= 88
                                         else C["accent"] if r["efficiency_pct"] >= 75
                                         else C["red"],
                            }),
                        ], style={"display":"flex","alignItems":"center","width":180})),
                        html.Td(f"{r['delay_rate']}%",
                                style={"padding":"10px 14px","fontSize":11,
                                       "color":C["red"] if r["delay_rate"]>20 else C["muted"]}),
                        html.Td(f"{r['avg_delay_hrs']:.1f}h",
                                style={"padding":"10px 14px","color":C["muted"],"fontSize":11}),
                        html.Td(f"${r['total_revenue']/1000:.0f}K",
                                style={"padding":"10px 14px","color":C["blue"],"fontSize":11}),
                    ], style={"borderBottom": f"1px solid {C['border']}"})
                    for _, r in routes.sort_values("efficiency_pct").iterrows()
                ]),
            ], style={"width":"100%","borderCollapse":"collapse"}),
        ], className="chart-card"),
    ])

def warehouse_body():
    return html.Div([
        html.Div([
            kpi_card("PEAK ORDERS/HR",    "102",   "",    -3.2, "vs last month", C["red"]),
            kpi_card("AVG PROCESSING",    "14.3",  "min",  6.8, "improvement",   C["green"]),
            kpi_card("STAFF UTILISATION", "78",    "%",    2.1, "efficiency",    C["blue"]),
            kpi_card("DAILY THROUGHPUT",  "1,847", "",     5.2, "orders/day",    C["accent"]),
        ], className="kpi-row"),
        html.Div([dcc.Graph(figure=make_warehouse_chart(), config={"displayModeBar":False})],
                 className="chart-card"),
        html.Div([
            html.Div([
                html.Div("⚠  BOTTLENECK ALERT: Hours 10:00–16:00 consistently exceed warehouse processing capacity.",
                         style={"color":C["red"],"fontFamily":"Share Tech Mono,monospace",
                                "fontSize":12,"marginBottom":6}),
                html.Div("RECOMMENDATION: Deploy 2 additional pickers during 10:00–14:00. Estimated throughput gain: +18%.",
                         style={"color":C["green"],"fontFamily":"Share Tech Mono,monospace","fontSize":12}),
            ], style={
                "background":"#060a0f","border":f"1px solid {C['red']}44",
                "borderLeft":f"3px solid {C['red']}","borderRadius":2,"padding":16,
            }),
        ], className="chart-card"),
    ])

def ml_body():
    metrics_path = os.path.join(BASE, "..", "models", "metrics.json")
    if os.path.exists(metrics_path):
        with open(metrics_path) as f:
            m = json.load(f)
        roc = m.get("roc_auc", 0.874)
        pr  = m.get("pr_auc",  0.812)
        cv  = m.get("cv_roc_auc_mean", 0.869)
    else:
        roc, pr, cv = 0.874, 0.812, 0.869

    return html.Div([
        html.Div([
            kpi_card("ROC-AUC",  f"{roc:.3f}", "",  1.2, "above baseline", C["green"]),
            kpi_card("PR-AUC",   f"{pr:.3f}",  "",  0.9, "above baseline", C["blue"]),
            kpi_card("CV SCORE", f"{cv:.3f}",  "",  0.5, "stable",         C["purple"]),
            kpi_card("MODEL",    "XGBoost",    "",  0,   "v2.4",           C["accent"]),
        ], className="kpi-row"),
        html.Div([
            html.Div([dcc.Graph(figure=make_feature_importance(), config={"displayModeBar":False})],
                     className="chart-card"),
            html.Div([
                html.Div("MODEL ARCHITECTURE", className="section-title"),
                html.Div("XGBOOST DELAY CLASSIFIER", className="section-sub"),
                *[html.Div([
                    html.Span(label, style={
                        "color":C["muted"],"fontSize":10,"letterSpacing":1,
                        "minWidth":160,"display":"inline-block",
                    }),
                    html.Span(val, style={
                        "color":C["accent"],"fontFamily":"Bebas Neue,sans-serif","fontSize":16,
                    }),
                ], style={
                    "borderBottom":f"1px solid {C['border']}","padding":"10px 0",
                    "display":"flex","alignItems":"center",
                }) for label, val in [
                    ("ALGORITHM",        "XGBoost Classifier"),
                    ("N ESTIMATORS",     "400"),
                    ("MAX DEPTH",        "6"),
                    ("LEARNING RATE",    "0.05"),
                    ("SUBSAMPLE",        "0.80"),
                    ("FEATURES",         "18 engineered"),
                    ("TRAINING RECORDS", "~14,000"),
                    ("TARGET",           "is_delayed (binary)"),
                    ("CLASS BALANCING",  "scale_pos_weight"),
                ]],
            ], className="chart-card"),
        ], className="grid-2"),
    ])

def scenario_body():
    return html.Div([
        html.Div("WHAT-IF SCENARIO SIMULATOR", className="section-title"),
        html.Div("ADJUST PARAMETERS · REAL-TIME OUTCOME PROJECTION",
                 className="section-sub", style={"marginBottom":20}),
        html.Div([
            html.Div([
                *[html.Div([
                    html.Div([
                        html.Span(label, style={"fontSize":10,"color":C["muted"],"letterSpacing":2}),
                        html.Span(id=f"val-{sid}", style={
                            "fontFamily":"Bebas Neue,sans-serif","fontSize":18,"color":C["accent"],
                        }),
                    ], style={"display":"flex","justifyContent":"space-between","marginBottom":6}),
                    dcc.Slider(id=f"slider-{sid}", min=mn, max=mx, step=st, value=dv,
                               marks=None, tooltip={"always_visible":False}, updatemode="drag"),
                ], style={"marginBottom":24})
                for label, sid, mn, mx, st, dv in [
                    ("FLEET SIZE (TRUCKS)",   "fleet",   20,  120,  1,  48),
                    ("ACTIVE DRIVERS",        "drivers", 50,  250,  1, 120),
                    ("WAREHOUSES",            "wh",       1,    8,  1,   3),
                    ("ROUTE RADIUS (KM)",     "radius", 100,  700, 10, 300),
                    ("PEAK STAFF MULTIPLIER", "staff",    1,    4,  1,   2),
                ]],
            ], style={
                "flex":1,"background":C["surface"],"border":f"1px solid {C['border']}",
                "borderRadius":3,"padding":24,
            }),
            html.Div([
                html.Div(id="scenario-results"),
            ], style={"flex":1,"display":"flex","flexDirection":"column","gap":12}),
        ], style={"display":"flex","gap":20}),
    ])

# ── App Layout ────────────────────────────────────────────────────────────────
app.layout = html.Div([
    header, nav,
    html.Div(id="page-body", className="tab-content",
             style={"maxWidth":1600,"margin":"0 auto","padding":"32px"}),
    html.Div([
        html.Span("SUPPLY CHAIN OPTIMIZER  ·  3PL INTELLIGENCE PLATFORM  ·  PYTHON · DASH · XGBOOST",
                  style={"fontSize":10,"color":C["muted"],"letterSpacing":2}),
        html.Span("DATA: SYNTHETIC 3-YR DATASET  ·  ROUTES: SOUTH AFRICA",
                  style={"fontSize":10,"color":C["muted"],"letterSpacing":1}),
    ], style={
        "borderTop":f"1px solid {C['border']}","padding":"16px 32px",
        "display":"flex","justifyContent":"space-between",
        "maxWidth":1600,"margin":"0 auto",
    }),
], style={"minHeight":"100vh","background":C["bg"]})

# ── Callbacks ─────────────────────────────────────────────────────────────────
@app.callback(Output("page-body", "children"), Input("active-tab", "data"))
def render_tab(tab):
    if tab == "routes":    return routes_body()
    if tab == "warehouse": return warehouse_body()
    if tab == "ml_model":  return ml_body()
    if tab == "scenario":  return scenario_body()
    return overview_body()

@app.callback(
    Output("active-tab", "data"),
    [Input(f"tab-{tid}", "n_clicks") for tid, _ in NAV_TABS],
    prevent_initial_call=True,
)
def switch_tab(*args):
    ctx = dash.callback_context
    if not ctx.triggered:
        return "overview"
    btn_id = ctx.triggered[0]["prop_id"].split(".")[0]
    return btn_id.replace("tab-", "")

@app.callback(
    [Output(f"val-{s}", "children") for s in ["fleet","drivers","wh","radius","staff"]],
    [Input(f"slider-{s}", "value") for s in ["fleet","drivers","wh","radius","staff"]],
)
def update_labels(fleet, drivers, wh, radius, staff):
    return [f" {fleet}", f" {drivers}", f" {wh}", f" {radius}km", f" {staff}x"]

@app.callback(
    Output("scenario-results", "children"),
    [Input(f"slider-{s}", "value") for s in ["fleet","drivers","wh","radius","staff"]],
)
def update_scenario(fleet, drivers, wh, radius, staff):
    eff     = min(99, round(58 + fleet*0.22 + drivers*0.10 + wh*3.5 - radius*0.025 + staff*2, 1))
    on_time = min(99, round(65 + fleet*0.15 + drivers*0.08 + wh*2.5 - radius*0.018 + staff*1.5, 1))
    cost_k  = round((fleet*850 + drivers*450 + wh*18000 + radius*55) / 1000, 1)
    co2     = round(fleet * radius * 0.21, 0)

    def result_card(label, value, color, note=""):
        return html.Div([
            html.Div(label, style={
                "fontFamily":"Share Tech Mono,monospace","fontSize":10,
                "color":C["muted"],"letterSpacing":2,"marginBottom":6,
            }),
            html.Div(value, style={
                "fontFamily":"Bebas Neue,sans-serif","fontSize":40,"color":color,"lineHeight":"1",
            }),
            html.Div(note, style={"fontSize":10,"color":C["muted"],"marginTop":4}),
        ], style={
            "background":C["surface"],"border":f"1px solid {color}33",
            "borderLeft":f"3px solid {color}","borderRadius":2,"padding":"16px 20px",
        })

    return [
        result_card("PROJECTED EFFICIENCY",  f"{eff}%",        C["green"] if eff>85    else C["accent"]),
        result_card("EST. ON-TIME RATE",      f"{on_time}%",    C["green"] if on_time>88 else C["red"]),
        result_card("MONTHLY COST ESTIMATE", f"${cost_k}K",    C["blue"]),
        result_card("CO₂ FOOTPRINT",         f"{co2:,.0f}kg",  C["purple"], "estimated monthly"),
    ]

# ── Expose server for Gunicorn (must be at module level) ─────────────────────
server = app.server

# ── Run locally ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    _port = int(os.environ.get("PORT", 8050))
    print(f"\n🚛 Supply Chain Optimizer starting on http://localhost:{_port}")
    app.run(debug=False, host="0.0.0.0", port=_port)

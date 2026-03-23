"""
Route Map Generator
Creates interactive Folium map of SA delivery routes
"""

import folium
from folium.plugins import HeatMap, AntPath
import pandas as pd
import json
import os

CITY_COORDS = {
    "Johannesburg":  (-26.2041, 28.0473),
    "Cape Town":     (-33.9249, 18.4241),
    "Durban":        (-29.8587, 31.0218),
    "Port Elizabeth":(-33.9608, 25.6022),
    "Bloemfontein":  (-29.0852, 26.1596),
}

def efficiency_color(pct):
    if pct >= 88: return "#4ade80"
    if pct >= 75: return "#e8770a"
    return "#f87171"

def build_route_map(route_df=None, output_path=None):
    """
    route_df: DataFrame with columns [origin, destination, efficiency_pct, total_shipments, avg_delay_hrs]
    """
    if route_df is None:
        proc_dir = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
        csv_path = os.path.join(proc_dir, "route_performance.csv")
        if os.path.exists(csv_path):
            route_df = pd.read_csv(csv_path)
        else:
            # Demo fallback
            route_df = pd.DataFrame([
                {"origin":"Johannesburg","destination":"Cape Town",      "efficiency_pct":94,"total_shipments":680,"avg_delay_hrs":0.4,"distance_km":1400},
                {"origin":"Johannesburg","destination":"Durban",         "efficiency_pct":78,"total_shipments":720,"avg_delay_hrs":1.8,"distance_km":560},
                {"origin":"Cape Town",   "destination":"Port Elizabeth", "efficiency_pct":88,"total_shipments":390,"avg_delay_hrs":0.9,"distance_km":770},
                {"origin":"Durban",      "destination":"Bloemfontein",   "efficiency_pct":65,"total_shipments":310,"avg_delay_hrs":2.9,"distance_km":620},
                {"origin":"Johannesburg","destination":"Port Elizabeth",  "efficiency_pct":71,"total_shipments":440,"avg_delay_hrs":2.1,"distance_km":1060},
                {"origin":"Johannesburg","destination":"Bloemfontein",   "efficiency_pct":85,"total_shipments":520,"avg_delay_hrs":1.1,"distance_km":400},
            ])

    # Dark tile map centred on SA
    m = folium.Map(
        location=[-29.0, 25.0],
        zoom_start=6,
        tiles="CartoDB dark_matter",
        prefer_canvas=True,
    )

    # Draw routes
    for _, row in route_df.iterrows():
        origin = row["origin"]
        dest   = row["destination"]
        if origin not in CITY_COORDS or dest not in CITY_COORDS:
            continue
        c1, c2  = CITY_COORDS[origin], CITY_COORDS[dest]
        color   = efficiency_color(row["efficiency_pct"])
        weight  = max(2, min(8, row["total_shipments"] / 100))

        AntPath(
            locations=[c1, c2],
            color=color,
            weight=weight,
            opacity=0.8,
            delay=1200,
            dash_array=[10, 20],
            pulse_color="#ffffff",
            tooltip=f"{origin} → {dest} | Efficiency: {row['efficiency_pct']}% | Shipments: {row['total_shipments']:,}",
        ).add_to(m)

    # City markers
    for city, (lat, lng) in CITY_COORDS.items():
        folium.CircleMarker(
            location=[lat, lng],
            radius=10,
            color="#e8770a",
            fill=True,
            fill_color="#e8770a",
            fill_opacity=0.9,
            tooltip=city,
            popup=folium.Popup(f"<b style='color:#e8770a'>{city}</b>", max_width=200),
        ).add_to(m)
        folium.Marker(
            location=[lat + 0.3, lng],
            icon=folium.DivIcon(
                html=f"<div style='font-family:monospace;font-size:11px;color:#e2e8f0;font-weight:bold;white-space:nowrap'>{city}</div>",
                icon_size=(150, 20),
            )
        ).add_to(m)

    # Legend
    legend_html = """
    <div style="position:fixed;bottom:30px;left:30px;z-index:1000;
                background:#0a0e14cc;border:1px solid #e8770a44;border-radius:4px;
                padding:14px 18px;font-family:monospace;font-size:12px;color:#e2e8f0;">
      <div style="color:#e8770a;font-size:13px;margin-bottom:10px;font-weight:bold;">ROUTE EFFICIENCY</div>
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
        <div style="width:30px;height:3px;background:#4ade80"></div> ≥ 88% — High
      </div>
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
        <div style="width:30px;height:3px;background:#e8770a"></div> 75–87% — Medium
      </div>
      <div style="display:flex;align-items:center;gap:8px;">
        <div style="width:30px;height:3px;background:#f87171"></div> &lt; 75% — Low
      </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    if output_path is None:
        output_path = os.path.join(os.path.dirname(__file__), "..", "assets", "route_map.html")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    m.save(output_path)
    print(f"✅ Route map saved → {output_path}")
    return m

if __name__ == "__main__":
    build_route_map()
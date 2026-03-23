"""
Data Preprocessing Pipeline
Cleans and engineers features from raw shipment data
"""

import pandas as pd
import numpy as np
import os

RAW_DIR  = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
PROC_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
os.makedirs(PROC_DIR, exist_ok=True)

def load_shipments():
    path = os.path.join(RAW_DIR, "shipments_3yr.csv")
    df = pd.read_csv(path, parse_dates=["date", "departure_datetime", "arrival_datetime"])
    return df

def load_warehouse_ops():
    path = os.path.join(RAW_DIR, "warehouse_ops_3yr.csv")
    df = pd.read_csv(path, parse_dates=["date"])
    return df

def engineer_shipment_features(df):
    df = df.copy()
    df["transit_efficiency"] = (df["planned_hours"] / df["actual_hours"].clip(lower=0.1)).clip(upper=1.0)
    df["cost_per_km"]        = df["freight_cost_usd"] / df["distance_km"]
    df["delay_severity"]     = pd.cut(df["delay_hours"], bins=[-1, 0, 2, 5, 100], labels=["none","minor","moderate","severe"])
    df["quarter"]            = pd.to_datetime(df["date"]).dt.quarter
    df["week_of_year"]       = pd.to_datetime(df["date"]).dt.isocalendar().week.astype(int)
    df["is_peak_season"]     = df["month"].isin([10, 11, 12, 1]).astype(int)
    return df

def aggregate_monthly(df):
    monthly = df.groupby(["year", "month"]).agg(
        total_shipments   =("shipment_id",       "count"),
        on_time_rate      =("on_time",           "mean"),
        avg_transit_hrs   =("actual_hours",      "mean"),
        avg_delay_hrs     =("delay_hours",        "mean"),
        total_revenue     =("freight_cost_usd",  "sum"),
        avg_freight_cost  =("freight_cost_usd",  "mean"),
        total_weight_kg   =("weight_kg",         "sum"),
        delay_rate        =("is_delayed",        "mean"),
    ).reset_index()
    monthly["on_time_rate"] = (monthly["on_time_rate"] * 100).round(2)
    monthly["delay_rate"]   = (monthly["delay_rate"] * 100).round(2)
    return monthly

def aggregate_route(df):
    route = df.groupby(["route_id", "origin", "destination", "distance_km"]).agg(
        total_shipments =("shipment_id",      "count"),
        efficiency_pct  =("on_time",          lambda x: round(x.mean()*100, 2)),
        avg_delay_hrs   =("delay_hours",       "mean"),
        avg_transit_hrs =("actual_hours",     "mean"),
        total_revenue   =("freight_cost_usd", "sum"),
        delay_rate      =("is_delayed",       lambda x: round(x.mean()*100, 2)),
    ).reset_index()
    return route

def run():
    print("⟳ Loading raw data...")
    ships = load_shipments()
    wh    = load_warehouse_ops()

    print("⟳ Engineering features...")
    ships = engineer_shipment_features(ships)

    print("⟳ Aggregating monthly KPIs...")
    monthly = aggregate_monthly(ships)

    print("⟳ Aggregating route performance...")
    routes  = aggregate_route(ships)

    ships.to_csv(os.path.join(PROC_DIR, "shipments_features.csv"),  index=False)
    monthly.to_csv(os.path.join(PROC_DIR, "monthly_kpis.csv"),      index=False)
    routes.to_csv(os.path.join(PROC_DIR, "route_performance.csv"),  index=False)
    wh.to_csv(os.path.join(PROC_DIR, "warehouse_ops.csv"),          index=False)

    print(f"✅ Processed data saved → {PROC_DIR}")
    return ships, monthly, routes, wh

if __name__ == "__main__":
    run()
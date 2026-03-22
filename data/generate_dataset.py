"""
Supply Chain Dataset Generator
Generates 3 years of realistic 3PL logistics data for South Africa
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

np.random.seed(42)
random.seed(42)

# ─── Config ─────────────────────────────────────────────────────────────────────
START_DATE = datetime(2022, 1, 1)
END_DATE   = datetime(2024, 12, 31)
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "raw")

ROUTES = [
    {"id": "R001", "origin": "Johannesburg", "dest": "Cape Town",       "distance_km": 1400, "base_hours": 16, "complexity": 3},
    {"id": "R002", "origin": "Johannesburg", "dest": "Durban",          "distance_km": 560,  "base_hours": 7,  "complexity": 2},
    {"id": "R003", "origin": "Cape Town",    "dest": "Port Elizabeth",  "distance_km": 770,  "base_hours": 9,  "complexity": 2},
    {"id": "R004", "origin": "Durban",       "dest": "Bloemfontein",    "distance_km": 620,  "base_hours": 8,  "complexity": 3},
    {"id": "R005", "origin": "Johannesburg", "dest": "Port Elizabeth",  "distance_km": 1060, "base_hours": 13, "complexity": 3},
    {"id": "R006", "origin": "Cape Town",    "dest": "Johannesburg",    "distance_km": 1400, "base_hours": 16, "complexity": 3},
    {"id": "R007", "origin": "Durban",       "dest": "Johannesburg",    "distance_km": 560,  "base_hours": 7,  "complexity": 2},
    {"id": "R008", "origin": "Port Elizabeth","dest": "Johannesburg",   "distance_km": 1060, "base_hours": 13, "complexity": 3},
    {"id": "R009", "origin": "Bloemfontein", "dest": "Cape Town",       "distance_km": 1000, "base_hours": 12, "complexity": 2},
    {"id": "R010", "origin": "Johannesburg", "dest": "Bloemfontein",    "distance_km": 400,  "base_hours": 5,  "complexity": 1},
]

WAREHOUSES = [
    {"id": "WH001", "name": "JHB Central Hub",   "city": "Johannesburg", "capacity": 5000},
    {"id": "WH002", "name": "CPT Distribution",  "city": "Cape Town",    "capacity": 3500},
    {"id": "WH003", "name": "DUR Coastal Depot", "city": "Durban",       "capacity": 2800},
]

VEHICLES = [f"TRK-{str(i).zfill(3)}" for i in range(1, 61)]

DRIVERS = [
    {"id": f"DRV-{str(i).zfill(3)}",
     "experience_years": random.randint(1, 20),
     "rating": round(random.uniform(3.0, 5.0), 1)}
    for i in range(1, 131)
]

CUSTOMERS = [f"CUST-{str(i).zfill(4)}" for i in range(1, 201)]

CARGO_TYPES = ["General Freight", "Perishables", "Hazardous", "Electronics", "Automotive Parts", "FMCG", "Textiles"]

SA_HOLIDAYS_2022 = ["2022-01-01","2022-03-21","2022-04-15","2022-04-18","2022-04-27","2022-05-01","2022-06-16","2022-08-09","2022-09-24","2022-12-16","2022-12-25","2022-12-26"]
SA_HOLIDAYS_2023 = ["2023-01-01","2023-03-21","2023-04-07","2023-04-10","2023-04-27","2023-05-01","2023-06-16","2023-08-09","2023-09-24","2023-12-16","2023-12-25","2023-12-26"]
SA_HOLIDAYS_2024 = ["2024-01-01","2024-03-21","2024-03-29","2024-04-01","2024-04-27","2024-05-01","2024-05-29","2024-06-16","2024-08-09","2024-09-24","2024-12-16","2024-12-25","2024-12-26"]
ALL_HOLIDAYS = set(SA_HOLIDAYS_2022 + SA_HOLIDAYS_2023 + SA_HOLIDAYS_2024)

WEATHER_EVENTS = {
    "Cape Town":    {"rain_months": [6, 7, 8], "storm_prob": 0.05},
    "Durban":       {"rain_months": [1, 2, 3, 11, 12], "storm_prob": 0.06},
    "Johannesburg": {"rain_months": [1, 2, 10, 11, 12], "storm_prob": 0.04},
    "Port Elizabeth":{"rain_months": [4, 5, 6, 7], "storm_prob": 0.04},
    "Bloemfontein": {"rain_months": [1, 2, 3], "storm_prob": 0.02},
}

# ─── Helpers ─────────────────────────────────────────────────────────────────
def get_weather_score(city, date):
    info = WEATHER_EVENTS.get(city, {"rain_months": [], "storm_prob": 0.02})
    score = 1.0
    if date.month in info["rain_months"]:
        score += 0.15
    if random.random() < info["storm_prob"]:
        score += 0.35
    return round(score, 3)

def get_traffic_index(date, hour):
    base = 1.0
    if date.weekday() < 5:  # weekday
        if hour in [7, 8, 9, 16, 17, 18]:
            base += 0.35
        elif hour in [6, 10, 15, 19]:
            base += 0.15
    if date.weekday() == 4:  # Friday
        base += 0.1
    base += random.uniform(-0.05, 0.1)
    return round(base, 3)

def calculate_delay(route, weather, traffic, is_holiday, driver_exp, day_of_week, cargo_type):
    delay_prob = 0.12
    delay_prob += (weather - 1.0) * 0.4
    delay_prob += (traffic - 1.0) * 0.3
    if is_holiday: delay_prob += 0.08
    if day_of_week == 4: delay_prob += 0.05  # Friday
    if driver_exp < 3:   delay_prob += 0.07
    if route["complexity"] == 3: delay_prob += 0.06
    if cargo_type == "Perishables": delay_prob += 0.04
    delay_prob = max(0.02, min(0.65, delay_prob))
    is_delayed = random.random() < delay_prob

    delay_hours = 0
    if is_delayed:
        base_delay = np.random.exponential(2.5)
        if weather > 1.2: base_delay *= 1.4
        if traffic > 1.3: base_delay *= 1.3
        delay_hours = round(min(base_delay, 18), 2)

    return is_delayed, delay_hours

def generate_shipments(n_per_day_range=(8, 22)):
    records = []
    shipment_id = 1
    current_date = START_DATE

    while current_date <= END_DATE:
        is_holiday = current_date.strftime("%Y-%m-%d") in ALL_HOLIDAYS
        n_shipments = random.randint(*n_per_day_range)
        if is_holiday: n_shipments = int(n_shipments * 0.3)
        if current_date.weekday() == 6: n_shipments = int(n_shipments * 0.4)  # Sunday

        for _ in range(n_shipments):
            route = random.choice(ROUTES)
            driver = random.choice(DRIVERS)
            vehicle = random.choice(VEHICLES)
            customer = random.choice(CUSTOMERS)
            cargo = random.choice(CARGO_TYPES)
            warehouse = random.choice(WAREHOUSES)

            departure_hour = random.choices(
                range(24),
                weights=[1,1,1,1,1,2,3,8,10,9,8,7,9,10,9,8,7,6,5,4,3,2,1,1],
                k=1
            )[0]
            departure_dt = current_date + timedelta(hours=departure_hour, minutes=random.randint(0,59))
            weather = get_weather_score(route["origin"], current_date)
            traffic = get_traffic_index(current_date, departure_hour)
            is_delayed, delay_hrs = calculate_delay(route, weather, traffic, is_holiday, driver["experience_years"], current_date.weekday(), cargo)

            planned_hours = route["base_hours"] * traffic
            actual_hours = planned_hours + delay_hrs
            arrival_dt = departure_dt + timedelta(hours=actual_hours)

            weight_kg = round(np.random.lognormal(8.5, 1.2), 1)
            weight_kg = min(max(weight_kg, 500), 28000)

            base_rate = route["distance_km"] * 0.85
            freight_cost = round(base_rate + weight_kg * 0.003 + random.uniform(-50, 100), 2)

            processing_mins = round(np.random.normal(14, 4), 1)
            if current_date.hour in [10, 11, 12, 13, 14]: processing_mins *= 1.3
            processing_mins = max(5, min(processing_mins, 45))

            records.append({
                "shipment_id":       f"SHP-{str(shipment_id).zfill(6)}",
                "date":              current_date.strftime("%Y-%m-%d"),
                "departure_datetime":departure_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "arrival_datetime":  arrival_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "route_id":          route["id"],
                "origin":            route["origin"],
                "destination":       route["dest"],
                "distance_km":       route["distance_km"],
                "route_complexity":  route["complexity"],
                "driver_id":         driver["id"],
                "driver_experience": driver["experience_years"],
                "driver_rating":     driver["rating"],
                "vehicle_id":        vehicle,
                "customer_id":       customer,
                "warehouse_id":      warehouse["id"],
                "cargo_type":        cargo,
                "weight_kg":         weight_kg,
                "freight_cost_usd":  freight_cost,
                "planned_hours":     round(planned_hours, 2),
                "actual_hours":      round(actual_hours, 2),
                "delay_hours":       delay_hrs,
                "is_delayed":        int(is_delayed),
                "departure_hour":    departure_hour,
                "day_of_week":       current_date.weekday(),
                "day_name":          current_date.strftime("%A"),
                "month":             current_date.month,
                "year":              current_date.year,
                "is_holiday":        int(is_holiday),
                "is_weekend":        int(current_date.weekday() >= 5),
                "weather_score":     weather,
                "traffic_index":     traffic,
                "processing_time_mins": round(processing_mins, 1),
                "on_time":           int(not is_delayed),
            })
            shipment_id += 1

        current_date += timedelta(days=1)

    return pd.DataFrame(records)

def generate_warehouse_operations():
    records = []
    current_date = START_DATE
    op_id = 1

    while current_date <= END_DATE:
        for wh in WAREHOUSES:
            for hour in range(24):
                is_peak = hour in range(8, 18)
                base_orders = 5 if not is_peak else 35
                if current_date.weekday() >= 5: base_orders = int(base_orders * 0.5)
                if current_date.strftime("%Y-%m-%d") in ALL_HOLIDAYS: base_orders = int(base_orders * 0.2)

                n_orders = max(0, int(np.random.poisson(base_orders)))
                capacity_used = min(100, round((n_orders / wh["capacity"]) * 100 * 24, 1))
                staff_count = max(2, int(n_orders / 8) + random.randint(1, 3))
                avg_processing = round(max(5, np.random.normal(14, 3)), 1)

                records.append({
                    "op_id":           f"WOP-{str(op_id).zfill(7)}",
                    "warehouse_id":    wh["id"],
                    "warehouse_name":  wh["name"],
                    "city":            wh["city"],
                    "date":            current_date.strftime("%Y-%m-%d"),
                    "hour":            hour,
                    "orders_processed":n_orders,
                    "capacity_used_pct":capacity_used,
                    "staff_on_duty":   staff_count,
                    "avg_processing_mins": avg_processing,
                    "throughput_efficiency": round(min(100, (n_orders / max(1, staff_count * 8)) * 100), 1),
                })
                op_id += 1
        current_date += timedelta(days=1)

    return pd.DataFrame(records)

# ─── Main ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("⟳ Generating shipment records (3 years)...")
    shipments = generate_shipments()
    path1 = os.path.join(OUTPUT_DIR, "shipments_3yr.csv")
    shipments.to_csv(path1, index=False)
    print(f"  ✓ {len(shipments):,} shipment records → {path1}")

    print("⟳ Generating warehouse operations data...")
    wh_ops = generate_warehouse_operations()
    path2 = os.path.join(OUTPUT_DIR, "warehouse_ops_3yr.csv")
    wh_ops.to_csv(path2, index=False)
    print(f"  ✓ {len(wh_ops):,} warehouse records → {path2}")

    print("\n📊 Dataset Summary:")
    print(f"  Date range:      {shipments['date'].min()} → {shipments['date'].max()}")
    print(f"  Total shipments: {len(shipments):,}")
    print(f"  Delay rate:      {shipments['is_delayed'].mean()*100:.1f}%")
    print(f"  Routes covered:  {shipments['route_id'].nunique()}")
    print(f"  Unique drivers:  {shipments['driver_id'].nunique()}")
    print(f"  Avg freight $:   ${shipments['freight_cost_usd'].mean():.2f}")
    print("\n✅ Data generation complete.")

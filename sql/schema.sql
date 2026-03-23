-- ============================================================
-- Supply Chain Optimizer - PostgreSQL Schema
-- Run: psql -U postgres -d supply_chain -f schema.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS supply_chain;
\c supply_chain;

-- ── Routes ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS routes (
    route_id        VARCHAR(10) PRIMARY KEY,
    origin          VARCHAR(100) NOT NULL,
    destination     VARCHAR(100) NOT NULL,
    distance_km     INTEGER NOT NULL,
    base_hours      FLOAT NOT NULL,
    complexity      SMALLINT CHECK (complexity IN (1, 2, 3)),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Warehouses ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS warehouses (
    warehouse_id    VARCHAR(10) PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    city            VARCHAR(100) NOT NULL,
    capacity        INTEGER NOT NULL,
    latitude        FLOAT,
    longitude       FLOAT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Drivers ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS drivers (
    driver_id           VARCHAR(10) PRIMARY KEY,
    experience_years    SMALLINT NOT NULL,
    rating              FLOAT CHECK (rating BETWEEN 1 AND 5),
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Shipments (main fact table) ──────────────────────────────
CREATE TABLE IF NOT EXISTS shipments (
    shipment_id             VARCHAR(15) PRIMARY KEY,
    date                    DATE NOT NULL,
    departure_datetime      TIMESTAMP NOT NULL,
    arrival_datetime        TIMESTAMP NOT NULL,
    route_id                VARCHAR(10) REFERENCES routes(route_id),
    origin                  VARCHAR(100),
    destination             VARCHAR(100),
    distance_km             INTEGER,
    route_complexity        SMALLINT,
    driver_id               VARCHAR(10) REFERENCES drivers(driver_id),
    driver_experience       SMALLINT,
    driver_rating           FLOAT,
    vehicle_id              VARCHAR(15),
    customer_id             VARCHAR(15),
    warehouse_id            VARCHAR(10) REFERENCES warehouses(warehouse_id),
    cargo_type              VARCHAR(50),
    weight_kg               FLOAT,
    freight_cost_usd        FLOAT,
    planned_hours           FLOAT,
    actual_hours            FLOAT,
    delay_hours             FLOAT DEFAULT 0,
    is_delayed              SMALLINT DEFAULT 0,
    departure_hour          SMALLINT,
    day_of_week             SMALLINT,
    day_name                VARCHAR(10),
    month                   SMALLINT,
    year                    SMALLINT,
    is_holiday              SMALLINT DEFAULT 0,
    is_weekend              SMALLINT DEFAULT 0,
    weather_score           FLOAT,
    traffic_index           FLOAT,
    processing_time_mins    FLOAT,
    on_time                 SMALLINT DEFAULT 1
);

-- ── Warehouse Operations ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS warehouse_operations (
    op_id                   VARCHAR(15) PRIMARY KEY,
    warehouse_id            VARCHAR(10) REFERENCES warehouses(warehouse_id),
    warehouse_name          VARCHAR(100),
    city                    VARCHAR(100),
    date                    DATE NOT NULL,
    hour                    SMALLINT NOT NULL,
    orders_processed        INTEGER DEFAULT 0,
    capacity_used_pct       FLOAT,
    staff_on_duty           SMALLINT,
    avg_processing_mins     FLOAT,
    throughput_efficiency   FLOAT
);

-- ── ML Predictions ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS delay_predictions (
    prediction_id   SERIAL PRIMARY KEY,
    shipment_id     VARCHAR(15),
    predicted_delay FLOAT,
    delay_prob      FLOAT,
    model_version   VARCHAR(20),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Indexes ──────────────────────────────────────────────────
CREATE INDEX idx_shipments_date        ON shipments(date);
CREATE INDEX idx_shipments_route       ON shipments(route_id);
CREATE INDEX idx_shipments_is_delayed  ON shipments(is_delayed);
CREATE INDEX idx_shipments_year_month  ON shipments(year, month);
CREATE INDEX idx_wh_ops_date           ON warehouse_operations(date);
CREATE INDEX idx_wh_ops_warehouse      ON warehouse_operations(warehouse_id);

-- ── Useful Views ─────────────────────────────────────────────
-- Views
CREATE OR REPLACE VIEW monthly_kpis AS
SELECT
    year, month,
    COUNT(*)                                AS total_shipments,
    ROUND(AVG(on_time)::numeric * 100, 2)   AS on_time_rate,
    ROUND(AVG(actual_hours)::numeric, 2)    AS avg_transit_hours,
    ROUND(AVG(delay_hours)::numeric, 2)     AS avg_delay_hours,
    ROUND(SUM(freight_cost_usd)::numeric, 2)AS total_revenue,
    ROUND(AVG(freight_cost_usd)::numeric, 2)AS avg_freight_cost
FROM shipments
GROUP BY year, month
ORDER BY year, month;

CREATE OR REPLACE VIEW route_performance AS
SELECT
    route_id, origin, destination, distance_km,
    COUNT(*)                                AS total_shipments,
    ROUND(AVG(on_time)::numeric * 100, 2)   AS efficiency_pct,
    ROUND(AVG(delay_hours)::numeric, 2)     AS avg_delay_hours,
    ROUND(AVG(actual_hours)::numeric, 2)    AS avg_transit_hours,
    ROUND(SUM(freight_cost_usd)::numeric, 2)AS total_revenue
FROM shipments
GROUP BY route_id, origin, destination, distance_km
ORDER BY efficiency_pct;
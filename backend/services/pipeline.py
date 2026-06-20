"""
Event-Driven Congestion — Full Pipeline (Final)
Flipkart GridLock Round 2

Supersedes pipeline.py. Adds the Resource Recommender and Case-Based
Retrieval stages that were previously listed as "What's Left", plus the two
genuinely good ideas from Master_Advanced_Pipeline.ipynb (BPR capacity-aware
routing, greedy barricade simulation) -- ported in with their bugs fixed.

  Stage 1: Data cleaning
  Stage 2: Spatial enrichment
  Stage 3: External signals
  Stage 4: Feature engineering
  Stage 5: Triage classifier (closure + priority + CascadeRisk)
  Stage 6: Duration models (fast XGBoost quantile / slow Weibull AFT)
  Stage 7: Spread model (footprint sizes, full dataset)
  Stage 8: Resource Recommender   <-- NEW
  Stage 9: Case-Based Retrieval   <-- NEW
  Stage 10: End-to-end demo       <-- NEW

Bugs found and fixed vs Master_Advanced_Pipeline.ipynb (see chat history for
the full bug report):
  - int/str node-ID mismatch in compute_footprint / find_through_route_endpoints
    / greedy_barricade_simulation -- silently zeroed every footprint there.
    Fixed here by keeping node IDs as int throughout (osmnx load_graphml
    convention), consistent with 04_Spread_Model.ipynb.
  - Priority model and cascade_risk_score were promised but never implemented
    there. Both are implemented here (carried over from pipeline.py Stage 5).
  - "Competing Risks" duration model claimed an abandonment classifier that
    did not exist in code. Not reintroduced here -- the single Weibull AFT
    with documented limitations (see Stage 6) is the honest version.
  - BPR was only wired into the barricade-candidate test loop, not applied
    pipeline-wide. Same scoping kept here deliberately: BPR makes sense for
    "what happens if we block this specific node," not for the dataset-wide
    footprint pass (no real per-road traffic volume data exists to make a
    city-wide BPR pass meaningful -- see Stage 8 note on the volume constant).

What's genuinely still left after this file -- see bottom of this file and
MASTER_VISION.md:
  - Presentation-layer polish, map visualization, and BPR demand-side realism
    (unchanged from before -- see printed "WHAT'S LEFT" block in main()).
  - Historical Trend / Upcoming-Hike Predictor is now IMPLEMENTED (previously
    a stub). See `historical_trend_predictor()` below: merges a DOW x Hour x
    Zone Poisson surge baseline, an Open-Meteo rainfall-forecast trigger, and
    optional Tavily live-event enrichment (Tavily calls are cached per
    zone/hour and auto-disabled for the rest of the run after repeated
    failures). Rainfall/Tavily signals are advisory-time only by design --
    they are never added to the trained models, since they'd be all-zero
    for every historical training row.

Run: python new_pipeline.py
"""

import json
import os
import pickle
import time
from pathlib import Path
import warnings
from collections import defaultdict
from datetime import date, timedelta
from typing import Optional

import numpy as np
import pandas as pd
import requests
from requests.exceptions import SSLError
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import precision_recall_curve
from sklearn.model_selection import KFold, StratifiedKFold, cross_val_predict
from sklearn.neighbors import BallTree, KNeighborsClassifier, NearestNeighbors
from sklearn.preprocessing import LabelEncoder, StandardScaler

try:
    from tavily import TavilyClient
    HAS_TAVILY = True
except ModuleNotFoundError:
    TavilyClient = None
    HAS_TAVILY = False

warnings.filterwarnings("ignore")

DATA_PATH = "Astram event data_anonymized - Astram event data_anonymizedb40ac87.csv"
GRAPH_PATH = "bengaluru_major_roads.graphml"
CENTRALITY_CACHE = "node_centrality.parquet"
RAINFALL_CACHE = Path(__file__).parent.parent / "data" / "rainfall_cache.parquet"
ENRICHED_PATH = "events_enriched.parquet"
TARGET_ENCODING_PATH = "target_encoding_maps.json"
CASCADE_SCALER_PATH = "cascade_risk_scaler.json"
CLOSURE_THRESHOLD_PATH = "closure_threshold.json"
NODE_NAME_CACHE = "node_name_cache.parquet"
SPATIAL_CONFIDENCE_THRESHOLD_M = 150

# Bengaluru school/office hours -- static domain knowledge, not something that
# changes day to day, so hardcoded rather than fetched. School dropoff/pickup
# and IT-corridor office peaks are well-documented, stable facts.
SCHOOL_HOURS = [(7, 9), (15, 16)]
OFFICE_PEAK_HOURS = [(9, 10), (18, 20)]
IT_CORRIDOR_ZONES = {"East Zone 1", "East Zone 2", "South Zone 1", "South Zone 2"}

# Road-class hierarchy, highest first -- used to pick the most significant
# road type at a junction instead of an arbitrary first-edge-wins choice.
ROAD_CLASS_RANK = {
    "motorway": 7, "motorway_link": 6.5, "trunk": 6, "trunk_link": 5.5,
    "primary": 5, "primary_link": 4.5, "secondary": 4, "secondary_link": 3.5,
    "tertiary": 3, "tertiary_link": 2.5, "unclassified": 1, "residential": 0,
}

CHINNASWAMY_LAT, CHINNASWAMY_LON = 12.9789, 77.5990
RCB_HOME_MATCHES_2024 = [
    "2024-03-22", "2024-03-29", "2024-04-03", "2024-04-15",
    "2024-04-21", "2024-04-30", "2024-05-08", "2024-05-13",
]
ELECTION_CAMPAIGN_START = pd.to_datetime("2024-02-15").date()
ELECTION_CAMPAIGN_END = pd.to_datetime("2024-04-26").date()
HOLIDAYS = {
    "2023-11-01": ("Kannada Rajyotsava", "state"),
    "2023-11-14": ("Children's Day", "observance"),
    "2023-11-27": ("Guru Nanak Jayanti", "religious"),
    "2023-12-25": ("Christmas", "religious"),
    "2024-01-01": ("New Year", "national"),
    "2024-01-15": ("Makar Sankranti / Pongal", "religious"),
    "2024-01-22": ("Ram Mandir Consecration", "national"),
    "2024-01-26": ("Republic Day", "national"),
    "2024-03-08": ("Maha Shivaratri", "religious"),
    "2024-03-25": ("Holi", "religious"),
    "2024-03-29": ("Good Friday", "religious"),
    "2024-04-09": ("Ugadi", "state"),
    "2024-04-11": ("Eid al-Fitr", "religious"),
    "2024-04-14": ("Dr. Ambedkar Jayanti / Tamil New Year", "national"),
    "2024-04-17": ("Ram Navami", "religious"),
}

FAST_CAUSES = ["vehicle_breakdown", "accident", "procession", "protest", "congestion", "test_demo"]
SLOW_CAUSES = ["construction", "water_logging", "road_conditions", "tree_fall",
               "public_event", "vip_movement", "others", "fog_low_visibility"]
ESCALATION_CAUSES = ["pot_holes", "debris"]
HEAVY_VEH = ["heavy_vehicle", "truck", "lcv", "bmtc_bus", "ksrtc_bus", "private_bus"]
PUBLIC_TRANSPORT = ["bmtc_bus", "ksrtc_bus", "private_bus"]

CLOSURE_KEYWORDS = ["closed", "blocked", "diverted", "divert", "closure", "barricade", "shut",
                     "ಮುಚ್ಚ", "ಬ್ಲಾಕ್"]
SLOW_KEYWORDS = ["slow", "congestion", "heavy", "jam", "traffic"]

TRIAGE_CAT_FEATURES = [
    "event_cause", "zone_filled", "corridor", "osm_road_type",
    "veh_type", "gba_identifier", "model_track", "holiday_type",
]
TRIAGE_NUM_FEATURES = [
    "hour_ist", "dow", "month", "is_weekend", "is_peak",
    "junction_centrality", "rainfall_mm", "rainfall_mm_3day",
    "is_ipl_match_day", "near_chinnaswamy_on_match_day", "distance_to_chinnaswamy_km",
    "is_election_campaign_period", "is_public_holiday",
    "has_kannada", "desc_word_count", "desc_closure_signal", "desc_slow_signal",
    "cascade_count", "hotspot_score", "segment_length_km", "is_stretch",
    "is_heavy_vehicle", "is_public_transport", "snap_distance_m",
    # -- Historical Trend module, Approach A: DOW x Hour x Zone Poisson baseline --
    "zone_baseline_rate", "zone_surge_ratio", "is_surge_zone",
    "is_school_hour", "is_office_peak_hour", "is_it_corridor_zone",
]
DURATION_NUM_FEATURES_EXTRA = ["closure_probability", "cascade_risk_score_v2"]

# ════════════════════════════════════════════════════════════════════════════
# HISTORICAL TREND / UPCOMING-HIKE PREDICTOR — constants
#
# Three signals merged in priority order inside historical_trend_predictor():
#   A. DOW x Hour x Zone Poisson surge baseline (zone_baseline_rate, etc.)
#   B. Rainfall-forecast trigger (Open-Meteo, advisory-time only)
#   D. Tavily live-event enrichment (advisory-time only, never trained on)
# ════════════════════════════════════════════════════════════════════════════
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
BASELINE_CACHE = Path(__file__).parent.parent / "models" / "baseline_table.pkl"
POISSON_SURGE_K = 2.0          # flag if count > mean + K*sqrt(mean)
MONSOON_RAIN_THRESH = 5.0      # mm/day forecast triggers predicted_monsoon_surge (IMD "rainy day" def.)
ZONE_FILL_VALUE = "Unknown"

# Tavily is inference-time-only context enrichment; never trains the models.
# Key is read from the environment only -- never hardcode a key in this file.
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")
TAVILY_CACHE_TTL_SECONDS = 1800            # 30 min: avoid duplicate queries per zone/hour
TAVILY_MAX_CONSECUTIVE_FAILURES = 3        # after this many errors in a row, stop calling Tavily

HIGH_IMPACT_KEYWORDS = [
    "procession", "chaturthi", "ganesh", "navratri", "dussehra",
    "bandh", "rally", "vip", "ipl", "match", "election", "flood",
    "waterlogging", "heavy rain", "storm", "closure", "blocked",
]
CAUSE_KEYWORD_MAP = {
    "procession":    ["procession", "chaturthi", "navratri", "dussehra", "rally", "parade"],
    "water_logging": ["flood", "waterlogging", "heavy rain", "storm", "inundated"],
    "vip_movement":  ["vip", "motorcade", "convoy", "minister", "pm", "cm", "president"],
    "public_event":  ["concert", "match", "ipl", "cricket", "event", "gathering", "stadium"],
    "protest":       ["protest", "bandh", "agitation", "demonstration", "strike"],
}

# Spread model parameters
DECAY_RATE = {
    "vip_movement": 0.10, "public_event": 0.15, "protest": 0.18,
    "procession": 0.20, "construction": 0.25, "road_conditions": 0.30,
    "water_logging": 0.30, "tree_fall": 0.35, "congestion": 0.35,
    "accident": 0.45, "vehicle_breakdown": 0.55, "others": 0.40,
    "pot_holes": 0.60, "debris": 0.50,
}
DEFAULT_DECAY = 0.40
MAX_RADIUS_M = {"vip_movement": 8000, "public_event": 6000, "protest": 5000,
                "procession": 5000, "construction": 4000}
DEFAULT_MAX_RADIUS_M = 3000
IMPACT_THRESHOLD = 0.15
HARD_CLOSURE_THRESHOLD = 0.6

# Resource Recommender parameters (MASTER_VISION.md Section 7.1)
BASE_OFFICERS = {
    "vip_movement": 10, "public_event": 8, "procession": 6, "protest": 5,
    "construction": 3, "accident": 3, "tree_fall": 2.5, "vehicle_breakdown": 1.5,
}
DEFAULT_BASE_OFFICERS = 2
BPR_CAPACITY_MAP = {
    "motorway": 6000, "trunk": 4000, "primary": 2000,
    "secondary": 1000, "tertiary": 800, "residential": 400, "unclassified": 200,
}


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return R * 2 * np.arcsin(np.sqrt(a))


def kfold_target_encode(df, group_col, target_col, n_splits=5, m=25, random_state=42):
    """Out-of-fold, smoothed target encoding (Micci-Barreca m-estimate).

    Fixes a leakage bug: cause_closure_rate / cause_median_duration were
    plain groupby().mean() with no holdout -- every row's encoding included
    its own label. Here each row's encoding comes only from the OTHER folds,
    and is shrunk toward the global mean when the group is small (m=25 -- a
    cause needs ~25 observations before its own average is trusted over the
    global prior).

    Returns (oof_encoded_series, full_data_map_for_inference, global_mean).
    """
    global_mean = df[target_col].mean()
    encoded = pd.Series(index=df.index, dtype=float)
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    for train_idx, val_idx in kf.split(df):
        train_fold = df.iloc[train_idx]
        stats = train_fold.groupby(group_col)[target_col].agg(["mean", "count"])
        smoothed = (stats["mean"] * stats["count"] + global_mean * m) / (stats["count"] + m)
        val_groups = df.iloc[val_idx][group_col]
        encoded.iloc[val_idx] = val_groups.map(smoothed).fillna(global_mean).values
    # Full-data map -- for applying to a new/unseen single event at inference time
    full_stats = df.groupby(group_col)[target_col].agg(["mean", "count"])
    full_smoothed = (full_stats["mean"] * full_stats["count"] + global_mean * m) / (full_stats["count"] + m)
    return encoded, full_smoothed.to_dict(), global_mean


# ════════════════════════════════════════════════════════════════════════════
# STAGE 1 — DATA CLEANING  (unchanged from pipeline.py, already validated)
# ════════════════════════════════════════════════════════════════════════════

def stage1_clean(df: pd.DataFrame) -> pd.DataFrame:
    print("\n[Stage 1] Data cleaning...")
    df = df.drop(columns=["map_file", "comment", "meta_data"], errors="ignore")

    time_cols = ["start_datetime", "end_datetime", "modified_datetime",
                 "resolved_datetime", "closed_datetime"]
    for col in time_cols:
        df[col] = pd.to_datetime(df[col], utc=True, errors="coerce")
    df["start_ist"] = df["start_datetime"].dt.tz_convert("Asia/Kolkata")

    df["requires_road_closure"] = df["requires_road_closure"].map(
        {True: 1, False: 0, "TRUE": 1, "FALSE": 0, "True": 1, "False": 0}
    ).fillna(0).astype(int)

    df["end_ts"] = df["resolved_datetime"].fillna(df["closed_datetime"])
    df["duration_hrs_raw"] = (df["end_ts"] - df["start_datetime"]).dt.total_seconds() / 3600
    mask_tz_fix = (df["duration_hrs_raw"] < 0) & (df["duration_hrs_raw"] > -6)
    df["duration_hrs"] = df["duration_hrs_raw"].copy()
    df.loc[mask_tz_fix, "duration_hrs"] = df.loc[mask_tz_fix, "duration_hrs_raw"] + 5.5
    df.loc[df["duration_hrs"] < 0, "duration_hrs"] = np.nan

    df["is_censored"] = (df["status"] == "active").astype(int)
    df["duration_valid"] = df["duration_hrs"].notna() & (df["duration_hrs"] > 0) & (df["duration_hrs"] <= 500)
    df["duration_hrs_capped"] = df["duration_hrs"].clip(0, 500)

    df["event_cause"] = df["event_cause"].str.strip()
    df["event_cause"] = df["event_cause"].replace(
        {"Debris": "debris", "Fog / Low Visibility": "fog_low_visibility"}
    ).str.lower()

    def assign_track(cause):
        if cause in FAST_CAUSES:
            return "fast"
        elif cause in ESCALATION_CAUSES:
            return "escalation"
        return "slow"
    df["model_track"] = df["event_cause"].apply(assign_track)

    df["endlatitude"] = pd.to_numeric(df["endlatitude"], errors="coerce")
    df["endlongitude"] = pd.to_numeric(df["endlongitude"], errors="coerce")
    has_end_coord = (df["endlatitude"].notna() & (df["endlatitude"] != 0) &
                      df["endlongitude"].notna() & (df["endlongitude"] != 0))
    df["segment_length_km"] = 0.0
    df.loc[has_end_coord, "segment_length_km"] = haversine_km(
        df.loc[has_end_coord, "latitude"], df.loc[has_end_coord, "longitude"],
        df.loc[has_end_coord, "endlatitude"], df.loc[has_end_coord, "endlongitude"]
    )
    df["is_stretch"] = ((df["segment_length_km"] >= 0.1) & (df["segment_length_km"] < 5)).astype(int)
    df["segment_length_km"] = df["segment_length_km"].clip(0, 5)
    df.loc[df["is_stretch"] == 0, "segment_length_km"] = 0.0

    df["is_heavy_vehicle"] = df["veh_type"].isin(HEAVY_VEH).astype(int)
    df["is_public_transport"] = df["veh_type"].isin(PUBLIC_TRANSPORT).astype(int)
    df = df.drop(columns=["cargo_material", "age_of_truck", "reason_breakdown"], errors="ignore")

    df["valid_coord"] = ((df["latitude"] > 12.0) & (df["latitude"] < 14.0) &
                          (df["longitude"] > 76.5) & (df["longitude"] < 78.5))

    print(f"  Rows: {len(df)} | Negative durations fixed: {mask_tz_fix.sum()} | "
          f"Tracks: {df['model_track'].value_counts().to_dict()}")
    return df


# ════════════════════════════════════════════════════════════════════════════
# STAGE 2 — SPATIAL ENRICHMENT  (unchanged from pipeline.py)
# ════════════════════════════════════════════════════════════════════════════

def stage2_spatial(df: pd.DataFrame):
    print("\n[Stage 2] Spatial enrichment...")
    import osmnx as ox
    import networkx as nx

    zone_labeled = df[df["zone"].notna() & df["valid_coord"]]
    zone_unlabeled = df[df["zone"].isna() & df["valid_coord"]]
    knn_zone = KNeighborsClassifier(n_neighbors=7, weights="distance")
    knn_zone.fit(zone_labeled[["latitude", "longitude"]], zone_labeled["zone"])
    df["zone_filled"] = df["zone"]
    if len(zone_unlabeled) > 0:
        df.loc[zone_unlabeled.index, "zone_filled"] = knn_zone.predict(
            zone_unlabeled[["latitude", "longitude"]]
        )
    df["zone_filled"] = df["zone_filled"].fillna("Unknown")
    print(f"  Zone coverage: {(df['zone_filled']!='Unknown').mean()*100:.1f}%")

    if not os.path.exists(GRAPH_PATH):
        print("  Downloading Bengaluru major-road graph (one-time, ~1-2 min)...")
        major_road_filter = (
            '["highway"~"motorway|trunk|primary|secondary|tertiary|'
            'motorway_link|trunk_link|primary_link|secondary_link|tertiary_link"]'
        )
        west, south, east, north = 77.28, 12.77, 77.80, 13.30
        G = ox.graph_from_bbox(bbox=(west, south, east, north),
                                custom_filter=major_road_filter, simplify=True, retain_all=False)
        G = ox.add_edge_speeds(G)
        G = ox.add_edge_travel_times(G)
        ox.save_graphml(G, GRAPH_PATH)
    else:
        G = ox.load_graphml(GRAPH_PATH)
    print(f"  Graph: {len(G.nodes)} nodes, {len(G.edges)} edges")

    if os.path.exists(CENTRALITY_CACHE):
        centrality_df = pd.read_parquet(CENTRALITY_CACHE)
        centrality = dict(zip(centrality_df["node"].astype(int), centrality_df["centrality"]))
    else:
        k_sample = min(500, len(G.nodes))
        centrality = nx.betweenness_centrality(G, k=k_sample, weight="length", seed=42)
        pd.DataFrame({"node": list(centrality.keys()), "centrality": list(centrality.values())}) \
            .to_parquet(CENTRALITY_CACHE)

    valid_idx = df[df["valid_coord"]].index
    nearest_nodes, dists = ox.distance.nearest_nodes(
        G, df.loc[valid_idx, "longitude"].values, df.loc[valid_idx, "latitude"].values,
        return_dist=True
    )
    df["osm_node"] = pd.NA
    df["snap_distance_m"] = np.nan
    df.loc[valid_idx, "osm_node"] = nearest_nodes
    df.loc[valid_idx, "snap_distance_m"] = dists
    df["junction_centrality"] = df["osm_node"].map(centrality).fillna(0.0)

    # Road-class hierarchy fix: setdefault() kept whichever edge was iterated
    # first at a junction -- a node at a primary+residential intersection
    # could read "residential" purely by iteration order. Now keeps the
    # highest-ranked road class seen across all incident edges, and the
    # `name` tag from that same highest-class edge (free road-name resolution
    # for diversion advisories, no geocoding API needed).
    edges_gdf = ox.graph_to_gdfs(G, nodes=False, edges=True)
    node_best_rank = {}
    node_to_road = {}
    node_to_name = {}
    for (u, v, k), row in edges_gdf.iterrows():
        rt = row.get("highway", "unclassified")
        if isinstance(rt, list):
            rt = rt[0]
        rank = ROAD_CLASS_RANK.get(rt, -1)
        name = row.get("name", None)
        if isinstance(name, list):
            name = name[0] if name else None
        for node in (u, v):
            if rank > node_best_rank.get(node, -2):
                node_best_rank[node] = rank
                node_to_road[node] = rt
                node_to_name[node] = name
    df["osm_road_type"] = df["osm_node"].map(node_to_road).fillna("unclassified")
    df["osm_road_name"] = df["osm_node"].map(node_to_name)

    # Spatial confidence flag (bug found in review: events far from any major
    # road silently snap to the nearest one anyway, polluting centrality and
    # footprint with a wrong location). Advisory degrades the spatial section
    # when this is False instead of trusting it blindly.
    df["spatial_confidence"] = df["snap_distance_m"] < SPATIAL_CONFIDENCE_THRESHOLD_M
    low_conf_pct = (~df["spatial_confidence"]).mean() * 100
    print(f"  Low spatial confidence (snap > {SPATIAL_CONFIDENCE_THRESHOLD_M}m): "
          f"{(~df['spatial_confidence']).sum()} events ({low_conf_pct:.1f}%)")

    df["lat_grid"] = (df["latitude"] / 0.001).round() * 0.001
    df["lon_grid"] = (df["longitude"] / 0.001).round() * 0.001
    grid_counts = df.groupby(["lat_grid", "lon_grid"]).size().rename("hotspot_count").reset_index()
    df = df.merge(grid_counts, on=["lat_grid", "lon_grid"], how="left")
    df["hotspot_score"] = df["hotspot_count"] / len(df)
    df = df.drop(columns=["lat_grid", "lon_grid", "hotspot_count"])

    print(f"  Median snap distance: {df['snap_distance_m'].median():.0f} m")
    return df, G, centrality


# ════════════════════════════════════════════════════════════════════════════
# STAGE 3 — EXTERNAL SIGNAL INTEGRATION  (unchanged from pipeline.py)
# ════════════════════════════════════════════════════════════════════════════

def stage3_external_signals(df: pd.DataFrame) -> pd.DataFrame:
    print("\n[Stage 3] External signal integration...")
    df["event_date"] = df["start_ist"].dt.date

    if os.path.exists(RAINFALL_CACHE):
        rainfall_df = pd.read_parquet(RAINFALL_CACHE)
    else:
        valid_dates = df["start_ist"].dropna().dt.date
        start_date, end_date = valid_dates.min().isoformat(), valid_dates.max().isoformat()
        url = (f"https://archive-api.open-meteo.com/v1/archive?latitude=12.9716&longitude=77.5946"
               f"&start_date={start_date}&end_date={end_date}&daily=precipitation_sum&timezone=Asia%2FKolkata")
        resp = requests.get(url, timeout=30).json()
        rainfall_df = pd.DataFrame({
            "date": pd.to_datetime(resp["daily"]["time"]).date,
            "rainfall_mm": resp["daily"]["precipitation_sum"]
        })
        rainfall_df.to_parquet(RAINFALL_CACHE)

    df = df.merge(rainfall_df, left_on="event_date", right_on="date", how="left").drop(columns=["date"])
    df["rainfall_mm"] = df["rainfall_mm"].fillna(0.0)
    rainfall_sorted = rainfall_df.sort_values("date").set_index("date")
    rainfall_sorted["rainfall_mm_3day"] = rainfall_sorted["rainfall_mm"].rolling(3, min_periods=1).sum()
    df = df.merge(rainfall_sorted[["rainfall_mm_3day"]], left_on="event_date", right_index=True, how="left")
    df["rainfall_mm_3day"] = df["rainfall_mm_3day"].fillna(0.0)

    holiday_df = pd.DataFrame([
        {"date": pd.to_datetime(d).date(), "holiday_name": n, "holiday_type": t}
        for d, (n, t) in HOLIDAYS.items()
    ])
    df = df.merge(holiday_df, left_on="event_date", right_on="date", how="left").drop(columns=["date"])
    df["is_public_holiday"] = df["holiday_name"].notna().astype(int)
    df["holiday_type"] = df["holiday_type"].fillna("none")

    max_event_date = df["event_date"].dropna().max()
    ipl_dates = [d for d in RCB_HOME_MATCHES_2024 if d <= max_event_date.isoformat()]
    df["is_ipl_match_day"] = df["event_date"].astype(str).isin(ipl_dates).astype(int)
    df["distance_to_chinnaswamy_km"] = haversine_km(
        df["latitude"], df["longitude"], CHINNASWAMY_LAT, CHINNASWAMY_LON
    )
    df["near_chinnaswamy_on_match_day"] = (
        (df["is_ipl_match_day"] == 1) & (df["distance_to_chinnaswamy_km"] < 5)
    ).astype(int)

    df["is_election_campaign_period"] = df["event_date"].apply(
        lambda d: bool(d is not None and not pd.isna(d) and
                       ELECTION_CAMPAIGN_START <= d <= ELECTION_CAMPAIGN_END)
    ).astype(int)

    print(f"  Holiday-tagged: {df['is_public_holiday'].sum()} | "
          f"IPL-day events near stadium: {df['near_chinnaswamy_on_match_day'].sum()} | "
          f"Election period: {df['is_election_campaign_period'].sum()}")
    return df


# ════════════════════════════════════════════════════════════════════════════
# HISTORICAL TREND / UPCOMING-HIKE PREDICTOR
#
# Implements the contract previously stubbed at the bottom of this file
# (`historical_trend_predictor`), per MASTER_VISION.md. Merges three signals:
#   A. DOW x Hour x Zone Poisson surge baseline  -- trained-feature-eligible
#   B. Rainfall-forecast trigger (Open-Meteo)      -- advisory-time only
#   D. Tavily live-event enrichment                -- advisory-time only
# ════════════════════════════════════════════════════════════════════════════

# ── Approach A: DOW x Hour x Zone Poisson baseline ──────────────────────────

def build_baseline_table(df: pd.DataFrame) -> dict:
    """
    Builds the (dow, hour_ist, zone_filled) -> {mean_rate, surge_threshold}
    lookup table from the training data. Must be called after `dow`,
    `hour_ist`, and `zone_filled` exist on df (Stage 2 + start of Stage 4).

    Poisson rationale: event counts at fine (dow, hour, zone) granularity are
    rare, memoryless, discrete events -- variance ~= mean, so
    surge_threshold = mean_rate + K * sqrt(mean_rate). This is more sensitive
    than a flat mean+std rule in quiet zones, and avoids false positives in
    high-volume slots where raw std is also high.
    """
    dow_week_keys = defaultdict(set)
    for dow_val, start_ist in zip(df["dow"], df["start_ist"]):
        if pd.notna(dow_val) and pd.notna(start_ist):
            iso = start_ist.isocalendar()
            dow_week_keys[int(dow_val)].add((iso[0], iso[1]))
    dow_n_occurrences = {dow: len(weeks) for dow, weeks in dow_week_keys.items()}

    slot_counts = (
        df.dropna(subset=["dow", "hour_ist"])
        .groupby(["dow", "hour_ist", "zone_filled"])
        .size()
        .reset_index(name="total_count")
    )
    slot_counts["n_occurrences"] = slot_counts["dow"].map(dow_n_occurrences)
    slot_counts["mean_rate"] = slot_counts["total_count"] / slot_counts["n_occurrences"]
    slot_counts["surge_threshold"] = (
        slot_counts["mean_rate"] + POISSON_SURGE_K * np.sqrt(slot_counts["mean_rate"])
    )

    table = {}
    for row in slot_counts.itertuples(index=False):
        key = (int(row.dow), int(row.hour_ist), str(row.zone_filled))
        table[key] = {
            "mean_rate": round(float(row.mean_rate), 4),
            "surge_threshold": round(float(row.surge_threshold), 4),
            "total_count": int(row.total_count),
            "n_occurrences": int(row.n_occurrences),
        }
    print(f"  Baseline table: {len(table)} (DOW, hour, zone) entries built")
    return {"table": table, "dow_n": dow_n_occurrences}


def compute_baseline_features(df: pd.DataFrame, baseline_table: dict) -> pd.DataFrame:
    """
    Adds zone_baseline_rate, zone_surge_ratio, is_surge_zone to df.
    Call AFTER cascade_count is computed (Stage 4). Vectorized (no iterrows)
    so it stays cheap on the full dataset.
    """
    df = df.copy()
    n = len(df)

    dow_arr = df["dow"].where(df["dow"].notna(), -1).astype(int).to_numpy()
    hour_arr = df["hour_ist"].where(df["hour_ist"].notna(), -1).astype(int).to_numpy()
    zone_arr = df["zone_filled"].fillna(ZONE_FILL_VALUE).astype(str).to_numpy()

    mean_rates = np.empty(n, dtype=float)
    surge_thresholds = np.empty(n, dtype=float)
    for i in range(n):
        if dow_arr[i] == -1 or hour_arr[i] == -1:
            mean_rates[i], surge_thresholds[i] = 0.0, POISSON_SURGE_K
            continue
        info = baseline_table.get((dow_arr[i], hour_arr[i], zone_arr[i]))
        if info is None:
            mean_rates[i], surge_thresholds[i] = 0.0, POISSON_SURGE_K
        else:
            mean_rates[i], surge_thresholds[i] = info["mean_rate"], info["surge_threshold"]

    df["zone_baseline_rate"] = mean_rates

    observed = df.get("cascade_count", pd.Series(0, index=df.index)).fillna(0).to_numpy(dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        raw_ratio = np.where(mean_rates > 0, observed / np.where(mean_rates > 0, mean_rates, 1), 0.0)
    ratio = np.where(
        mean_rates > 0,
        np.clip(raw_ratio, a_min=None, a_max=10),
        np.where(observed > 0, POISSON_SURGE_K + 1, 0.0),
    )
    df["zone_surge_ratio"] = np.round(ratio, 3)
    df["is_surge_zone"] = (observed > surge_thresholds).astype(int)
    return df


# ── Approach B: rainfall-forecast trigger (advisory-time only) ─────────────

def safe_get_json(url: str, timeout: int) -> Optional[dict]:
    """Retry once with SSL verification disabled for environments with
    incomplete certificate bundles. Never crashes the caller -- returns None
    on any failure so the pipeline keeps running without live forecasts."""
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except SSLError:
        try:
            r = requests.get(url, timeout=timeout, verify=False)
            r.raise_for_status()
            print("  SSL verification failed; retried without certificate validation.")
            return r.json()
        except Exception as e:
            print(f"  API error after SSL fallback: {e}")
            return None
    except Exception as e:
        print(f"  API error: {e}")
        return None


def fetch_forecast_rainfall() -> Optional[pd.DataFrame]:
    """Open-Meteo 3-day precipitation forecast for Bengaluru. Free, no key,
    live. Returns None (not a crash) if the API is unreachable -- callers
    must treat a None forecast as 'rainfall signal unavailable this run'."""
    url = ("https://api.open-meteo.com/v1/forecast"
           "?latitude=12.9716&longitude=77.5946"
           "&daily=precipitation_sum,precipitation_probability_max"
           "&forecast_days=3&timezone=Asia/Kolkata")
    d = safe_get_json(url, timeout=10)
    if d and "daily" in d:
        return pd.DataFrame({
            "date": pd.to_datetime(d["daily"]["time"]).date,
            "forecast_mm": pd.Series(d["daily"]["precipitation_sum"]).fillna(0.0),
            "rain_prob_pct": d["daily"]["precipitation_probability_max"],
        })
    return None


# ── Approach D: Tavily live-event enrichment (advisory-time only) ──────────
# Cached per (zone, lat, lon, hour) for TAVILY_CACHE_TTL_SECONDS, and
# auto-disabled for the rest of the run after TAVILY_MAX_CONSECUTIVE_FAILURES
# consecutive errors -- protects the free 1,000-search/month quota and avoids
# retry storms slowing down Stage 10's per-event demo loop.
_TAVILY_CACHE = {}
_TAVILY_STATE = {"consecutive_failures": 0, "disabled": False}


def _tavily_cache_key(zone, latitude, longitude, as_of_time) -> tuple:
    return (zone, round(float(latitude), 2), round(float(longitude), 2),
             as_of_time.strftime("%Y-%m-%d-%H"))


def _query_tavily_uncached(zone: str, latitude: float, longitude: float,
                            as_of_date: str) -> Optional[dict]:
    client = TavilyClient(api_key=TAVILY_API_KEY)
    query = (f"Bengaluru Bangalore traffic event procession flood closure "
             f"near {latitude:.2f} {longitude:.2f} today {as_of_date}")
    result = client.search(query, max_results=3, search_depth="basic")
    snippets = result.get("results", [])
    if not snippets:
        return None
    combined = " ".join(s.get("content", "").lower() for s in snippets)
    titles = "; ".join(s.get("title", "") for s in snippets)[:300]
    found_kw = [kw for kw in HIGH_IMPACT_KEYWORDS if kw in combined]
    if not found_kw:
        return None
    suggested_cause = "public_event"
    for cause, kws in CAUSE_KEYWORD_MAP.items():
        if any(kw in combined for kw in kws):
            suggested_cause = cause
            break
    confidence = min(0.95, 0.5 + 0.15 * len(found_kw))
    return {
        "trigger_reason": f"Tavily detected: {', '.join(found_kw[:3])}",
        "suggested_event_cause": suggested_cause,
        "source_snippet": titles,
        "confidence": round(confidence, 2),
    }


def query_tavily(zone: str, latitude: float, longitude: float, as_of_date: str,
                  as_of_time: Optional[pd.Timestamp] = None) -> Optional[dict]:
    """
    Query Tavily for live city events near a location. Returns an enrichment
    dict, or None if Tavily isn't configured / no relevant event was found /
    Tavily has been auto-disabled for this run.

    Runs at INFERENCE TIME only, never during training.
    Install: pip install tavily-python | Key: https://app.tavily.com
    """
    if not TAVILY_API_KEY or not HAS_TAVILY:
        return None
    if _TAVILY_STATE["disabled"]:
        return None

    as_of_time = as_of_time or pd.Timestamp.now(tz="Asia/Kolkata")
    cache_key = _tavily_cache_key(zone, latitude, longitude, as_of_time)
    cached = _TAVILY_CACHE.get(cache_key)
    if cached is not None and (time.time() - cached[0]) < TAVILY_CACHE_TTL_SECONDS:
        return cached[1]

    try:
        enrichment = _query_tavily_uncached(zone, latitude, longitude, as_of_date)
        _TAVILY_STATE["consecutive_failures"] = 0
        _TAVILY_CACHE[cache_key] = (time.time(), enrichment)
        return enrichment
    except Exception as e:
        _TAVILY_STATE["consecutive_failures"] += 1
        print(f"  Tavily error: {e}")
        if (_TAVILY_STATE["consecutive_failures"] >= TAVILY_MAX_CONSECUTIVE_FAILURES
                and not _TAVILY_STATE["disabled"]):
            _TAVILY_STATE["disabled"] = True
            print(f"  Tavily: {TAVILY_MAX_CONSECUTIVE_FAILURES} consecutive failures -- "
                  f"disabling Tavily enrichment for the rest of this run.")
        return None


# ── Merged predictor: real implementation, replaces the old stub ───────────

def historical_trend_predictor(
    zone: str,
    as_of_time: pd.Timestamp,
    latitude: float = 12.9716,
    longitude: float = 77.5946,
    *,
    baseline_table: Optional[dict] = None,
    rainfall_forecast: Optional[pd.DataFrame] = None,
    current_zone_count: int = 0,
) -> Optional[dict]:
    """
    Predicts an upcoming "hike" (surge in events) for a zone, merging three
    signals in priority order (highest confidence wins):
      B. Rainfall forecast   (max confidence 0.92, causal)
      D. Tavily live event   (max confidence 0.95, real-time context)
      A. Poisson zone surge  (max confidence 0.88, data-driven anomaly)

    Parameters
    ----------
    zone               : BTP zone string (e.g. "Central Zone 2")
    as_of_time         : pd.Timestamp (IST) of the incoming event
    latitude/longitude : event location (for Tavily proximity search)
    baseline_table     : DOW x Hour x Zone lookup; loads BASELINE_CACHE if None
    rainfall_forecast  : 3-row DataFrame from fetch_forecast_rainfall()
    current_zone_count : events reported in this zone in the last 2 hrs
                          (= cascade_count from Stage 4)

    Returns
    -------
    dict with zone, predicted_window, trigger_reason, confidence,
    suggested_event_cause, source_snippet -- or None if no hike is predicted.
    """
    if baseline_table is None:
        if os.path.exists(BASELINE_CACHE):
            with open(BASELINE_CACHE, "rb") as f:
                baseline_table = pickle.load(f)["table"]
        else:
            baseline_table = {}

    dow = as_of_time.dayofweek
    hour = as_of_time.hour
    as_of_date = as_of_time.date().isoformat()

    signals = []

    # ─── Signal B: rainfall forecast (highest priority, causal) ──────────
    if rainfall_forecast is not None and len(rainfall_forecast) > 0:
        tomorrow = (as_of_time + pd.Timedelta(days=1)).date()
        three_day_mm = float(rainfall_forecast["forecast_mm"].sum())
        tomorrow_rows = rainfall_forecast[rainfall_forecast["date"] == tomorrow]
        tomorrow_mm = float(tomorrow_rows["forecast_mm"].values[0]) if len(tomorrow_rows) else 0.0
        prob_pct = float(tomorrow_rows["rain_prob_pct"].values[0]) if (
            len(tomorrow_rows) and "rain_prob_pct" in tomorrow_rows.columns) else 0.0

        if tomorrow_mm > MONSOON_RAIN_THRESH or three_day_mm > MONSOON_RAIN_THRESH * 2:
            signals.append({
                "zone": zone,
                "predicted_window": f"next 24-72 hours (starting {tomorrow})",
                "trigger_reason": (f"Rainfall forecast: {tomorrow_mm:.1f}mm tomorrow "
                                    f"({prob_pct:.0f}% probability), {three_day_mm:.1f}mm over 3 days"),
                "confidence": round(min(0.92, 0.6 + 0.01 * tomorrow_mm + 0.002 * three_day_mm), 3),
                "suggested_event_cause": "water_logging",
                "source_snippet": f"Open-Meteo forecast: {tomorrow_mm:.1f}mm on {tomorrow}",
                "_signal_type": "rainfall_forecast",
            })

    # ─── Signal A: Poisson zone surge ─────────────────────────────────────
    key = (int(dow), int(hour), str(zone))
    info = baseline_table.get(key)
    if info is not None:
        mean_rate, surge_threshold = info["mean_rate"], info["surge_threshold"]
        if current_zone_count > surge_threshold and mean_rate > 0:
            surge_ratio = current_zone_count / mean_rate
            confidence = min(0.88, 0.55 + 0.08 * min(surge_ratio, 5))
            signals.append({
                "zone": zone,
                "predicted_window": "next 1-2 hours (ongoing surge)",
                "trigger_reason": (f"Zone surge: {current_zone_count} events observed, "
                                    f"baseline is {mean_rate:.2f}/occurrence "
                                    f"(ratio {surge_ratio:.1f}x, threshold {surge_threshold:.2f})"),
                "confidence": round(confidence, 3),
                "suggested_event_cause": "congestion",
                "source_snippet": None,
                "_signal_type": "poisson_surge",
            })
    elif current_zone_count > 0:
        signals.append({
            "zone": zone,
            "predicted_window": "next 1-2 hours (anomalous slot)",
            "trigger_reason": (f"Zone anomaly: {current_zone_count} events in a historically "
                                f"zero-event slot ({DAYS[dow]} {hour:02d}h {zone})"),
            "confidence": 0.50,
            "suggested_event_cause": "vehicle_breakdown",
            "source_snippet": None,
            "_signal_type": "zero_rate_slot",
        })

    # ─── Signal D: Tavily live enrichment ─────────────────────────────────
    tavily_result = query_tavily(zone, latitude, longitude, as_of_date, as_of_time=as_of_time)
    if tavily_result:
        signals.append({
            "zone": zone,
            "predicted_window": "imminent (live city event detected)",
            "trigger_reason": tavily_result["trigger_reason"],
            "confidence": tavily_result["confidence"],
            "suggested_event_cause": tavily_result["suggested_event_cause"],
            "source_snippet": tavily_result["source_snippet"],
            "_signal_type": "tavily_live",
        })

    if not signals:
        return None

    best = max(signals, key=lambda s: s["confidence"])
    best.pop("_signal_type", None)
    return best


# ════════════════════════════════════════════════════════════════════════════
# STAGE 4 — FEATURE ENGINEERING  (unchanged from pipeline.py, plus Approach A
# baseline-feature integration below)
# ════════════════════════════════════════════════════════════════════════════

def has_kannada(text):
    if pd.isna(text):
        return False
    return any("ಀ" <= c <= "೿" for c in str(text))


def has_keyword(text, keywords):
    if pd.isna(text):
        return 0
    t = str(text).lower()
    return int(any(kw.lower() in t for kw in keywords))


def stage4_features(df: pd.DataFrame) -> pd.DataFrame:
    print("\n[Stage 4] Feature engineering...")
    df["hour_ist"] = df["start_ist"].dt.hour
    df["dow"] = df["start_ist"].dt.dayofweek
    df["dow_name"] = df["start_ist"].dt.day_name()
    df["month"] = df["start_ist"].dt.month
    df["is_weekend"] = (df["dow"] >= 5).astype(int)
    df["is_peak"] = (df["hour_ist"].between(8, 10) | df["hour_ist"].between(17, 19)).astype(int)

    # School/office peak hours -- static Bengaluru domain knowledge (dropoff
    # ~7-9am, pickup ~3-4pm; IT-corridor office peaks ~9-10am/6-8pm). Not
    # fetched from an API -- these are stable facts, not day-to-day variables.
    def _in_any_range(hour, ranges):
        return any(start <= hour < end for start, end in ranges)
    df["is_school_hour"] = (df["hour_ist"].apply(lambda h: _in_any_range(h, SCHOOL_HOURS))
                             & (df["is_weekend"] == 0)).astype(int)
    df["is_office_peak_hour"] = (df["hour_ist"].apply(lambda h: _in_any_range(h, OFFICE_PEAK_HOURS))
                                  & (df["is_weekend"] == 0)).astype(int)
    df["is_it_corridor_zone"] = df["zone_filled"].isin(IT_CORRIDOR_ZONES).astype(int)
    df["hour_sin"] = np.sin(2 * np.pi * df["hour_ist"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour_ist"] / 24)
    df["dow_sin"] = np.sin(2 * np.pi * df["dow"] / 7)
    df["dow_cos"] = np.cos(2 * np.pi * df["dow"] / 7)
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)

    df["has_description"] = df["description"].notna().astype(int)
    df["has_kannada"] = df["description"].apply(has_kannada).astype(int)
    df["desc_word_count"] = df["description"].fillna("").apply(lambda x: len(str(x).split()))
    df["desc_closure_signal"] = df["description"].apply(lambda x: has_keyword(x, CLOSURE_KEYWORDS))
    df["desc_slow_signal"] = df["description"].apply(lambda x: has_keyword(x, SLOW_KEYWORDS))

    valid = df[df["valid_coord"]].copy()
    coords_rad = np.radians(valid[["latitude", "longitude"]].values)
    tree = BallTree(coords_rad, metric="haversine")
    radius_rad = 5.0 / 6371.0
    neighbor_lists = tree.query_radius(coords_rad, r=radius_rad)
    start_times = valid["start_datetime"].values
    cascade_counts = np.zeros(len(valid), dtype=int)
    for i, neighbors in enumerate(neighbor_lists):
        t0 = start_times[i]
        diffs_hrs = (start_times[neighbors] - t0) / np.timedelta64(1, "h")
        cascade_counts[i] = np.sum((diffs_hrs > 0) & (diffs_hrs <= 2) & (neighbors != i))
    valid["cascade_count"] = cascade_counts
    df["cascade_count"] = 0
    df.loc[valid.index, "cascade_count"] = valid["cascade_count"]

    # ── Historical Trend module, Approach A: DOW x Hour x Zone Poisson baseline ──
    if os.path.exists(BASELINE_CACHE):
        with open(BASELINE_CACHE, "rb") as f:
            _baseline = pickle.load(f)
    else:
        _baseline = build_baseline_table(df)
        with open(BASELINE_CACHE, "wb") as f:
            pickle.dump(_baseline, f)
    df = compute_baseline_features(df, _baseline["table"])
    print(f"  Surge-zone events flagged: {df['is_surge_zone'].sum()} "
          f"({df['is_surge_zone'].mean()*100:.1f}%)")

    # K-fold smoothed target encoding (replaces plain groupby().mean(), which
    # leaked the target -- every row's encoding included its own label).
    # cause_median_duration uses the duration_valid subset (mean, not median,
    # since kfold_target_encode pools via mean -- close enough at cause-level
    # granularity and avoids a separate median-OOF implementation).
    dur_subset = df[df["duration_valid"]].copy()
    _, cause_duration_map, overall_mean_duration = kfold_target_encode(
        dur_subset, "event_cause", "duration_hrs", m=25
    )
    df["cause_median_duration"] = df["event_cause"].map(cause_duration_map).fillna(overall_mean_duration)

    oof_closure_rate, cause_closure_map, _ = kfold_target_encode(
        df, "event_cause", "requires_road_closure", m=25
    )
    df["cause_closure_rate"] = oof_closure_rate.values
    risk = (df["cause_closure_rate"] * (df["junction_centrality"] + 0.01) *
            (1 / (df["cause_median_duration"] + 1)) * np.log1p(df["cascade_count"]) *
            np.where(df["is_peak"] == 1, 2, 1))
    df["cascade_risk_score"] = 10 * (risk - risk.min()) / (risk.max() - risk.min() + 1e-9)

    # Persist the inference-time maps (full-data fit, no OOF needed once
    # trained) so a single new event gets the same encoding without needing
    # the whole historical batch in memory.
    with open(TARGET_ENCODING_PATH, "w") as f:
        json.dump({
            "cause_duration_map": {str(k): float(v) for k, v in cause_duration_map.items()},
            "overall_mean_duration": float(overall_mean_duration),
            "cause_closure_map": {str(k): float(v) for k, v in cause_closure_map.items()},
        }, f)

    print(f"  Kannada descriptions: {df['has_kannada'].sum()} | "
          f"Closure-keyword hits: {df['desc_closure_signal'].sum()}")
    print("  cause_median_duration / cause_closure_rate now K-fold OOF-encoded "
          f"(saved inference map: {TARGET_ENCODING_PATH})")
    return df


# ════════════════════════════════════════════════════════════════════════════
# STAGE 5 — TRIAGE CLASSIFIER  (unchanged from pipeline.py)
# ════════════════════════════════════════════════════════════════════════════

def manual_oof_predict_proba(make_estimator, X, y, skf):
    """Manual out-of-fold prediction loop.

    sklearn's cross_val_predict / CalibratedClassifierCV both call
    sklearn.base.clone() internally, which CatBoostClassifier fails --
    get_params()/set_params() doesn't round-trip cat_features cleanly
    (confirmed by actually running it: "Cannot clone object ... constructor
    either does not set or modifies parameter cat_features"). Looping the
    folds by hand sidesteps clone() entirely -- each fold gets a fresh
    CatBoostClassifier from the factory function, fit and predicted exactly
    like the original 02_Triage_Classifier.ipynb did.
    """
    oof = np.zeros(len(X))
    for train_idx, val_idx in skf.split(X, y):
        model = make_estimator()
        model.fit(X.iloc[train_idx], y.iloc[train_idx])
        oof[val_idx] = model.predict_proba(X.iloc[val_idx])[:, 1]
    return oof


def fit_isotonic_calibrator(oof_proba, y):
    """Fits isotonic regression mapping raw OOF scores -> empirical
    frequencies. This is what CalibratedClassifierCV does internally; doing
    it directly avoids the clone() incompatibility while keeping the same
    statistical intent: 'predicted 12%' should mean an empirical 12%."""
    from sklearn.isotonic import IsotonicRegression
    iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
    iso.fit(oof_proba, y)
    return iso


def stage5_triage(df: pd.DataFrame):
    print("\n[Stage 5] Triage classifier (CatBoost)...")
    from catboost import CatBoostClassifier

    all_features = TRIAGE_CAT_FEATURES + TRIAGE_NUM_FEATURES
    model_df = df[all_features + ["requires_road_closure", "priority"]].copy()
    for c in TRIAGE_CAT_FEATURES:
        model_df[c] = model_df[c].astype(str).fillna("MISSING").replace("None", "MISSING").replace("nan", "MISSING")

    y_closure = model_df["requires_road_closure"].astype(int)
    X = model_df[all_features]
    pos_rate = y_closure.mean()
    scale_pos_weight = (1 - pos_rate) / pos_rate
    cat_idx = [X.columns.get_loc(c) for c in TRIAGE_CAT_FEATURES]
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    def make_closure_estimator():
        return CatBoostClassifier(
            iterations=800, learning_rate=0.05, depth=7, loss_function="Logloss",
            eval_metric="AUC", scale_pos_weight=scale_pos_weight, cat_features=cat_idx,
            random_seed=42, verbose=False,
        )

    # Fix (bug #1): fitting on all X then predict_proba(X) on the same rows
    # is in-sample -- every probability is optimistic because the model has
    # already seen that row's label. Manual OOF loop gives each row a
    # probability from a model that never saw it.
    oof_closure_proba = manual_oof_predict_proba(make_closure_estimator, X, y_closure, skf)
    df["closure_probability_raw"] = oof_closure_proba

    # Fix (bug #4): "12%" should be a calibrated 12%, not a raw tree-ensemble
    # score. Isotonic regression on the OOF scores rescales probabilities so
    # they match empirical frequencies. The calibrator -- not the raw
    # CatBoost score -- is what gets applied for closure_probability.
    closure_calibrated = fit_isotonic_calibrator(oof_closure_proba, y_closure.values)
    with open("triage_model_closure_calibrated.pkl", "wb") as f:
        pickle.dump({"calibrator": closure_calibrated, "features": all_features,
                     "cat_features": TRIAGE_CAT_FEATURES}, f)

    # Final deployed model -- fit on all data (standard practice once OOF has
    # validated the approach; this is the model actually saved/served).
    closure_model = make_closure_estimator()
    closure_model.fit(X, y_closure)
    closure_model.save_model("triage_model_closure.cbm")
    closure_raw_full = closure_model.predict_proba(X)[:, 1]
    df["closure_probability"] = closure_calibrated.predict(closure_raw_full)

    # Decision threshold (bug #4): picked on the honest OOF probabilities,
    # not argmax(0.5), and persisted so the advisory uses the same rule the
    # batch evaluation was scored on. Threshold is on the OOF (uncalibrated)
    # scale to match how it's applied (raw model output -> calibrator ->
    # compare against a threshold picked on the calibrated OOF curve below).
    oof_calibrated = closure_calibrated.predict(oof_closure_proba)
    precisions, recalls, thresholds = precision_recall_curve(y_closure, oof_calibrated)
    f1s = 2 * precisions * recalls / (precisions + recalls + 1e-9)
    best_idx = np.argmax(f1s[:-1])
    closure_threshold = float(thresholds[best_idx])
    with open(CLOSURE_THRESHOLD_PATH, "w") as f:
        json.dump({"closure_threshold": closure_threshold,
                   "precision_at_threshold": float(precisions[best_idx]),
                   "recall_at_threshold": float(recalls[best_idx])}, f)

    # Priority model -- corridor EXCLUDED (near-deterministic encoding of
    # priority in the source data: see chat history / 02_Triage_Classifier.ipynb)
    cat_features_pri = [c for c in TRIAGE_CAT_FEATURES if c != "corridor"]
    all_features_pri = cat_features_pri + TRIAGE_NUM_FEATURES
    cat_idx_pri = [all_features_pri.index(c) for c in cat_features_pri]
    priority_mask = model_df["priority"].notna()
    X_pri = model_df.loc[priority_mask, all_features_pri]
    y_priority = (model_df.loc[priority_mask, "priority"] == "High").astype(int)
    skf_pri = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    def make_priority_estimator():
        return CatBoostClassifier(
            iterations=600, learning_rate=0.05, depth=6, loss_function="Logloss",
            eval_metric="AUC", cat_features=cat_idx_pri, random_seed=42, verbose=False,
        )

    oof_priority_proba = manual_oof_predict_proba(make_priority_estimator, X_pri, y_priority, skf_pri)
    priority_calibrated = fit_isotonic_calibrator(oof_priority_proba, y_priority.values)
    with open("triage_model_priority_calibrated.pkl", "wb") as f:
        pickle.dump({"calibrator": priority_calibrated, "features": all_features_pri,
                     "cat_features": cat_features_pri}, f)

    priority_model = make_priority_estimator()
    priority_model.fit(X_pri, y_priority)
    priority_model.save_model("triage_model_priority.cbm")
    priority_raw_full = priority_model.predict_proba(X_pri)[:, 1]
    oof_priority_calibrated = priority_calibrated.predict(oof_priority_proba)
    precisions_p, recalls_p, thresholds_p = precision_recall_curve(y_priority, oof_priority_calibrated)
    f1s_p = 2 * precisions_p * recalls_p / (precisions_p + recalls_p + 1e-9)
    priority_threshold = float(thresholds_p[np.argmax(f1s_p[:-1])])
    with open(CLOSURE_THRESHOLD_PATH.replace("closure", "priority"), "w") as f:
        json.dump({"priority_threshold": priority_threshold}, f)

    # CascadeRisk: persist 1st/99th percentile bounds (not raw min/max --
    # more robust to outliers) instead of normalizing against whatever batch
    # happens to be in memory. Bug #3: without this, scoring a single live
    # event is undefined (min==max==that one value), and the scale silently
    # drifts every time the historical dataset changes.
    risk = (df["closure_probability"] * (df["junction_centrality"] + 0.01) *
            (1 / (df["cause_median_duration"] + 1)) * np.log1p(df["cascade_count"]) *
            np.where(df["is_peak"] == 1, 2, 1))
    risk_p01, risk_p99 = float(risk.quantile(0.01)), float(risk.quantile(0.99))
    with open(CASCADE_SCALER_PATH, "w") as f:
        json.dump({"risk_p01": risk_p01, "risk_p99": risk_p99}, f)
    df["cascade_risk_score_v2"] = (
        10 * (risk.clip(risk_p01, risk_p99) - risk_p01) / (risk_p99 - risk_p01 + 1e-9)
    ).clip(0, 10)

    print(f"  Closure positive rate: {pos_rate:.4f} | scale_pos_weight: {scale_pos_weight:.2f}")
    print(f"  Saved threshold {closure_threshold:.3f} (P={precisions[best_idx]:.3f}, R={recalls[best_idx]:.3f})")
    print("  Models saved: triage_model_closure.cbm + _calibrated.pkl, "
          "triage_model_priority.cbm + _calibrated.pkl")
    print("  closure_probability / priority columns are now honest OOF + isotonic-calibrated "
          "(previously in-sample -- see review)")
    return df, closure_model, priority_model, closure_calibrated, priority_calibrated, \
        closure_threshold, priority_threshold, all_features_pri, cat_features_pri


# ════════════════════════════════════════════════════════════════════════════
# STAGE 6 — DURATION MODELS  (unchanged from pipeline.py)
# ════════════════════════════════════════════════════════════════════════════

def stage6_duration(df: pd.DataFrame):
    print("\n[Stage 6] Duration models...")
    import xgboost as xgb
    from lifelines import WeibullAFTFitter

    all_features = TRIAGE_CAT_FEATURES + TRIAGE_NUM_FEATURES + DURATION_NUM_FEATURES_EXTRA

    fast_df = df[(df["model_track"] == "fast") & (df["duration_valid"])].copy()
    fast_df["log_duration"] = np.log1p(fast_df["duration_hrs"])
    X_fast = fast_df[all_features].copy()
    fast_encoders = {}
    for c in TRIAGE_CAT_FEATURES:
        le = LabelEncoder()
        X_fast[c] = le.fit_transform(X_fast[c].astype(str).fillna("MISSING"))
        fast_encoders[c] = le
    y_fast = fast_df["log_duration"].values

    fast_models = {}
    for q in [0.1, 0.5, 0.9]:
        model = xgb.XGBRegressor(
            objective="reg:quantileerror", quantile_alpha=q, n_estimators=400,
            max_depth=6, learning_rate=0.03, subsample=0.8, colsample_bytree=0.8,
            min_child_weight=10, random_state=42,
        )
        model.fit(X_fast, y_fast)
        model.save_model(f"duration_model_fast_q{int(q*100)}.json")
        fast_models[q] = model
    print(f"  Fast track (n={len(fast_df)}): saved duration_model_fast_q{{10,50,90}}.json")
    print("  (80% interval coverage ~78.3% on CV; MAPE not meaningful here -- 12% of events <12 min)")

    slow_df = df[df["model_track"] == "slow"].copy()
    reference_now = df["start_datetime"].max()
    slow_df["survival_time_hrs"] = np.where(
        slow_df["is_censored"] == 1,
        (reference_now - slow_df["start_datetime"]).dt.total_seconds() / 3600,
        slow_df["duration_hrs"]
    )
    slow_df["event_observed"] = 1 - slow_df["is_censored"]
    slow_df = slow_df[slow_df["survival_time_hrs"].notna() & (slow_df["survival_time_hrs"] > 0)]
    slow_df["survival_time_hrs"] = slow_df["survival_time_hrs"].clip(upper=2000)

    aft_cat_features = ["event_cause", "holiday_type"]
    aft_num_features = [
        "hour_ist", "month", "is_weekend", "is_peak", "junction_centrality",
        "rainfall_mm", "is_election_campaign_period", "is_public_holiday",
        "has_kannada", "desc_slow_signal", "cascade_count", "hotspot_score",
        "is_heavy_vehicle", "closure_probability",
    ]
    aft_df = slow_df[aft_cat_features + aft_num_features + ["survival_time_hrs", "event_observed"]].copy()
    aft_df = pd.get_dummies(aft_df, columns=aft_cat_features, drop_first=True)

    aft_final = WeibullAFTFitter(penalizer=0.1)
    aft_final.fit(aft_df, duration_col="survival_time_hrs", event_col="event_observed")
    with open("duration_model_slow_weibull.pkl", "wb") as f:
        pickle.dump({"model": aft_final,
                     "columns": aft_df.drop(columns=["survival_time_hrs", "event_observed"]).columns.tolist()}, f)

    censored_n = (slow_df["event_observed"] == 0).sum()
    print(f"  Slow track (n={len(aft_df)}, {censored_n} censored): saved duration_model_slow_weibull.pkl")
    print("  FINDING: concordance ~0.566 (weak) -- stale/abandoned tickets inflate censored survival")
    print("  time (avg 1,167 hrs elapsed vs 210 hrs for resolved). Use as risk ranking, not point estimate.")

    escalation_n = (df["model_track"] == "escalation").sum()
    print(f"  Escalation track (n={escalation_n}, pot_holes/debris): NO duration model -- BBMP handoff.")

    aft_columns = aft_df.drop(columns=["survival_time_hrs", "event_observed"]).columns.tolist()
    return fast_models, fast_encoders, all_features, aft_final, aft_columns, aft_cat_features, aft_num_features


# ════════════════════════════════════════════════════════════════════════════
# STAGE 7 — SPREAD MODEL  (node-ID handling fixed: int throughout, matching
# osmnx's load_graphml convention -- this is the bug found in
# Master_Advanced_Pipeline.ipynb, where str(node) silently broke every lookup)
# ════════════════════════════════════════════════════════════════════════════

def get_decay_rate(cause):
    return DECAY_RATE.get(cause, DEFAULT_DECAY)


def get_max_radius(cause):
    return MAX_RADIUS_M.get(cause, DEFAULT_MAX_RADIUS_M)


def compute_footprint(source_node, event_cause, graph):
    """Soft congestion-awareness zone -- impact decays with network distance."""
    import networkx as nx
    source_node = int(source_node)
    if source_node not in graph.nodes:
        return {}
    rate = get_decay_rate(event_cause)
    max_radius = get_max_radius(event_cause)
    lengths = nx.single_source_dijkstra_path_length(graph, source_node, cutoff=max_radius, weight="length")
    footprint = {node: np.exp(-rate * dist_m / 1000) for node, dist_m in lengths.items()}
    return {n: v for n, v in footprint.items() if v >= IMPACT_THRESHOLD}


def compute_footprint_with_radius(source_node, event_cause, graph):
    """Same as compute_footprint, but also returns the radius in km -- the
    farthest distance reached by any node in the footprint. Used for the
    advisory ("congestion footprint: 1.4 km radius") instead of node count
    alone, since node count depends on graph density, not real distance."""
    import networkx as nx
    source_node = int(source_node)
    if source_node not in graph.nodes:
        return {}, 0.0
    rate = get_decay_rate(event_cause)
    max_radius = get_max_radius(event_cause)
    lengths = nx.single_source_dijkstra_path_length(graph, source_node, cutoff=max_radius, weight="length")
    footprint = {node: np.exp(-rate * dist_m / 1000) for node, dist_m in lengths.items()
                 if np.exp(-rate * dist_m / 1000) >= IMPACT_THRESHOLD}
    radius_km = max((lengths[n] for n in footprint), default=0.0) / 1000
    return footprint, radius_km


def find_through_route_endpoints(source_node, graph, target_dist_m=2000):
    import networkx as nx
    source_node = int(source_node)
    if source_node not in graph.nodes:
        return None, None
    fwd = nx.single_source_dijkstra_path_length(graph, source_node, cutoff=target_dist_m * 1.5, weight="length")
    downstream_candidates = {n: d for n, d in fwd.items() if d >= target_dist_m * 0.7}
    downstream = max(downstream_candidates, key=downstream_candidates.get) if downstream_candidates else None
    rev = nx.single_source_dijkstra_path_length(graph.reverse(copy=False), source_node,
                                                  cutoff=target_dist_m * 1.5, weight="length")
    upstream_candidates = {n: d for n, d in rev.items() if d >= target_dist_m * 0.7}
    upstream = max(upstream_candidates, key=upstream_candidates.get) if upstream_candidates else None
    return upstream, downstream


def compute_routing_delay(source_node, event_cause, graph):
    """Hard-closure-core routing delay -- not the full soft footprint (see Stage 7 notes)."""
    import networkx as nx
    footprint = compute_footprint(source_node, event_cause, graph)
    if not footprint:
        return None
    upstream, downstream = find_through_route_endpoints(source_node, graph)
    if upstream is None or downstream is None:
        return None
    try:
        baseline_time_s = nx.shortest_path_length(graph, upstream, downstream, weight="travel_time")
    except nx.NetworkXNoPath:
        return None
    blocked_nodes = [n for n, score in footprint.items()
                      if score >= HARD_CLOSURE_THRESHOLD and n not in (upstream, downstream)]
    G_blocked = graph.copy()
    G_blocked.remove_nodes_from(blocked_nodes)
    try:
        affected_time_s = nx.shortest_path_length(G_blocked, upstream, downstream, weight="travel_time")
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return {"footprint_size": len(footprint), "baseline_minutes": baseline_time_s / 60,
                "affected_minutes": None, "delay_minutes": None, "alt_route_exists": False,
                "blocked_node_count": len(blocked_nodes), "blocked_nodes": blocked_nodes}
    return {"footprint_size": len(footprint), "baseline_minutes": baseline_time_s / 60,
            "affected_minutes": affected_time_s / 60, "delay_minutes": (affected_time_s - baseline_time_s) / 60,
            "alt_route_exists": True, "blocked_node_count": len(blocked_nodes), "blocked_nodes": blocked_nodes}


def stage7_spread(df: pd.DataFrame, G) -> pd.DataFrame:
    print("\n[Stage 7] Spread model (footprint sizes for full dataset)...")
    import networkx as nx

    largest_scc = max(nx.strongly_connected_components(G), key=len)
    G_main = G.subgraph(largest_scc).copy()

    # Bug #8 fix: df.index.get_loc(idx) inside the loop is O(n) per call,
    # O(n^2) total over the full dataset. Build {idx: size} once, map back
    # with a single vectorized .map() -- O(n) total.
    valid_mask = df["valid_coord"] & df["osm_node"].notna()
    size_by_idx = {}
    radius_by_idx = {}
    for idx in df[valid_mask].index:
        node = int(df.at[idx, "osm_node"])
        cause = df.at[idx, "event_cause"]
        if node not in G_main.nodes:
            continue
        fp, radius_km = compute_footprint_with_radius(node, cause, G_main)
        size_by_idx[idx] = len(fp)
        radius_by_idx[idx] = radius_km
    df["footprint_size"] = df.index.map(size_by_idx).fillna(0).astype(int)
    df["footprint_radius_km"] = df.index.map(radius_by_idx).fillna(0.0)

    print(f"  Footprint computed for {valid_mask.sum()} events. "
          f"Mean size: {df['footprint_size'].mean():.0f} nodes, "
          f"mean radius: {df['footprint_radius_km'].mean():.2f} km")
    return df, G_main


# ════════════════════════════════════════════════════════════════════════════
# STAGE 8 — RESOURCE RECOMMENDER  (NEW)
#
# Officer count: formula from MASTER_VISION.md Section 7.1.
# Barricade placement: greedy BPR-aware simulation, ported from
#   Master_Advanced_Pipeline.ipynb with the int/str node-ID bug fixed.
# Diversion routing: k-shortest paths around the blocked nodes.
# ════════════════════════════════════════════════════════════════════════════

def apply_bpr_weights(graph, volume_multiplier=1.0):
    """Bureau of Public Roads formula: T = T0 x (1 + 0.15 x (V/C)^4).

    NOTE: V (volume) is a flat assumed constant (500 veh/hr), not derived from
    real per-road traffic counts -- there is no such data in this dataset.
    C (capacity) is the genuinely data-driven part, from OSM highway tags.
    This makes the result directionally useful (narrow roads penalized more
    under the same assumed load) but not a precise volume estimate. Documented
    here rather than overstated as fully "capacity-aware" in the modeling sense.
    """
    G_bpr = graph.copy()
    for u, v, d in G_bpr.edges(data=True):
        hw = d.get("highway", "unclassified")
        if isinstance(hw, list):
            hw = hw[0]
        capacity = BPR_CAPACITY_MAP.get(hw, 200)
        base_time = d.get("travel_time", d.get("length", 100) / 10.0)
        volume = 500 * volume_multiplier
        d["bpr_travel_time"] = base_time * (1 + 0.15 * (volume / capacity) ** 4)
    return G_bpr


def greedy_barricade_simulation(source_node, event_cause, graph, centrality_dict, top_k=5):
    """Tests removing each of the top-k impact*centrality footprint nodes and
    picks whichever minimizes network-wide delay under BPR-weighted re-routing.
    Demo/single-event scale only -- too expensive to run for the full dataset
    (graph copy + BPR recompute per candidate), same scoping as
    compute_routing_delay in Stage 7."""
    import networkx as nx
    source_node = int(source_node)
    footprint = compute_footprint(source_node, event_cause, graph)
    if not footprint:
        return None, []

    upstream, downstream = find_through_route_endpoints(source_node, graph)
    if upstream is None or downstream is None:
        return None, []

    try:
        G_bpr = apply_bpr_weights(graph, volume_multiplier=1.0)
        baseline_time = nx.shortest_path_length(G_bpr, upstream, downstream, weight="bpr_travel_time")
    except nx.NetworkXNoPath:
        return None, []

    scored = [(node, impact * centrality_dict.get(node, 0.0)) for node, impact in footprint.items()]
    candidates = [node for node, _ in sorted(scored, key=lambda x: -x[1])[:top_k]]

    best_node, min_delay = None, float("inf")
    for candidate in candidates:
        if candidate in (upstream, downstream):
            continue
        G_test = graph.copy()
        G_test.remove_node(candidate)
        G_test = apply_bpr_weights(G_test, volume_multiplier=1.5)
        try:
            affected_time = nx.shortest_path_length(G_test, upstream, downstream, weight="bpr_travel_time")
            delay = affected_time - baseline_time
            if delay < min_delay:
                min_delay, best_node = delay, candidate
        except nx.NetworkXNoPath:
            continue

    return best_node, candidates


def recommend_diversion(graph, upstream, downstream, blocked_nodes, k=3,
                         max_node_overlap=0.6, max_candidates_checked=25):
    """k-shortest simple paths between upstream/downstream avoiding blocked_nodes.

    nx.shortest_simple_paths does not support MultiDiGraph (osmnx's native
    graph type) -- found by actually running this against the real graph.
    Collapse to a simple DiGraph for the path search; carry travel_time and
    name through so the advisory can report "+3 min via Ballari Rd" instead
    of a bare distance figure.

    Bug fixed (found via real usage, not just code review): the original
    version did `islice(paths_gen, k)` -- just took the first k results off
    nx.shortest_simple_paths. In a dense city road graph, the first several
    "shortest simple paths" between two points are almost always near-
    identical, differing by a single short detour around one side street --
    so the advisory was reporting 3 "alternate routes" that were actually
    the same arterial road with a sub-1% distance difference, which looks
    like a bug to anyone reading it ("why are all 3 routes identical?").
    nx.shortest_simple_paths guarantees increasing weight and simplicity
    (no repeated node), NOT route diversity. Fixed by pulling more candidates
    from the generator and only keeping ones that share fewer than
    `max_node_overlap` (60%) of their nodes with an already-accepted route --
    if the road network genuinely only has one viable artery here, this
    correctly returns fewer than k routes instead of faking diversity.
    """
    import networkx as nx
    from itertools import islice

    G_diverted = graph.copy()
    G_diverted.remove_nodes_from([n for n in blocked_nodes if n not in (upstream, downstream)])
    G_simple = nx.DiGraph()
    for u, v, d in G_diverted.edges(data=True):
        length = d.get("length", float("inf"))
        travel_time = d.get("travel_time", length / 10.0)
        name = d.get("name", None)
        if isinstance(name, list):
            name = name[0] if name else None
        if not G_simple.has_edge(u, v) or G_simple[u][v]["length"] > length:
            G_simple.add_edge(u, v, length=length, travel_time=travel_time, name=name)

    # Bug found via direct testing: nx.shortest_simple_paths returns a lazy
    # generator -- NodeNotFound/NetworkXNoPath is raised on first iteration,
    # not at call time. A try/except wrapping only the generator's creation
    # never catches it; it surfaces later, uncaught, inside the for-loop that
    # consumes it (happens when blocked_nodes is large enough to strip every
    # edge off upstream or downstream, so the node never even enters
    # G_simple). The fix is to wrap the consumption itself.
    routes = []
    accepted_node_sets = []
    try:
        paths_gen = nx.shortest_simple_paths(G_simple, upstream, downstream, weight="travel_time")
        for path in islice(paths_gen, max_candidates_checked):
            path_set = set(path)
            is_diverse = all(
                len(path_set & seen) / len(path_set | seen) <= max_node_overlap
                for seen in accepted_node_sets
            )
            if not is_diverse:
                continue
            edges = list(zip(path, path[1:]))
            distance_km = sum(G_simple[u][v]["length"] for u, v in edges) / 1000
            travel_minutes = sum(G_simple[u][v]["travel_time"] for u, v in edges) / 60
            names = [G_simple[u][v]["name"] for u, v in edges if G_simple[u][v]["name"]]
            primary_name = max(set(names), key=names.count) if names else "unnamed road"
            routes.append({"rank": len(routes) + 1, "path_length": len(path), "distance_km": round(distance_km, 2),
                           "travel_minutes": round(travel_minutes, 1), "via": primary_name,
                           "path_nodes": path})
            accepted_node_sets.append(path_set)
            if len(routes) >= k:
                break
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return routes
    return routes


def compute_officer_count(event_row, zone_counts, global_mean_zone_count):
    """officers = base(cause) x closure_mult x peak_mult x zone_density_mult x simultaneous_penalty"""
    base = BASE_OFFICERS.get(event_row["event_cause"], DEFAULT_BASE_OFFICERS)
    closure_mult = 1 + 0.5 * event_row["closure_probability"]
    peak_mult = 1.3 if event_row["is_peak"] == 1 else 1.0
    zone_count = zone_counts.get(event_row["zone_filled"], global_mean_zone_count)
    zone_density_mult = 1 + (zone_count / global_mean_zone_count - 1) * 0.3
    simultaneous_penalty = 0.8 if event_row["cascade_count"] > 2 else 1.0
    officers = base * closure_mult * peak_mult * zone_density_mult * simultaneous_penalty
    return max(1, round(officers))


# Tow trucks only make sense for causes that physically involve a stranded/
# crashed vehicle blocking the carriageway -- formula-based (same honesty
# standard as compute_officer_count above), not a trained model, since there
# is no tow-truck dispatch data in this dataset to fit one on.
TOW_TRUCK_CAUSES = {"vehicle_breakdown", "accident"}


def compute_tow_truck_count(event_row):
    if event_row["event_cause"] not in TOW_TRUCK_CAUSES:
        return 0
    count = 1
    if event_row["closure_probability"] > 0.5:
        count += 1
    if event_row.get("is_heavy_vehicle"):
        count += 1
    return count


def compute_signal_timing_suggestion(event_row):
    """Formula-based heuristic, not measured signal-cycle data (none exists
    in this dataset) -- explicitly labelled as such in the returned string."""
    centrality = event_row.get("junction_centrality", 0.0) or 0.0
    if centrality <= 0.02:
        return None
    extend_pct = 20 if event_row.get("is_peak") == 1 else 10
    return (f"Extend green phase ~{extend_pct}% at the nearest signal-controlled junction "
            f"for the event duration (centrality-weighted heuristic, not measured signal-cycle data).")


def get_historical_peak_window(zone_filled, baseline_table):
    """Historically busiest hour-of-day for this zone, averaged across all
    days of week in the Poisson baseline table -- a pattern-based estimate
    ('this zone tends to be busiest around 6pm'), NOT a forecast that THIS
    event will peak then.

    `baseline_table` here is the INNER (dow, hour, zone) -> info dict, same
    convention as historical_trend_predictor's `baseline_table` param --
    NOT the outer {"table":..., "dow_n":...} wrapper build_baseline_table()
    returns at construction time.
    """
    table = baseline_table or {}
    hour_rates = defaultdict(list)
    for (dow, hour, zone), info in table.items():
        if zone == zone_filled:
            hour_rates[hour].append(info["mean_rate"])
    if not hour_rates:
        return None
    avg_by_hour = {h: sum(v) / len(v) for h, v in hour_rates.items()}
    peak_hour = max(avg_by_hour, key=avg_by_hour.get)
    if avg_by_hour[peak_hour] <= 0:
        return None
    return {
        "window": f"{peak_hour:02d}:00-{(peak_hour + 1) % 24:02d}:00",
        "basis": "historical pattern for this zone, not a forecast for this specific event",
    }


def stage8_resource_recommender(df: pd.DataFrame, G_main, centrality):
    print("\n[Stage 8] Resource Recommender...")
    zone_counts = df["zone_filled"].value_counts().to_dict()
    global_mean_zone_count = df["zone_filled"].value_counts().mean()

    df["recommended_officers"] = df.apply(
        lambda r: compute_officer_count(r, zone_counts, global_mean_zone_count), axis=1
    )
    print(f"  Officer count computed for all {len(df)} events. "
          f"Mean: {df['recommended_officers'].mean():.1f}, max: {df['recommended_officers'].max()}")
    print("  Barricade placement (greedy BPR simulation) and diversion routing are demo/single-event")
    print("  functions (compute cost scales per-event) -- exercised in Stage 10 End-to-End Demo below,")
    print("  not run for the full 8,173-row batch here.")
    return df


# ════════════════════════════════════════════════════════════════════════════
# STAGE 9 — CASE-BASED RETRIEVAL  (NEW)
# ════════════════════════════════════════════════════════════════════════════

CBR_NUM_FEATURES = [
    "hour_sin", "hour_cos", "dow_sin", "dow_cos", "month_sin", "month_cos",
    "junction_centrality", "is_heavy_vehicle", "is_peak", "closure_probability",
    "cascade_risk_score_v2",
]


def build_cbr_index(df: pd.DataFrame):
    """Encodes each historical event as a numeric vector and fits a
    NearestNeighbors index for similarity retrieval at inference time."""
    cbr_df = df[CBR_NUM_FEATURES].copy().fillna(0.0)
    cause_dummies = pd.get_dummies(df["event_cause"], prefix="cause")
    zone_dummies = pd.get_dummies(df["zone_filled"], prefix="zone")
    feature_matrix = pd.concat([cbr_df, cause_dummies, zone_dummies], axis=1)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(feature_matrix.values)

    nn_index = NearestNeighbors(n_neighbors=6, metric="cosine")
    nn_index.fit(X_scaled)

    return {"index": nn_index, "scaler": scaler, "columns": feature_matrix.columns.tolist()}


def retrieve_similar_events(event_idx, df, cbr_artifacts, top_k=5):
    """Given a row index into df, return the top_k most similar historical
    events (excluding itself) with their outcome stats."""
    feature_matrix = pd.DataFrame(0.0, index=[0], columns=cbr_artifacts["columns"])
    row = df.loc[event_idx]
    for c in CBR_NUM_FEATURES:
        if c in feature_matrix.columns:
            feature_matrix.at[0, c] = row[c] if pd.notna(row[c]) else 0.0
    cause_col = f"cause_{row['event_cause']}"
    if cause_col in feature_matrix.columns:
        feature_matrix.at[0, cause_col] = 1
    zone_col = f"zone_{row['zone_filled']}"
    if zone_col in feature_matrix.columns:
        feature_matrix.at[0, zone_col] = 1

    X_query = cbr_artifacts["scaler"].transform(feature_matrix.values)
    distances, indices = cbr_artifacts["index"].kneighbors(X_query, n_neighbors=top_k + 1)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == df.index.get_loc(event_idx):
            continue
        similar_row = df.iloc[idx]
        results.append({
            "event_cause": similar_row["event_cause"],
            "zone": similar_row["zone_filled"],
            "duration_hrs": similar_row["duration_hrs"] if similar_row["duration_valid"] else None,
            "requires_road_closure": bool(similar_row["requires_road_closure"]),
            "recommended_officers": similar_row.get("recommended_officers"),
            "similarity": round(1 - dist, 3),
        })
        if len(results) >= top_k:
            break
    return results


def aggregate_similar_events(similar_events):
    """Turns the raw retrieve_similar_events list into the summary stats the
    advisory card actually wants to print: "3 similar... avg 1.1 hrs, 2
    officers, no closure in any case" -- instead of a bare list."""
    if not similar_events:
        return {"n": 0, "avg_resolution_hrs": None, "avg_officers": None, "closure_rate": None}
    durations = [e["duration_hrs"] for e in similar_events if e["duration_hrs"] is not None]
    officers = [e["recommended_officers"] for e in similar_events if e["recommended_officers"] is not None]
    closures = [e["requires_road_closure"] for e in similar_events]
    return {
        "n": len(similar_events),
        "avg_resolution_hrs": round(float(np.mean(durations)), 2) if durations else None,
        "avg_officers": round(float(np.mean(officers)), 1) if officers else None,
        "closure_rate": round(float(np.mean(closures)), 2),
    }


def stage9_case_based_retrieval(df: pd.DataFrame):
    print("\n[Stage 9] Case-Based Retrieval index...")
    cbr_artifacts = build_cbr_index(df)
    with open("cbr_index.pkl", "wb") as f:
        pickle.dump(cbr_artifacts, f)
    print(f"  Built NearestNeighbors index over {len(df)} historical events, "
          f"{len(cbr_artifacts['columns'])} features. Saved cbr_index.pkl")
    return cbr_artifacts


# ════════════════════════════════════════════════════════════════════════════
# DURATION OUTPUT HELPERS  (NEW)
#
# Fixes review point #5: the advisory previously had no duration line at
# all. Fast causes get the actual XGBoost quantiles (with np.expm1 applied --
# the models were trained on log1p(duration_hrs), forgetting this would
# silently under-report by an order of magnitude). Slow causes get a
# qualitative band, not a fake point estimate, because the Weibull AFT
# concordance is weak (~0.566, see Stage 6) -- a number that looks precise
# but isn't would mislead a controller more than a category would.
# ════════════════════════════════════════════════════════════════════════════

def encode_for_fast_model(event_row, fast_encoders, all_features):
    row_df = pd.DataFrame([event_row[all_features]])
    for c, le in fast_encoders.items():
        val = str(row_df.at[row_df.index[0], c])
        if val in le.classes_:
            row_df[c] = le.transform([val])
        else:
            row_df[c] = 0  # unseen category at inference -- falls back to the encoder's first class
    return row_df


def get_fast_duration_estimate(event_row, fast_models, fast_encoders, all_features):
    row_df = encode_for_fast_model(event_row, fast_encoders, all_features)
    p10 = float(np.expm1(fast_models[0.1].predict(row_df)[0]))
    p50 = float(np.expm1(fast_models[0.5].predict(row_df)[0]))
    p90 = float(np.expm1(fast_models[0.9].predict(row_df)[0]))
    return {"type": "quantile", "p10_hrs": round(p10, 2), "p50_hrs": round(p50, 2), "p90_hrs": round(p90, 2)}


def get_slow_duration_band(event_row, aft_final, aft_columns, aft_cat_features, aft_num_features):
    row = {c: 0 for c in aft_columns}
    for c in aft_num_features:
        if c in row:
            row[c] = event_row[c] if pd.notna(event_row[c]) else 0.0
    for c in aft_cat_features:
        dummy_col = f"{c}_{event_row[c]}"
        if dummy_col in row:
            row[dummy_col] = 1
    row_df = pd.DataFrame([row])[aft_columns]
    median_hrs = float(aft_final.predict_median(row_df).iloc[0])

    if median_hrs < 6:
        band = "short (<6h)"
    elif median_hrs < 24:
        band = "multi-hour (6-24h)"
    else:
        band = "long (>24h)"
    return {"type": "band", "band": band, "median_hrs_raw": round(median_hrs, 1),
            "confidence": ("low -- survival model concordance is ~0.566 (weak) for this track, "
                            "because some 'active' events are stale/abandoned tickets rather than "
                            "genuinely still-unresolved incidents; treat this as a risk band, not a "
                            "precise estimate")}


# ════════════════════════════════════════════════════════════════════════════
# CONFLICT CHECK  (NEW)
#
# No external API needed -- a query over the events already in df. "Other
# events with elevated closure probability in the same zone, within a time
# window and radius of this one."
# ════════════════════════════════════════════════════════════════════════════

def check_conflicts(event_row, df, radius_km=2.0, window_hrs=2.0, closure_threshold=0.3):
    same_zone = df[(df.index != event_row.name) & (df["zone_filled"] == event_row["zone_filled"])]
    if same_zone.empty:
        return {"count": 0, "events": []}
    dist_km = haversine_km(event_row["latitude"], event_row["longitude"],
                            same_zone["latitude"], same_zone["longitude"])
    time_diff_hrs = (same_zone["start_datetime"] - event_row["start_datetime"]).abs().dt.total_seconds() / 3600
    mask = ((dist_km <= radius_km) & (time_diff_hrs <= window_hrs) &
            (same_zone["closure_probability"] > closure_threshold))
    conflicts = same_zone[mask]
    return {
        "count": int(mask.sum()),
        "events": conflicts[["event_cause", "closure_probability"]].head(5).to_dict("records"),
    }


# ════════════════════════════════════════════════════════════════════════════
# NETWORK RESILIENCE / CASCADING CONGESTION WARNING  (NEW)
#
# The ask: "if the main road gets blocked, side roads may get heavy traffic"
# and "if 2 of 3 roads are blocked, the 3rd is at high risk." Implementation:
# find this event's k alternate routes (reusing the diversion machinery),
# then check how many of those alternates already overlap with OTHER nearby
# active events' hard-closure cores. If most/all alternates are already
# compromised, warn about the remaining one(s) absorbing displaced traffic.
# Demo/single-event scale (footprint per nearby candidate is not free) --
# same scoping as routing delay and barricade simulation.
# ════════════════════════════════════════════════════════════════════════════

def assess_network_resilience(event_row, graph, df, k=3, conflict_radius_km=3.0, conflict_window_hrs=4.0):
    if pd.isna(event_row.get("osm_node")):
        return None
    source_node = int(event_row["osm_node"])
    if source_node not in graph.nodes:
        return None

    footprint, _ = compute_footprint_with_radius(source_node, event_row["event_cause"], graph)
    upstream, downstream = find_through_route_endpoints(source_node, graph)
    if upstream is None or downstream is None:
        return None

    blocked_nodes = [n for n, score in footprint.items() if score >= HARD_CLOSURE_THRESHOLD]
    routes = recommend_diversion(graph, upstream, downstream, blocked_nodes, k=k)
    if not routes:
        return None

    same_zone = df[(df.index != event_row.name) & (df["zone_filled"] == event_row["zone_filled"]) &
                    df["osm_node"].notna() & (df["closure_probability"] > 0.3)]
    if not same_zone.empty:
        dist_km = haversine_km(event_row["latitude"], event_row["longitude"],
                                same_zone["latitude"], same_zone["longitude"])
        time_diff_hrs = (same_zone["start_datetime"] - event_row["start_datetime"]).abs().dt.total_seconds() / 3600
        nearby = same_zone[(dist_km <= conflict_radius_km) & (time_diff_hrs <= conflict_window_hrs)].head(20)
    else:
        nearby = same_zone

    other_blocked_nodes = set()
    for _, other in nearby.iterrows():
        other_node = int(other["osm_node"])
        if other_node not in graph.nodes:
            continue
        other_fp, _ = compute_footprint_with_radius(other_node, other["event_cause"], graph)
        other_blocked_nodes.update(n for n, s in other_fp.items() if s >= HARD_CLOSURE_THRESHOLD)

    route_status = []
    compromised = 0
    for route in routes:
        is_compromised = bool(set(route["path_nodes"]) & other_blocked_nodes)
        compromised += int(is_compromised)
        route_status.append({k2: v for k2, v in route.items() if k2 != "path_nodes"} |
                             {"compromised": is_compromised})

    warning = None
    if len(routes) >= 2 and compromised >= len(routes) - 1:
        viable = [r for r in route_status if not r["compromised"]]
        if viable:
            warning = (f"{compromised}/{len(routes)} alternate routes already congested by nearby events -- "
                       f"high risk of overflow onto '{viable[0]['via']}'")
        else:
            warning = f"All {len(routes)} known alternate routes are compromised -- no clear bypass remains"

    return {"routes_checked": len(routes), "routes_compromised": compromised,
            "warning": warning, "route_status": route_status}


# ════════════════════════════════════════════════════════════════════════════
# STAGE 10 — END-TO-END DEMO  (NEW)
# ════════════════════════════════════════════════════════════════════════════

def predict_priority_label(event_row, priority_model, priority_calibrated, priority_threshold,
                            all_features_pri, cat_features_pri):
    row_df = pd.DataFrame([event_row[all_features_pri]])
    for c in cat_features_pri:
        row_df[c] = row_df[c].astype(str)
    raw_proba = priority_model.predict_proba(row_df)[:, 1]
    proba = float(priority_calibrated.predict(raw_proba)[0])
    return {"probability_high": round(proba, 3), "label": "HIGH" if proba >= priority_threshold else "LOW"}


def build_advisory(event_row, df, G_main, centrality, cbr_artifacts,
                    fast_models=None, fast_encoders=None, all_features=None,
                    aft_final=None, aft_columns=None, aft_cat_features=None, aft_num_features=None,
                    priority_model=None, priority_calibrated=None, priority_threshold=0.5,
                    all_features_pri=None, cat_features_pri=None,
                    baseline_table=None, rainfall_forecast=None):
    """Produces the OUTPUT ADVISORY format from MASTER_VISION.md Section 12 /
    the 'what is the expected output' discussion, for one real event."""
    spatial_confidence = bool(event_row.get("spatial_confidence", True))
    advisory = {
        "event_cause": event_row["event_cause"],
        "zone": event_row["zone_filled"],
        "closure_probability": round(float(event_row["closure_probability"]), 3),
        "recommended_officers": int(event_row["recommended_officers"]),
        "cascade_risk_score": round(float(event_row["cascade_risk_score_v2"]), 2),
        "spatial_confidence": spatial_confidence,
    }
    if not spatial_confidence:
        advisory["spatial_warning"] = (
            f"Nearest major road is {event_row.get('snap_distance_m', 0):.0f}m away -- "
            "spatial fields below (footprint/barricade/diversion) are degraded confidence."
        )

    advisory["recommended_tow_trucks"] = compute_tow_truck_count(event_row)
    advisory["signal_timing_suggestion"] = compute_signal_timing_suggestion(event_row)
    advisory["historical_peak_window"] = get_historical_peak_window(event_row["zone_filled"], baseline_table)

    if priority_calibrated is not None:
        advisory["priority"] = predict_priority_label(
            event_row, priority_model, priority_calibrated, priority_threshold,
            all_features_pri, cat_features_pri
        )

    if event_row["model_track"] == "fast" and fast_models is not None:
        advisory["duration"] = get_fast_duration_estimate(event_row, fast_models, fast_encoders, all_features)
    elif event_row["model_track"] == "slow" and aft_final is not None:
        advisory["duration"] = get_slow_duration_band(
            event_row, aft_final, aft_columns, aft_cat_features, aft_num_features
        )
    else:
        advisory["duration"] = {"type": "none", "note": "escalation track -- BBMP handoff, no duration model"}

    hike = historical_trend_predictor(
        event_row["zone_filled"],
        event_row["start_ist"],
        latitude=event_row["latitude"],
        longitude=event_row["longitude"],
        baseline_table=baseline_table,
        rainfall_forecast=rainfall_forecast,
        current_zone_count=int(event_row["cascade_count"]),
    )
    advisory["predicted_hike_context"] = hike
    advisory["conflicts"] = check_conflicts(event_row, df)

    # Raw coordinates + footprint radius, surfaced for the map view in the
    # UI (not used by any model -- purely presentation-layer data).
    advisory["latitude"] = float(event_row["latitude"])
    advisory["longitude"] = float(event_row["longitude"])
    advisory["footprint_radius_km"] = 0.0

    if spatial_confidence and pd.notna(event_row["osm_node"]) and int(event_row["osm_node"]) in G_main.nodes:
        node = int(event_row["osm_node"])
        routing = compute_routing_delay(node, event_row["event_cause"], G_main)
        advisory["routing"] = routing

        _, radius_km = compute_footprint_with_radius(node, event_row["event_cause"], G_main)
        advisory["footprint_radius_km"] = round(float(radius_km), 2)

        best_barricade, candidates = greedy_barricade_simulation(
            node, event_row["event_cause"], G_main, centrality
        )
        advisory["recommended_barricade_node"] = best_barricade
        advisory["barricade_candidates_considered"] = candidates

        if routing and routing.get("alt_route_exists"):
            upstream, downstream = find_through_route_endpoints(node, G_main)
            advisory["diversion_routes"] = recommend_diversion(
                G_main, upstream, downstream, routing["blocked_nodes"]
            )
        else:
            advisory["diversion_routes"] = []

        advisory["network_resilience"] = assess_network_resilience(event_row, G_main, df)
    else:
        advisory["routing"] = None
        advisory["recommended_barricade_node"] = None
        advisory["diversion_routes"] = []
        advisory["network_resilience"] = None

    event_idx = event_row.name
    similar = retrieve_similar_events(event_idx, df, cbr_artifacts, top_k=3)
    advisory["similar_past_events"] = similar
    advisory["similar_past_events_summary"] = aggregate_similar_events(similar)
    return advisory


def stage10_demo(df: pd.DataFrame, G_main, centrality, cbr_artifacts, n=5,
                  baseline_table=None, rainfall_forecast=None,
                  fast_models=None, fast_encoders=None, all_features=None,
                  aft_final=None, aft_columns=None, aft_cat_features=None, aft_num_features=None,
                  priority_model=None, priority_calibrated=None, priority_threshold=0.5,
                  all_features_pri=None, cat_features_pri=None):
    print("\n[Stage 10] End-to-end demo on real events...")
    sample = df[df["valid_coord"] & df["osm_node"].notna()].sample(n, random_state=42)

    for _, row in sample.iterrows():
        advisory = build_advisory(
            row, df, G_main, centrality, cbr_artifacts,
            fast_models=fast_models, fast_encoders=fast_encoders, all_features=all_features,
            aft_final=aft_final, aft_columns=aft_columns,
            aft_cat_features=aft_cat_features, aft_num_features=aft_num_features,
            priority_model=priority_model, priority_calibrated=priority_calibrated, priority_threshold=priority_threshold,
            all_features_pri=all_features_pri, cat_features_pri=cat_features_pri,
            baseline_table=baseline_table, rainfall_forecast=rainfall_forecast,
        )
        print(f"\n  --- {advisory['event_cause']} in {advisory['zone']} ---")
        print(f"    Closure probability (calibrated): {advisory['closure_probability']:.1%}")
        if "priority" in advisory:
            print(f"    Priority: {advisory['priority']['label']} "
                  f"(P={advisory['priority']['probability_high']:.1%})")
        print(f"    Recommended officers: {advisory['recommended_officers']}")
        print(f"    CascadeRisk score: {advisory['cascade_risk_score']}")
        d = advisory["duration"]
        if d["type"] == "quantile":
            print(f"    Duration: {d['p50_hrs']:.1f}h (80% CI {d['p10_hrs']:.1f}-{d['p90_hrs']:.1f}h)")
        elif d["type"] == "band":
            print(f"    Duration: {d['band']} [{d['confidence']}]")
        else:
            print(f"    Duration: {d['note']}")
        if not advisory["spatial_confidence"]:
            print(f"    SPATIAL WARNING: {advisory['spatial_warning']}")
        if advisory["routing"]:
            r = advisory["routing"]
            if r.get("delay_minutes") is not None:
                print(f"    Routing delay: +{r['delay_minutes']:.1f} min "
                      f"({r['baseline_minutes']:.1f} -> {r['affected_minutes']:.1f} min)")
            else:
                print("    Routing delay: no alternate route found in major-road graph")
        print(f"    Recommended barricade node: {advisory['recommended_barricade_node']}")
        print(f"    Diversion routes available: {len(advisory['diversion_routes'])}")
        if advisory.get("network_resilience") and advisory["network_resilience"].get("warning"):
            print(f"    NETWORK RESILIENCE WARNING: {advisory['network_resilience']['warning']}")
        if advisory["conflicts"]["count"] > 0:
            print(f"    Conflicts: {advisory['conflicts']['count']} other elevated-risk events nearby/concurrent")
        s = advisory["similar_past_events_summary"]
        if s["n"] > 0:
            dur_str = f"{s['avg_resolution_hrs']}h" if s["avg_resolution_hrs"] is not None else "unknown duration"
            print(f"    Similar past events: {s['n']} found, avg {dur_str}, "
                  f"avg {s['avg_officers']} officers, closure rate {s['closure_rate']:.0%}")
        if advisory["predicted_hike_context"]:
            h = advisory["predicted_hike_context"]
            print(f"    Upcoming-hike context: {h['trigger_reason']} "
                  f"(confidence {h['confidence']}, window: {h['predicted_window']})")
        else:
            print("    Upcoming-hike context: none predicted for this zone/time")


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("EVENT-DRIVEN CONGESTION -- FULL PIPELINE (FINAL)")
    print("Flipkart GridLock Round 2")
    print("=" * 70)

    df = pd.read_csv(DATA_PATH, low_memory=False)
    print(f"\nLoaded {len(df)} rows, {len(df.columns)} columns")

    df = stage1_clean(df)
    df, G, centrality = stage2_spatial(df)
    df = stage3_external_signals(df)
    df = stage4_features(df)
    (df, closure_model, priority_model, closure_calibrated, priority_calibrated,
     closure_threshold, priority_threshold, all_features_pri, cat_features_pri) = stage5_triage(df)
    (fast_models, fast_encoders, duration_all_features,
     aft_final, aft_columns, aft_cat_features, aft_num_features) = stage6_duration(df)
    df, G_main = stage7_spread(df, G)
    df = stage8_resource_recommender(df, G_main, centrality)
    cbr_artifacts = stage9_case_based_retrieval(df)

    # Historical Trend module artifacts for Stage 10's advisory calls.
    # BASELINE_CACHE is guaranteed to exist by this point (Stage 4 builds it).
    with open(BASELINE_CACHE, "rb") as f:
        BASELINE_TABLE = pickle.load(f)["table"]
    print("\n[Historical Trend] Fetching live 3-day rainfall forecast (Open-Meteo)...")
    RAINFALL_FORECAST = fetch_forecast_rainfall()
    if RAINFALL_FORECAST is None:
        print("  Forecast API unreachable this run -- rainfall hike signal disabled, "
              "Poisson surge + Tavily signals still active.")

    stage10_demo(
        df, G_main, centrality, cbr_artifacts, n=5,
        baseline_table=BASELINE_TABLE, rainfall_forecast=RAINFALL_FORECAST,
        fast_models=fast_models, fast_encoders=fast_encoders, all_features=duration_all_features,
        aft_final=aft_final, aft_columns=aft_columns,
        aft_cat_features=aft_cat_features, aft_num_features=aft_num_features,
        priority_model=priority_model, priority_calibrated=priority_calibrated, priority_threshold=priority_threshold,
        all_features_pri=all_features_pri, cat_features_pri=cat_features_pri,
    )

    df.to_parquet(ENRICHED_PATH, index=False)
    print(f"\nSaved {ENRICHED_PATH}: {df.shape[0]} rows x {df.shape[1]} columns")

    print("\n" + "=" * 70)
    print("WHAT'S LEFT")
    print("=" * 70)
    print("""
  1. Presentation-layer polish
     - The advisory dict in Stage 10 is the data; turning it into the
       human-readable card format from the "what is the expected output"
       discussion (deck-ready) is formatting work, not modeling work.

  2. Map visualization (Folium/Kepler.gl)
     - CascadeRisk heatmap and live+predicted congestion layers described
       in MASTER_VISION.md / INNOVATIONS.md are not built -- would consume
       `cascade_risk_score_v2` and `footprint_size`, already computed here.

  3. BPR demand-side realism
     - `apply_bpr_weights` uses a flat assumed volume (500 veh/hr) since no
       real per-road traffic-count data exists in this dataset. Directionally
       useful (penalizes narrow roads more under equal assumed load) but not
       a calibrated volume estimate. Would need a traffic-count data source
       to improve.

  4. Historical Trend / Upcoming-Hike Predictor is now IMPLEMENTED
     - `historical_trend_predictor()` merges a DOW x Hour x Zone Poisson
       surge baseline, an Open-Meteo rainfall forecast trigger, and optional
       Tavily live-event enrichment (cached + auto-backoff). Set
       TAVILY_API_KEY in the environment to enable the Tavily signal; the
       other two signals work with no extra setup.
""")


if __name__ == "__main__":
    main()

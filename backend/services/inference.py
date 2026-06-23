"""
inference.py — Inference layer for the GridLock FastAPI backend.

Adapted from docs/Flipkart-GridLock/inference.py.
Key changes vs. original:
  1. All file paths sourced from backend.core.config (absolute pathlib.Path).
  2. `import new_pipeline as np_pipe` → `from backend.services import pipeline as np_pipe`
  3. No Flask imports anywhere.
  4. _CTX_SINGLETON pattern preserved — load_artifacts() is called once in
     FastAPI lifespan; subsequent calls return cached context immediately.

No logic changes. All function signatures are identical to the original.
"""

import json
import pickle
import uuid
from pathlib import Path

import numpy as np
import pandas as pd

from backend.services import pipeline as np_pipe
from backend.services.pipeline import (
    TRIAGE_CAT_FEATURES, TRIAGE_NUM_FEATURES, DURATION_NUM_FEATURES_EXTRA,
    CBR_NUM_FEATURES, CLOSURE_KEYWORDS, SLOW_KEYWORDS, HOLIDAYS,
    ELECTION_CAMPAIGN_START, ELECTION_CAMPAIGN_END, RCB_HOME_MATCHES_2024,
    CHINNASWAMY_LAT, CHINNASWAMY_LON, SCHOOL_HOURS, OFFICE_PEAK_HOURS,
    IT_CORRIDOR_ZONES, ROAD_CLASS_RANK, BASE_OFFICERS, DEFAULT_BASE_OFFICERS,
    FAST_CAUSES, SLOW_CAUSES, ESCALATION_CAUSES, HEAVY_VEH, PUBLIC_TRANSPORT,
    SPATIAL_CONFIDENCE_THRESHOLD_M,
    haversine_km, has_kannada, has_keyword,
    compute_officer_count, check_conflicts, assess_network_resilience,
    predict_priority_label, historical_trend_predictor,
    aggregate_similar_events,
    compute_routing_delay, greedy_barricade_simulation,
    find_through_route_endpoints, recommend_diversion,
    get_fast_duration_estimate, get_slow_duration_band,
    compute_tow_truck_count, compute_signal_timing_suggestion, get_historical_peak_window,
    LabelEncoder,
)

from backend.core.config import (
    GRAPH_PATH, CENTRALITY_CACHE, ENRICHED_PATH, RAINFALL_CACHE,
    CBR_INDEX_PATH, BASELINE_CACHE, TARGET_ENCODING_PATH,
    CASCADE_SCALER_PATH, PRIORITY_THRESHOLD_PATH,
    CLOSURE_CALIBRATED_PATH, PRIORITY_CALIBRATED_PATH,
    CLOSURE_MODEL_PATH, PRIORITY_MODEL_PATH,
    DURATION_FAST_Q_PATHS, DURATION_SLOW_WEIBULL_PATH,
    PENDING_EVENTS_PATH, MODELS_DIR, USE_SUPABASE, IS_PRODUCTION,
)

import logging
logger = logging.getLogger("gridlock")


# Exact same num-feature list as in new_pipeline.stage6_duration -- copied
# here because stage6_duration only returns it as a local variable, never
# persisted by itself (it IS returned by stage6_duration, but we don't run
# stage6_duration here -- we only reconstruct fast_encoders deterministically).
AFT_NUM_FEATURES = [
    "hour_ist", "month", "is_weekend", "is_peak", "junction_centrality",
    "rainfall_mm", "is_election_campaign_period", "is_public_holiday",
    "has_kannada", "desc_slow_signal", "cascade_count", "hotspot_score",
    "is_heavy_vehicle", "closure_probability",
]
AFT_CAT_FEATURES = ["event_cause", "holiday_type"]


# ════════════════════════════════════════════════════════════════════════════
# Context object + singleton loader
# ════════════════════════════════════════════════════════════════════════════

class InferenceContext:
    """Plain attribute bag -- not a dataclass on purpose, populated
    incrementally inside load_artifacts()."""
    pass


_CTX_SINGLETON = None


def load_artifacts() -> InferenceContext:
    """Loads every persisted artifact once and caches the result at module
    level. Safe to call on every request -- subsequent calls just return
    the cached context. Called once from FastAPI lifespan at startup."""
    global _CTX_SINGLETON
    if _CTX_SINGLETON is not None:
        return _CTX_SINGLETON

    import networkx as nx
    import osmnx as ox
    from catboost import CatBoostClassifier
    import xgboost as xgb

    ctx = InferenceContext()

    # ── historical dataframe ──────────────────────────────────────────────
    ctx.df_hist = pd.read_parquet(ENRICHED_PATH)

    # ── road graph + main strongly-connected component ────────────────────
    ctx.G = ox.load_graphml(GRAPH_PATH)
    largest_scc = max(nx.strongly_connected_components(ctx.G), key=len)
    ctx.G_main = ctx.G.subgraph(largest_scc).copy()

    # ── centrality ──────────────────────────────────────────────────────────
    centrality_df = pd.read_parquet(CENTRALITY_CACHE)
    ctx.centrality = dict(zip(centrality_df["node"].astype(int), centrality_df["centrality"]))

    # ── node -> road type / name (replicates stage2_spatial's edge scan) ───
    edges_gdf = ox.graph_to_gdfs(ctx.G, nodes=False, edges=True)
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
    ctx.node_to_road = node_to_road
    ctx.node_to_name = node_to_name

    # ── CBR index ────────────────────────────────────────────────────────────
    with open(CBR_INDEX_PATH, "rb") as f:
        ctx.cbr_artifacts = pickle.load(f)

    # ── baseline (DOW x hour x zone) table ──────────────────────────────────
    with open(BASELINE_CACHE, "rb") as f:
        ctx.baseline_table = pickle.load(f)

    # ── target-encoding maps ────────────────────────────────────────────────
    with open(TARGET_ENCODING_PATH) as f:
        ctx.target_encoding_maps = json.load(f)

    # ── cascade-risk scaler bounds ───────────────────────────────────────────
    with open(CASCADE_SCALER_PATH) as f:
        ctx.cascade_risk_scaler = json.load(f)

    # ── triage models (closure) ─────────────────────────────────────────────
    ctx.closure_model = CatBoostClassifier()
    ctx.closure_model.load_model(str(CLOSURE_MODEL_PATH))
    with open(CLOSURE_CALIBRATED_PATH, "rb") as f:
        ctx.closure_calibrated = pickle.load(f)["calibrator"]

    # ── triage models (priority) ────────────────────────────────────────────
    ctx.priority_model = CatBoostClassifier()
    ctx.priority_model.load_model(str(PRIORITY_MODEL_PATH))
    with open(PRIORITY_CALIBRATED_PATH, "rb") as f:
        ctx.priority_calibrated = pickle.load(f)["calibrator"]
    with open(PRIORITY_THRESHOLD_PATH) as f:
        ctx.priority_threshold = json.load(f)["priority_threshold"]

    cat_features_pri = [c for c in TRIAGE_CAT_FEATURES if c != "corridor"]
    ctx.cat_features_pri = cat_features_pri
    ctx.all_features_pri = cat_features_pri + TRIAGE_NUM_FEATURES

    # ── duration models: fast track (XGBoost quantiles) ─────────────────────
    ctx.fast_models = {}
    for q, path in DURATION_FAST_Q_PATHS.items():
        model = xgb.XGBRegressor()
        model.load_model(str(path))
        ctx.fast_models[q] = model

    ctx.duration_all_features = TRIAGE_CAT_FEATURES + TRIAGE_NUM_FEATURES + DURATION_NUM_FEATURES_EXTRA

    # GAP FILL: fast_encoders are never persisted by stage6_duration. They
    # are deterministic given the same input values (sklearn LabelEncoder
    # fits a sorted set of unique strings), so we reconstruct them by
    # re-running the exact same filter + fit stage6_duration used.
    fast_df = ctx.df_hist[(ctx.df_hist["model_track"] == "fast") & (ctx.df_hist["duration_valid"])]
    fast_encoders = {}
    for c in TRIAGE_CAT_FEATURES:
        le = LabelEncoder()
        le.fit(fast_df[c].astype(str).fillna("MISSING"))
        fast_encoders[c] = le
    ctx.fast_encoders = fast_encoders

    # ── duration models: slow track (Weibull AFT) ───────────────────────────
    with open(DURATION_SLOW_WEIBULL_PATH, "rb") as f:
        slow_artifacts = pickle.load(f)
    ctx.aft_final = slow_artifacts["model"]
    ctx.aft_columns = slow_artifacts["columns"]
    ctx.aft_cat_features = AFT_CAT_FEATURES
    ctx.aft_num_features = AFT_NUM_FEATURES

    # ── resource recommender helpers ────────────────────────────────────────
    ctx.zone_counts = ctx.df_hist["zone_filled"].value_counts().to_dict()
    ctx.global_mean_zone_count = ctx.df_hist["zone_filled"].value_counts().mean()

    # ── known categorical universes ─────────────────────────────────────────
    ctx.known_zones = sorted(ctx.df_hist["zone_filled"].dropna().unique().tolist())
    ctx.known_causes = sorted(ctx.df_hist["event_cause"].dropna().unique().tolist())

    # ── hotspot grid (replicates stage2_spatial's grid-count logic) ────────
    tmp = ctx.df_hist.copy()
    tmp["lat_grid"] = (tmp["latitude"] / 0.001).round() * 0.001
    tmp["lon_grid"] = (tmp["longitude"] / 0.001).round() * 0.001
    grid_counts = tmp.groupby(["lat_grid", "lon_grid"]).size().rename("hotspot_count").reset_index()
    n = len(ctx.df_hist)
    ctx.hotspot_grid = {
        (round(float(r.lat_grid), 3), round(float(r.lon_grid), 3)): r.hotspot_count / n
        for r in grid_counts.itertuples(index=False)
    }

    _CTX_SINGLETON = ctx
    return ctx


# ════════════════════════════════════════════════════════════════════════════
# featurize_new_event
# ════════════════════════════════════════════════════════════════════════════

def _in_any_range(hour, ranges):
    return any(start <= hour < end for start, end in ranges)


def featurize_new_event(raw: dict, ctx: InferenceContext) -> pd.Series:
    event_cause = str(raw["event_cause"]).strip().lower()
    if event_cause not in ctx.known_causes:
        raise ValueError(f"Unknown event_cause '{event_cause}'. Must be one of: {ctx.known_causes}")

    zone_filled = str(raw["zone_filled"])
    if zone_filled not in ctx.known_zones:
        raise ValueError(f"Unknown zone_filled '{zone_filled}'. Must be one of: {ctx.known_zones}")

    latitude = float(raw["latitude"])
    longitude = float(raw["longitude"])

    description = raw.get("description") or ""
    veh_type = str(raw.get("veh_type") or "MISSING")
    corridor = str(raw.get("corridor") or "MISSING")
    gba_identifier = str(raw.get("gba_identifier") or "MISSING")
    endlatitude = raw.get("endlatitude")
    endlongitude = raw.get("endlongitude")

    # ── start_datetime parsing / IST localization (mirrors stage1_clean) ───
    start_raw = pd.to_datetime(raw["start_datetime"])
    if start_raw.tzinfo is None:
        start_ist = start_raw.tz_localize("Asia/Kolkata")
    else:
        start_ist = start_raw.tz_convert("Asia/Kolkata")
    start_datetime_utc = start_ist.tz_convert("UTC")

    row = {}
    row["event_cause"] = event_cause
    row["zone_filled"] = zone_filled
    row["latitude"] = latitude
    row["longitude"] = longitude
    row["description"] = description
    row["veh_type"] = veh_type
    row["corridor"] = corridor
    row["gba_identifier"] = gba_identifier
    row["endlatitude"] = endlatitude
    row["endlongitude"] = endlongitude
    row["start_ist"] = start_ist
    row["start_datetime"] = start_datetime_utc

    # ── model_track (mirrors stage1_clean.assign_track) ────────────────────
    if event_cause in FAST_CAUSES:
        row["model_track"] = "fast"
    elif event_cause in ESCALATION_CAUSES:
        row["model_track"] = "escalation"
    else:
        row["model_track"] = "slow"

    # ── segment_length_km / is_stretch (mirrors stage1_clean ~299-310) ─────
    has_end_coord = (
        endlatitude is not None and endlongitude is not None
        and not pd.isna(endlatitude) and not pd.isna(endlongitude)
        and float(endlatitude) != 0 and float(endlongitude) != 0
    )
    if has_end_coord:
        seg_km = float(haversine_km(latitude, longitude, float(endlatitude), float(endlongitude)))
        is_stretch = int(0.1 <= seg_km < 5)
        seg_km = min(max(seg_km, 0.0), 5.0)
        if not is_stretch:
            seg_km = 0.0
    else:
        seg_km, is_stretch = 0.0, 0
    row["segment_length_km"] = seg_km
    row["is_stretch"] = is_stretch

    # ── vehicle flags ────────────────────────────────────────────────────────
    row["is_heavy_vehicle"] = int(veh_type in HEAVY_VEH)
    row["is_public_transport"] = int(veh_type in PUBLIC_TRANSPORT)

    # ── valid_coord ──────────────────────────────────────────────────────────
    row["valid_coord"] = bool(12.0 < latitude < 14.0 and 76.5 < longitude < 78.5)

    # ── spatial snap (mirrors stage2_spatial) ───────────────────────────────
    import osmnx as ox
    nearest, dist = ox.distance.nearest_nodes(ctx.G, [longitude], [latitude], return_dist=True)
    osm_node = int(nearest[0])
    snap_distance_m = float(dist[0])
    row["osm_node"] = osm_node
    row["snap_distance_m"] = snap_distance_m
    row["junction_centrality"] = ctx.centrality.get(osm_node, 0.0)
    row["osm_road_type"] = ctx.node_to_road.get(osm_node, "unclassified")
    row["osm_road_name"] = ctx.node_to_name.get(osm_node, None)
    row["spatial_confidence"] = snap_distance_m < SPATIAL_CONFIDENCE_THRESHOLD_M

    # ── hotspot score ────────────────────────────────────────────────────────
    lat_grid = round(round(latitude / 0.001) * 0.001, 3)
    lon_grid = round(round(longitude / 0.001) * 0.001, 3)
    row["hotspot_score"] = ctx.hotspot_grid.get((lat_grid, lon_grid), 0.0)

    # ── external signals (stage3) ────────────────────────────────────────────
    event_date = start_ist.date()
    row["event_date"] = event_date
    rainfall_mm, rainfall_mm_3day = 0.0, 0.0
    try:
        rainfall_df = pd.read_parquet(RAINFALL_CACHE)
        match = rainfall_df[rainfall_df["date"] == event_date]
        if len(match):
            rainfall_mm = float(match["rainfall_mm"].iloc[0])
        # 3-day rolling sum, same definition as stage3
        rsorted = rainfall_df.sort_values("date").set_index("date")
        if event_date in rsorted.index:
            roll = rsorted["rainfall_mm"].rolling(3, min_periods=1).sum()
            rainfall_mm_3day = float(roll.loc[event_date])
    except Exception:
        pass
    row["rainfall_mm"] = rainfall_mm
    row["rainfall_mm_3day"] = rainfall_mm_3day

    # ── holidays ─────────────────────────────────────────────────────────────
    date_str = event_date.isoformat()
    holiday_info = HOLIDAYS.get(date_str)
    row["holiday_type"] = holiday_info[1] if holiday_info else "none"
    row["is_public_holiday"] = int(holiday_info is not None)

    # ── IPL / Chinnaswamy ────────────────────────────────────────────────────
    is_ipl = int(date_str in RCB_HOME_MATCHES_2024)
    row["is_ipl_match_day"] = is_ipl
    dist_chinn = float(haversine_km(latitude, longitude, CHINNASWAMY_LAT, CHINNASWAMY_LON))
    row["distance_to_chinnaswamy_km"] = dist_chinn
    row["near_chinnaswamy_on_match_day"] = int(is_ipl == 1 and dist_chinn < 5)

    # ── election campaign period ─────────────────────────────────────────────
    row["is_election_campaign_period"] = int(ELECTION_CAMPAIGN_START <= event_date <= ELECTION_CAMPAIGN_END)

    # ── stage4 time features ─────────────────────────────────────────────────
    hour_ist = start_ist.hour
    dow = start_ist.dayofweek
    month = start_ist.month
    row["hour_ist"] = hour_ist
    row["dow"] = dow
    row["dow_name"] = start_ist.day_name()
    row["month"] = month
    is_weekend = int(dow >= 5)
    row["is_weekend"] = is_weekend
    row["is_peak"] = int((8 <= hour_ist < 11) or (17 <= hour_ist < 20))
    row["is_school_hour"] = int(_in_any_range(hour_ist, SCHOOL_HOURS) and is_weekend == 0)
    row["is_office_peak_hour"] = int(_in_any_range(hour_ist, OFFICE_PEAK_HOURS) and is_weekend == 0)
    row["is_it_corridor_zone"] = int(zone_filled in IT_CORRIDOR_ZONES)
    row["hour_sin"] = float(np.sin(2 * np.pi * hour_ist / 24))
    row["hour_cos"] = float(np.cos(2 * np.pi * hour_ist / 24))
    row["dow_sin"] = float(np.sin(2 * np.pi * dow / 7))
    row["dow_cos"] = float(np.cos(2 * np.pi * dow / 7))
    row["month_sin"] = float(np.sin(2 * np.pi * month / 12))
    row["month_cos"] = float(np.cos(2 * np.pi * month / 12))

    # ── description signals ─────────────────────────────────────────────────
    row["has_description"] = int(bool(description))
    row["has_kannada"] = int(has_kannada(description))
    row["desc_word_count"] = len(str(description).split())
    row["desc_closure_signal"] = has_keyword(description, CLOSURE_KEYWORDS)
    row["desc_slow_signal"] = has_keyword(description, SLOW_KEYWORDS)

    # ── cascade_count: approximated via historical day-of-week / time-of-day
    # co-occurrence rate (NOT live data).
    hist = ctx.df_hist
    valid_hist = hist[hist["valid_coord"] & hist["start_ist"].notna()]
    dist_km = haversine_km(latitude, longitude, valid_hist["latitude"], valid_hist["longitude"])
    nearby = valid_hist[dist_km <= 5.0]
    if len(nearby):
        hour_of_day = nearby["start_ist"].dt.hour + nearby["start_ist"].dt.minute / 60.0
        this_hour_of_day = hour_ist + start_ist.minute / 60.0
        delta_hrs = (hour_of_day - this_hour_of_day) % 24
        cascade_mask = (nearby["dow"] == dow) & (delta_hrs > 0) & (delta_hrs <= 2)
        total_occurrences = int(cascade_mask.sum())
    else:
        total_occurrences = 0
    n_weeks = ctx.baseline_table.get("dow_n", {}).get(int(dow), 1) or 1
    row["cascade_count"] = max(0, round(total_occurrences / n_weeks))

    # ── baseline-table lookup ─────────────────────────────────────────────
    table = ctx.baseline_table.get("table", {})
    info = table.get((int(dow), int(hour_ist), str(zone_filled)))
    if info is None:
        zone_baseline_rate = 0.0
        surge_threshold = 2.0  # POISSON_SURGE_K
    else:
        zone_baseline_rate = info["mean_rate"]
        surge_threshold = info["surge_threshold"]
    row["zone_baseline_rate"] = zone_baseline_rate
    observed = row["cascade_count"]
    if zone_baseline_rate > 0:
        ratio = min(observed / zone_baseline_rate, 10)
    else:
        ratio = 3.0 if observed > 0 else 0.0
    row["zone_surge_ratio"] = round(float(ratio), 3)
    row["is_surge_zone"] = int(observed > surge_threshold)

    # ── target-encoding lookups ──────────────────────────────────────────────
    maps = ctx.target_encoding_maps
    cause_duration_map = maps["cause_duration_map"]
    overall_mean_duration = maps["overall_mean_duration"]
    cause_closure_map = maps["cause_closure_map"]
    global_mean_closure = float(ctx.df_hist["requires_road_closure"].mean())
    row["cause_median_duration"] = cause_duration_map.get(event_cause, overall_mean_duration)
    row["cause_closure_rate"] = cause_closure_map.get(event_cause, global_mean_closure)

    return pd.Series(row, name=-1)


# ════════════════════════════════════════════════════════════════════════════
# score_new_event
# ════════════════════════════════════════════════════════════════════════════

def score_new_event(row: pd.Series, ctx: InferenceContext) -> pd.Series:
    row = row.copy()
    all_features = TRIAGE_CAT_FEATURES + TRIAGE_NUM_FEATURES
    row_dict = {}
    for c in all_features:
        v = row[c]
        if c in TRIAGE_CAT_FEATURES:
            v = "MISSING" if (v is None or (isinstance(v, float) and pd.isna(v))) else str(v)
        row_dict[c] = v
    row_df = pd.DataFrame([row_dict])[all_features]

    raw_proba = ctx.closure_model.predict_proba(row_df)[:, 1]
    closure_probability = float(ctx.closure_calibrated.predict(raw_proba)[0])
    row["closure_probability"] = closure_probability

    row["recommended_officers"] = compute_officer_count(row, ctx.zone_counts, ctx.global_mean_zone_count)

    risk = (closure_probability * (row["junction_centrality"] + 0.01) *
            (1.0 / (row["cause_median_duration"] + 1)) * np.log1p(row["cascade_count"]) *
            (2 if row["is_peak"] == 1 else 1))
    p01 = ctx.cascade_risk_scaler["risk_p01"]
    p99 = ctx.cascade_risk_scaler["risk_p99"]
    risk_clipped = min(max(risk, p01), p99)
    scaled = 10 * (risk_clipped - p01) / (p99 - p01 + 1e-9)
    row["cascade_risk_score_v2"] = float(min(max(scaled, 0.0), 10.0))

    return row


# ════════════════════════════════════════════════════════════════════════════
# CBR retrieval for a brand-new row (not a member of df_hist)
# ════════════════════════════════════════════════════════════════════════════

def retrieve_similar_events_for_new_row(row: pd.Series, ctx: InferenceContext, top_k: int = 3):
    cbr_artifacts = ctx.cbr_artifacts
    feature_matrix = pd.DataFrame(0.0, index=[0], columns=cbr_artifacts["columns"])
    for c in CBR_NUM_FEATURES:
        if c in feature_matrix.columns:
            v = row[c]
            feature_matrix.at[0, c] = v if pd.notna(v) else 0.0
    cause_col = f"cause_{row['event_cause']}"
    if cause_col in feature_matrix.columns:
        feature_matrix.at[0, cause_col] = 1
    zone_col = f"zone_{row['zone_filled']}"
    if zone_col in feature_matrix.columns:
        feature_matrix.at[0, zone_col] = 1

    X_query = cbr_artifacts["scaler"].transform(feature_matrix.values)
    distances, indices = cbr_artifacts["index"].kneighbors(X_query, n_neighbors=top_k)

    df = ctx.df_hist
    results = []
    for dist, idx in zip(distances[0], indices[0]):
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


# ════════════════════════════════════════════════════════════════════════════
# _build_advisory_new
# ════════════════════════════════════════════════════════════════════════════

def _build_advisory_new(event_row, df, G_main, centrality, cbr_artifacts,
                         fast_models=None, fast_encoders=None, all_features=None,
                         aft_final=None, aft_columns=None, aft_cat_features=None, aft_num_features=None,
                         priority_model=None, priority_calibrated=None, priority_threshold=0.5,
                         all_features_pri=None, cat_features_pri=None,
                         baseline_table=None, rainfall_forecast=None,
                         ctx=None, top_k=3):
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

    advisory["latitude"] = float(event_row["latitude"])
    advisory["longitude"] = float(event_row["longitude"])
    advisory["footprint_radius_km"] = 0.0

    if spatial_confidence and pd.notna(event_row["osm_node"]) and int(event_row["osm_node"]) in G_main.nodes:
        node = int(event_row["osm_node"])
        routing = compute_routing_delay(node, event_row["event_cause"], G_main)
        advisory["routing"] = routing

        _, radius_km = np_pipe.compute_footprint_with_radius(node, event_row["event_cause"], G_main)
        advisory["footprint_radius_km"] = round(float(radius_km), 2)

        best_barricade, candidates = greedy_barricade_simulation(
            node, event_row["event_cause"], G_main, centrality
        )
        advisory["recommended_barricade_node"] = best_barricade
        advisory["recommended_barricade_coordinates"] = (
            np_pipe.node_to_latlng(best_barricade, G_main) if best_barricade is not None else None
        )
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
        advisory["recommended_barricade_coordinates"] = None
        advisory["diversion_routes"] = []
        advisory["network_resilience"] = None

    similar = retrieve_similar_events_for_new_row(event_row, ctx, top_k=top_k)
    advisory["similar_past_events"] = similar
    advisory["similar_past_events_summary"] = aggregate_similar_events(similar)
    return advisory


# ════════════════════════════════════════════════════════════════════════════
# JSON-safety helper
# ════════════════════════════════════════════════════════════════════════════

def _to_jsonable(obj):
    if isinstance(obj, dict):
        return {str(k): _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        f = float(obj)
        return None if np.isnan(f) else f
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return _to_jsonable(obj.tolist())
    if isinstance(obj, (pd.Timestamp,)):
        if pd.isna(obj):
            return None
        return obj.isoformat()
    if isinstance(obj, float) and np.isnan(obj):
        return None
    if obj is pd.NaT:
        return None
    try:
        if pd.isna(obj):
            return None
    except (TypeError, ValueError):
        pass
    return obj


# ════════════════════════════════════════════════════════════════════════════
# Public orchestration entry points
# ════════════════════════════════════════════════════════════════════════════

def _persist_pending_event(event_id: str, row: pd.Series) -> None:
    """Persists the full feature row for a newly predicted event, keyed by
    event_id, so a later officer-submitted outcome can be joined back to
    its original features and used to retrain the triage classifier (see
    services/retrain.py). Plain CSV append -- cheap and avoids read-modify-
    write races that a parquet rewrite would have under concurrent requests."""
    # DURATION_NUM_FEATURES_EXTRA (closure_probability, cascade_risk_score_v2)
    # tag along too -- not used by the closure/priority classifiers, but
    # required to retrain the duration models from live outcomes later.
    all_features = TRIAGE_CAT_FEATURES + TRIAGE_NUM_FEATURES + DURATION_NUM_FEATURES_EXTRA
    record = {"event_id": event_id, "created_at": pd.Timestamp.utcnow().isoformat()}
    for c in all_features:
        record[c] = row[c]

    file_exists = PENDING_EVENTS_PATH.exists() and PENDING_EVENTS_PATH.stat().st_size >= 10
    if not file_exists:
        pd.DataFrame([record]).to_csv(PENDING_EVENTS_PATH, mode="w", header=True, index=False)
        return

    # Schema-safe append: a column added here later (like the two
    # DURATION_NUM_FEATURES_EXTRA columns just now) must not change the
    # field count of a row appended to a file with an older, narrower
    # header -- that silently misaligns every row read back afterwards.
    existing_columns = pd.read_csv(PENDING_EVENTS_PATH, nrows=0).columns.tolist()
    new_columns = [c for c in record.keys() if c not in existing_columns]
    if new_columns:
        full_df = pd.read_csv(PENDING_EVENTS_PATH)
        for c in new_columns:
            full_df[c] = None
        full_df.to_csv(PENDING_EVENTS_PATH, mode="w", header=True, index=False)
        existing_columns = existing_columns + new_columns

    row_df = pd.DataFrame([record]).reindex(columns=existing_columns)
    row_df.to_csv(PENDING_EVENTS_PATH, mode="a", header=False, index=False)


def build_advisory_for_new_event(raw: dict, ctx: InferenceContext) -> dict:
    row = featurize_new_event(raw, ctx)
    row = score_new_event(row, ctx)
    event_id = uuid.uuid4().hex
    _persist_pending_event(event_id, row)
    advisory = _build_advisory_new(
        row, ctx.df_hist, ctx.G_main, ctx.centrality, ctx.cbr_artifacts,
        fast_models=ctx.fast_models, fast_encoders=ctx.fast_encoders, all_features=ctx.duration_all_features,
        aft_final=ctx.aft_final, aft_columns=ctx.aft_columns,
        aft_cat_features=ctx.aft_cat_features, aft_num_features=ctx.aft_num_features,
        priority_model=ctx.priority_model, priority_calibrated=ctx.priority_calibrated,
        priority_threshold=ctx.priority_threshold,
        all_features_pri=ctx.all_features_pri, cat_features_pri=ctx.cat_features_pri,
        baseline_table=ctx.baseline_table.get("table", ctx.baseline_table), rainfall_forecast=None,
        ctx=ctx, top_k=3,
    )
    advisory["event_id"] = event_id
    return _to_jsonable(advisory)


def build_advisory_for_existing_event(idx, ctx: InferenceContext) -> dict:
    row = ctx.df_hist.loc[idx]
    advisory = np_pipe.build_advisory(
        row, ctx.df_hist, ctx.G_main, ctx.centrality, ctx.cbr_artifacts,
        fast_models=ctx.fast_models, fast_encoders=ctx.fast_encoders, all_features=ctx.duration_all_features,
        aft_final=ctx.aft_final, aft_columns=ctx.aft_columns,
        aft_cat_features=ctx.aft_cat_features, aft_num_features=ctx.aft_num_features,
        priority_model=ctx.priority_model, priority_calibrated=ctx.priority_calibrated,
        priority_threshold=ctx.priority_threshold,
        all_features_pri=ctx.all_features_pri, cat_features_pri=ctx.cat_features_pri,
        baseline_table=ctx.baseline_table.get("table", ctx.baseline_table), rainfall_forecast=None,
    )
    return _to_jsonable(advisory)

"""
api/meta.py — GET /api/meta
Source of truth: migration/API_CONTRACT.md → Endpoint 1.
"""

from fastapi import APIRouter
from backend.core.context import get_context
from backend.schemas.meta import MetaResponse, ZoneCentroid

router = APIRouter()


@router.get("/meta", response_model=MetaResponse)
def api_meta():
    ctx = get_context()
    df = ctx.df_hist

    causes = sorted(df["event_cause"].dropna().unique().tolist())
    zones = sorted(df["zone_filled"].dropna().unique().tolist())
    veh_types = sorted(df["veh_type"].dropna().unique().tolist()) if "veh_type" in df.columns else []
    event_count = int(len(df))

    # Zone centroids: mean lat/lon of valid_coord events per zone
    zone_centroids = {}
    if "valid_coord" in df.columns:
        valid_df = df[df["valid_coord"] == True]
    else:
        valid_df = df
    for zone in zones:
        zone_df = valid_df[valid_df["zone_filled"] == zone]
        if len(zone_df):
            zone_centroids[zone] = ZoneCentroid(
                latitude=round(float(zone_df["latitude"].mean()), 5),
                longitude=round(float(zone_df["longitude"].mean()), 5),
            )

    return MetaResponse(
        causes=causes,
        zones=zones,
        veh_types=veh_types,
        event_count=event_count,
        zone_centroids=zone_centroids,
        model_version=getattr(ctx, "model_version", "v1"),
    )

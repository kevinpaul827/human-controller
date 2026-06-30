"""Shared contract, produced by perception and consumed by matching_engine."""

from .body_regions import (
    ALL_BODY_REGIONS,
    BODY_CONNECTIONS,
    BODY_LANDMARKS,
    BODY_REGION_GROUPS,
    BODY_REGION_LABELS,
    DEFAULT_SKELETON_REGIONS,
    BodyRegion,
    BodyRegionGroup,
    MEASURABLE_REGIONS,
    connections_for_regions,
    group_region_ids,
    landmarks_for_regions,
    parse_regions,
)
from .landmarks import NUM_LANDMARKS, BlazePose33, PoseLandmarks

__all__ = [
    "NUM_LANDMARKS",
    "BlazePose33",
    "PoseLandmarks",
    "BODY_LANDMARKS",
    "BODY_CONNECTIONS",
    "DEFAULT_SKELETON_REGIONS",
    "BodyRegion",
    "BodyRegionGroup",
    "ALL_BODY_REGIONS",
    "MEASURABLE_REGIONS",
    "BODY_REGION_GROUPS",
    "BODY_REGION_LABELS",
    "parse_regions",
    "landmarks_for_regions",
    "connections_for_regions",
    "group_region_ids",
]

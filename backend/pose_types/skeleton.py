from __future__ import annotations

from collections.abc import Iterable, Mapping
from types import MappingProxyType

from .body_regions import MEASURABLE_REGIONS, BodyRegion
from .landmarks import PoseKeypoint

_B = PoseKeypoint

REGION_CONNECTIONS: Mapping[
    BodyRegion,
    tuple[tuple[PoseKeypoint, PoseKeypoint], ...],
] = MappingProxyType(
    {
        BodyRegion.TORSO: (
            (_B.L_SHOULDER, _B.R_SHOULDER),
            (_B.L_SHOULDER, _B.L_HIP),
            (_B.R_SHOULDER, _B.R_HIP),
            (_B.L_HIP, _B.R_HIP),
        ),
        BodyRegion.LEFT_SHOULDER: (
            (_B.L_HIP, _B.L_SHOULDER),
            (_B.L_SHOULDER, _B.L_ELBOW),
        ),
        BodyRegion.LEFT_ELBOW: (
            (_B.L_SHOULDER, _B.L_ELBOW),
            (_B.L_ELBOW, _B.L_WRIST),
        ),
        BodyRegion.LEFT_WRIST: (
            (_B.L_ELBOW, _B.L_WRIST),
        ),
        BodyRegion.RIGHT_SHOULDER: (
            (_B.R_HIP, _B.R_SHOULDER),
            (_B.R_SHOULDER, _B.R_ELBOW),
        ),
        BodyRegion.RIGHT_ELBOW: (
            (_B.R_SHOULDER, _B.R_ELBOW),
            (_B.R_ELBOW, _B.R_WRIST),
        ),
        BodyRegion.RIGHT_WRIST: (
            (_B.R_ELBOW, _B.R_WRIST),
        ),
        BodyRegion.LEFT_HIP: (
            (_B.L_SHOULDER, _B.L_HIP),
            (_B.L_HIP, _B.L_KNEE),
        ),
        BodyRegion.LEFT_KNEE: (
            (_B.L_HIP, _B.L_KNEE),
            (_B.L_KNEE, _B.L_ANKLE),
        ),
        BodyRegion.LEFT_ANKLE: (
            (_B.L_KNEE, _B.L_ANKLE),
            (_B.L_ANKLE, _B.L_HEEL),
            (_B.L_HEEL, _B.L_FOOT_INDEX),
        ),
        BodyRegion.RIGHT_HIP: (
            (_B.R_SHOULDER, _B.R_HIP),
            (_B.R_HIP, _B.R_KNEE),
        ),
        BodyRegion.RIGHT_KNEE: (
            (_B.R_HIP, _B.R_KNEE),
            (_B.R_KNEE, _B.R_ANKLE),
        ),
        BodyRegion.RIGHT_ANKLE: (
            (_B.R_KNEE, _B.R_ANKLE),
            (_B.R_ANKLE, _B.R_HEEL),
            (_B.R_HEEL, _B.R_FOOT_INDEX),
        ),
    }
)

REGION_LANDMARKS: Mapping[BodyRegion, tuple[int, ...]] = MappingProxyType(
    {
        region: tuple(sorted({int(point) for edge in edges for point in edge}))
        for region, edges in REGION_CONNECTIONS.items()
    }
)


def _norm_edge(a: int, b: int) -> tuple[int, int]:
    return (a, b) if a < b else (b, a)


def landmarks_for_regions(regions: Iterable[BodyRegion]) -> list[int]:
    landmarks: set[int] = set()
    for region in regions:
        landmarks.update(REGION_LANDMARKS[region])
    return sorted(landmarks)


def connections_for_regions(
    regions: Iterable[BodyRegion],
) -> list[tuple[int, int]]:
    connections: set[tuple[int, int]] = set()
    for region in regions:
        for a, b in REGION_CONNECTIONS[region]:
            connections.add(_norm_edge(int(a), int(b)))
    return sorted(connections)


DEFAULT_SKELETON_REGIONS: tuple[BodyRegion, ...] = (
    *MEASURABLE_REGIONS,
    BodyRegion.TORSO,
)

BODY_LANDMARKS: tuple[int, ...] = tuple(
    landmarks_for_regions(DEFAULT_SKELETON_REGIONS)
)
BODY_CONNECTIONS: tuple[tuple[int, int], ...] = tuple(
    connections_for_regions(DEFAULT_SKELETON_REGIONS)
)

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping


class BodyRegion(StrEnum):
    TORSO = "torso"
    LEFT_SHOULDER = "left_shoulder"
    LEFT_ELBOW = "left_elbow"
    LEFT_WRIST = "left_wrist"
    RIGHT_SHOULDER = "right_shoulder"
    RIGHT_ELBOW = "right_elbow"
    RIGHT_WRIST = "right_wrist"
    LEFT_HIP = "left_hip"
    LEFT_KNEE = "left_knee"
    LEFT_ANKLE = "left_ankle"
    RIGHT_HIP = "right_hip"
    RIGHT_KNEE = "right_knee"
    RIGHT_ANKLE = "right_ankle"


ALL_BODY_REGIONS: tuple[BodyRegion, ...] = tuple(BodyRegion)

MEASURABLE_REGIONS: tuple[BodyRegion, ...] = (
    BodyRegion.LEFT_SHOULDER,
    BodyRegion.LEFT_ELBOW,
    BodyRegion.RIGHT_SHOULDER,
    BodyRegion.RIGHT_ELBOW,
    BodyRegion.LEFT_HIP,
    BodyRegion.LEFT_KNEE,
    BodyRegion.LEFT_ANKLE,
    BodyRegion.RIGHT_HIP,
    BodyRegion.RIGHT_KNEE,
    BodyRegion.RIGHT_ANKLE,
)


@dataclass(frozen=True)
class BodyRegionGroup:
    id: str
    label: str
    regions: tuple[BodyRegion, ...]


BODY_REGION_GROUPS: tuple[BodyRegionGroup, ...] = (
    BodyRegionGroup("torso", "Torso", (BodyRegion.TORSO,)),
    BodyRegionGroup(
        "left_arm",
        "Left arm",
        (
            BodyRegion.LEFT_SHOULDER,
            BodyRegion.LEFT_ELBOW,
            BodyRegion.LEFT_WRIST,
        ),
    ),
    BodyRegionGroup(
        "right_arm",
        "Right arm",
        (
            BodyRegion.RIGHT_SHOULDER,
            BodyRegion.RIGHT_ELBOW,
            BodyRegion.RIGHT_WRIST,
        ),
    ),
    BodyRegionGroup(
        "left_leg",
        "Left leg",
        (BodyRegion.LEFT_HIP, BodyRegion.LEFT_KNEE, BodyRegion.LEFT_ANKLE),
    ),
    BodyRegionGroup(
        "right_leg",
        "Right leg",
        (BodyRegion.RIGHT_HIP, BodyRegion.RIGHT_KNEE, BodyRegion.RIGHT_ANKLE),
    ),
)

BODY_REGION_LABELS: Mapping[BodyRegion, str] = MappingProxyType(
    {
        BodyRegion.TORSO: "Torso / core",
        BodyRegion.LEFT_SHOULDER: "Left shoulder",
        BodyRegion.LEFT_ELBOW: "Left elbow",
        BodyRegion.LEFT_WRIST: "Left wrist",
        BodyRegion.RIGHT_SHOULDER: "Right shoulder",
        BodyRegion.RIGHT_ELBOW: "Right elbow",
        BodyRegion.RIGHT_WRIST: "Right wrist",
        BodyRegion.LEFT_HIP: "Left hip",
        BodyRegion.LEFT_KNEE: "Left knee",
        BodyRegion.LEFT_ANKLE: "Left ankle / foot",
        BodyRegion.RIGHT_HIP: "Right hip",
        BodyRegion.RIGHT_KNEE: "Right knee",
        BodyRegion.RIGHT_ANKLE: "Right ankle / foot",
    }
)

_GROUP_REGIONS: Mapping[str, tuple[BodyRegion, ...]] = MappingProxyType(
    {group.id: group.regions for group in BODY_REGION_GROUPS}
)
_REGIONS_BY_VALUE: Mapping[str, BodyRegion] = MappingProxyType(
    {region.value: region for region in BodyRegion}
)


def parse_regions(names: list[str] | None) -> list[BodyRegion]:
    if not names:
        return list(ALL_BODY_REGIONS)
    picked = [_REGIONS_BY_VALUE[name] for name in names if name in _REGIONS_BY_VALUE]
    return picked if picked else list(ALL_BODY_REGIONS)


def group_region_ids(group_id: str) -> list[BodyRegion]:
    return list(_GROUP_REGIONS.get(group_id, ()))

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .landmarks import BlazePose33

_B = BlazePose33


class BodyRegion(str, Enum):
  TORSO = "torso"
  HEAD = "head"

  LEFT_SHOULDER = "left_shoulder"
  LEFT_ELBOW = "left_elbow"
  LEFT_WRIST = "left_wrist"
  LEFT_HAND = "left_hand"

  RIGHT_SHOULDER = "right_shoulder"
  RIGHT_ELBOW = "right_elbow"
  RIGHT_WRIST = "right_wrist"
  RIGHT_HAND = "right_hand"

  LEFT_HIP = "left_hip"
  LEFT_KNEE = "left_knee"
  LEFT_ANKLE = "left_ankle"

  RIGHT_HIP = "right_hip"
  RIGHT_KNEE = "right_knee"
  RIGHT_ANKLE = "right_ankle"


ALL_BODY_REGIONS: list[BodyRegion] = list(BodyRegion)

MEASURABLE_REGIONS: list[BodyRegion] = [
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
]


@dataclass(frozen=True)
class BodyRegionGroup:
  id: str
  label: str
  regions: tuple[BodyRegion, ...]


BODY_REGION_GROUPS: list[BodyRegionGroup] = [
  BodyRegionGroup("torso", "Torso & head", (BodyRegion.TORSO, BodyRegion.HEAD)),
  BodyRegionGroup(
    "left_arm",
    "Left arm",
    (
      BodyRegion.LEFT_SHOULDER,
      BodyRegion.LEFT_ELBOW,
      BodyRegion.LEFT_WRIST,
      BodyRegion.LEFT_HAND,
    ),
  ),
  BodyRegionGroup(
    "right_arm",
    "Right arm",
    (
      BodyRegion.RIGHT_SHOULDER,
      BodyRegion.RIGHT_ELBOW,
      BodyRegion.RIGHT_WRIST,
      BodyRegion.RIGHT_HAND,
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
]

BODY_REGION_LABELS: dict[BodyRegion, str] = {
  BodyRegion.TORSO: "Torso / core",
  BodyRegion.HEAD: "Head / neck",
  BodyRegion.LEFT_SHOULDER: "Left shoulder",
  BodyRegion.LEFT_ELBOW: "Left elbow",
  BodyRegion.LEFT_WRIST: "Left wrist",
  BodyRegion.LEFT_HAND: "Left hand",
  BodyRegion.RIGHT_SHOULDER: "Right shoulder",
  BodyRegion.RIGHT_ELBOW: "Right elbow",
  BodyRegion.RIGHT_WRIST: "Right wrist",
  BodyRegion.RIGHT_HAND: "Right hand",
  BodyRegion.LEFT_HIP: "Left hip",
  BodyRegion.LEFT_KNEE: "Left knee",
  BodyRegion.LEFT_ANKLE: "Left ankle / foot",
  BodyRegion.RIGHT_HIP: "Right hip",
  BodyRegion.RIGHT_KNEE: "Right knee",
  BodyRegion.RIGHT_ANKLE: "Right ankle / foot",
}

REGION_LANDMARKS: dict[BodyRegion, list[int]] = {
  BodyRegion.TORSO: [_B.L_SHOULDER, _B.R_SHOULDER, _B.L_HIP, _B.R_HIP],
  BodyRegion.HEAD: [
    _B.NOSE,
    _B.L_EAR,
    _B.R_EAR,
    _B.L_SHOULDER,
    _B.R_SHOULDER,
  ],
  BodyRegion.LEFT_SHOULDER: [_B.L_HIP, _B.L_SHOULDER, _B.L_ELBOW],
  BodyRegion.LEFT_ELBOW: [_B.L_SHOULDER, _B.L_ELBOW, _B.L_WRIST],
  BodyRegion.LEFT_WRIST: [_B.L_ELBOW, _B.L_WRIST, _B.L_PINKY, _B.L_INDEX, _B.L_THUMB],
  BodyRegion.LEFT_HAND: [_B.L_WRIST, _B.L_PINKY, _B.L_INDEX, _B.L_THUMB],
  BodyRegion.RIGHT_SHOULDER: [_B.R_HIP, _B.R_SHOULDER, _B.R_ELBOW],
  BodyRegion.RIGHT_ELBOW: [_B.R_SHOULDER, _B.R_ELBOW, _B.R_WRIST],
  BodyRegion.RIGHT_WRIST: [_B.R_ELBOW, _B.R_WRIST, _B.R_PINKY, _B.R_INDEX, _B.R_THUMB],
  BodyRegion.RIGHT_HAND: [_B.R_WRIST, _B.R_PINKY, _B.R_INDEX, _B.R_THUMB],
  BodyRegion.LEFT_HIP: [_B.L_SHOULDER, _B.L_HIP, _B.L_KNEE],
  BodyRegion.LEFT_KNEE: [_B.L_HIP, _B.L_KNEE, _B.L_ANKLE],
  BodyRegion.LEFT_ANKLE: [_B.L_KNEE, _B.L_ANKLE, _B.L_HEEL, _B.L_FOOT_INDEX],
  BodyRegion.RIGHT_HIP: [_B.R_SHOULDER, _B.R_HIP, _B.R_KNEE],
  BodyRegion.RIGHT_KNEE: [_B.R_HIP, _B.R_KNEE, _B.R_ANKLE],
  BodyRegion.RIGHT_ANKLE: [_B.R_KNEE, _B.R_ANKLE, _B.R_HEEL, _B.R_FOOT_INDEX],
}

REGION_CONNECTIONS: dict[BodyRegion, list[tuple[int, int]]] = {
  BodyRegion.TORSO: [
    (_B.L_SHOULDER, _B.R_SHOULDER),
    (_B.L_SHOULDER, _B.L_HIP),
    (_B.R_SHOULDER, _B.R_HIP),
    (_B.L_HIP, _B.R_HIP),
  ],
  BodyRegion.HEAD: [
    (_B.NOSE, _B.L_EAR),
    (_B.NOSE, _B.R_EAR),
    (_B.L_EAR, _B.R_EAR),
    (_B.L_EAR, _B.L_SHOULDER),
    (_B.R_EAR, _B.R_SHOULDER),
  ],
  BodyRegion.LEFT_SHOULDER: [
    (_B.L_HIP, _B.L_SHOULDER),
    (_B.L_SHOULDER, _B.L_ELBOW),
  ],
  BodyRegion.LEFT_ELBOW: [
    (_B.L_SHOULDER, _B.L_ELBOW),
    (_B.L_ELBOW, _B.L_WRIST),
  ],
  BodyRegion.LEFT_WRIST: [
    (_B.L_ELBOW, _B.L_WRIST),
    (_B.L_WRIST, _B.L_PINKY),
    (_B.L_WRIST, _B.L_INDEX),
    (_B.L_WRIST, _B.L_THUMB),
  ],
  BodyRegion.LEFT_HAND: [
    (_B.L_WRIST, _B.L_PINKY),
    (_B.L_WRIST, _B.L_INDEX),
    (_B.L_WRIST, _B.L_THUMB),
  ],
  BodyRegion.RIGHT_SHOULDER: [
    (_B.R_HIP, _B.R_SHOULDER),
    (_B.R_SHOULDER, _B.R_ELBOW),
  ],
  BodyRegion.RIGHT_ELBOW: [
    (_B.R_SHOULDER, _B.R_ELBOW),
    (_B.R_ELBOW, _B.R_WRIST),
  ],
  BodyRegion.RIGHT_WRIST: [
    (_B.R_ELBOW, _B.R_WRIST),
    (_B.R_WRIST, _B.R_PINKY),
    (_B.R_WRIST, _B.R_INDEX),
    (_B.R_WRIST, _B.R_THUMB),
  ],
  BodyRegion.RIGHT_HAND: [
    (_B.R_WRIST, _B.R_PINKY),
    (_B.R_WRIST, _B.R_INDEX),
    (_B.R_WRIST, _B.R_THUMB),
  ],
  BodyRegion.LEFT_HIP: [
    (_B.L_SHOULDER, _B.L_HIP),
    (_B.L_HIP, _B.L_KNEE),
  ],
  BodyRegion.LEFT_KNEE: [
    (_B.L_HIP, _B.L_KNEE),
    (_B.L_KNEE, _B.L_ANKLE),
  ],
  BodyRegion.LEFT_ANKLE: [
    (_B.L_KNEE, _B.L_ANKLE),
    (_B.L_ANKLE, _B.L_HEEL),
    (_B.L_HEEL, _B.L_FOOT_INDEX),
  ],
  BodyRegion.RIGHT_HIP: [
    (_B.R_SHOULDER, _B.R_HIP),
    (_B.R_HIP, _B.R_KNEE),
  ],
  BodyRegion.RIGHT_KNEE: [
    (_B.R_HIP, _B.R_KNEE),
    (_B.R_KNEE, _B.R_ANKLE),
  ],
  BodyRegion.RIGHT_ANKLE: [
    (_B.R_KNEE, _B.R_ANKLE),
    (_B.R_ANKLE, _B.R_HEEL),
    (_B.R_HEEL, _B.R_FOOT_INDEX),
  ],
}


def parse_regions(names: list[str] | None) -> list[BodyRegion]:
  if not names:
    return list(ALL_BODY_REGIONS)
  valid = {r.value: r for r in BodyRegion}
  picked = [valid[n] for n in names if n in valid]
  return picked if picked else list(ALL_BODY_REGIONS)


def _norm_edge(a: int, b: int) -> tuple[int, int]:
  return (a, b) if a < b else (b, a)


def landmarks_for_regions(regions: list[BodyRegion]) -> list[int]:
  out: set[int] = set()
  for region in regions:
    out.update(REGION_LANDMARKS[region])
  return sorted(out)


def connections_for_regions(regions: list[BodyRegion]) -> list[tuple[int, int]]:
  out: set[tuple[int, int]] = set()
  for region in regions:
    for a, b in REGION_CONNECTIONS[region]:
      out.add(_norm_edge(a, b))
  return sorted(out)


def group_region_ids(group_id: str) -> list[BodyRegion]:
  for group in BODY_REGION_GROUPS:
    if group.id == group_id:
      return list(group.regions)
  return []


DEFAULT_SKELETON_REGIONS: list[BodyRegion] = [*MEASURABLE_REGIONS, BodyRegion.TORSO]

BODY_LANDMARKS: list[int] = landmarks_for_regions(DEFAULT_SKELETON_REGIONS)
BODY_CONNECTIONS: list[tuple[int, int]] = connections_for_regions(DEFAULT_SKELETON_REGIONS)

_EXPECTED_LANDMARK_COUNT = 16
assert len(BODY_LANDMARKS) == _EXPECTED_LANDMARK_COUNT
assert len(BODY_CONNECTIONS) == 16

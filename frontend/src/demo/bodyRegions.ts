export type BodyRegionId =
  | "torso"
  | "head"
  | "left_shoulder"
  | "left_elbow"
  | "left_wrist"
  | "left_hand"
  | "right_shoulder"
  | "right_elbow"
  | "right_wrist"
  | "right_hand"
  | "left_hip"
  | "left_knee"
  | "left_ankle"
  | "right_hip"
  | "right_knee"
  | "right_ankle";

export type BodyRegionGroupId = "torso" | "left_arm" | "right_arm" | "left_leg" | "right_leg";

export const ALL_BODY_REGIONS: BodyRegionId[] = [
  "torso",
  "head",
  "left_shoulder",
  "left_elbow",
  "left_wrist",
  "left_hand",
  "right_shoulder",
  "right_elbow",
  "right_wrist",
  "right_hand",
  "left_hip",
  "left_knee",
  "left_ankle",
  "right_hip",
  "right_knee",
  "right_ankle",
];

export const MEASURABLE_REGIONS: BodyRegionId[] = [
  "left_shoulder",
  "left_elbow",
  "right_shoulder",
  "right_elbow",
  "left_hip",
  "left_knee",
  "left_ankle",
  "right_hip",
  "right_knee",
  "right_ankle",
];

export const BODY_REGION_LABELS: Record<BodyRegionId, string> = {
  torso: "Torso / core",
  head: "Head / neck",
  left_shoulder: "Left shoulder",
  left_elbow: "Left elbow",
  left_wrist: "Left wrist",
  left_hand: "Left hand",
  right_shoulder: "Right shoulder",
  right_elbow: "Right elbow",
  right_wrist: "Right wrist",
  right_hand: "Right hand",
  left_hip: "Left hip",
  left_knee: "Left knee",
  left_ankle: "Left ankle / foot",
  right_hip: "Right hip",
  right_knee: "Right knee",
  right_ankle: "Right ankle / foot",
};

export const BODY_REGION_HINTS: Partial<Record<BodyRegionId, string>> = {
  torso: "Planks, posture, trunk stability",
  head: "Neck alignment, cervical ROM",
  left_shoulder: "Lateral raises, shoulder press",
  left_elbow: "Bicep curls, tricep extensions",
  left_wrist: "Wrist flexion / extension",
  left_hand: "Grip, finger opening",
  right_shoulder: "Lateral raises, shoulder press",
  right_elbow: "Bicep curls, tricep extensions",
  right_wrist: "Wrist flexion / extension",
  right_hand: "Grip, finger opening",
  left_hip: "Hip hikes, leg marches, abduction",
  left_knee: "Squats, leg extensions",
  left_ankle: "Ankle pumps, calf raises",
  right_hip: "Hip hikes, leg marches, abduction",
  right_knee: "Squats, leg extensions",
  right_ankle: "Ankle pumps, calf raises",
};

export type BodyRegionGroup = {
  id: BodyRegionGroupId;
  label: string;
  regions: BodyRegionId[];
};

export const BODY_REGION_GROUPS: BodyRegionGroup[] = [
  { id: "torso", label: "Torso & head", regions: ["torso", "head"] },
  {
    id: "left_arm",
    label: "Left arm",
    regions: ["left_shoulder", "left_elbow", "left_wrist", "left_hand"],
  },
  {
    id: "right_arm",
    label: "Right arm",
    regions: ["right_shoulder", "right_elbow", "right_wrist", "right_hand"],
  },
  {
    id: "left_leg",
    label: "Left leg",
    regions: ["left_hip", "left_knee", "left_ankle"],
  },
  {
    id: "right_leg",
    label: "Right leg",
    regions: ["right_hip", "right_knee", "right_ankle"],
  },
];

const REGION_LANDMARKS: Record<BodyRegionId, number[]> = {
  torso: [11, 12, 23, 24],
  head: [0, 7, 8, 11, 12],
  left_shoulder: [23, 11, 13],
  left_elbow: [11, 13, 15],
  left_wrist: [13, 15, 17, 19, 21],
  left_hand: [15, 17, 19, 21],
  right_shoulder: [24, 12, 14],
  right_elbow: [12, 14, 16],
  right_wrist: [14, 16, 18, 20, 22],
  right_hand: [16, 18, 20, 22],
  left_hip: [11, 23, 25],
  left_knee: [23, 25, 27],
  left_ankle: [25, 27, 29, 31],
  right_hip: [12, 24, 26],
  right_knee: [24, 26, 28],
  right_ankle: [26, 28, 30, 32],
};

const REGION_CONNECTIONS: Record<BodyRegionId, [number, number][]> = {
  torso: [
    [11, 12],
    [11, 23],
    [12, 24],
    [23, 24],
  ],
  head: [
    [0, 7],
    [0, 8],
    [7, 8],
    [7, 11],
    [8, 12],
  ],
  left_shoulder: [
    [23, 11],
    [11, 13],
  ],
  left_elbow: [
    [11, 13],
    [13, 15],
  ],
  left_wrist: [
    [13, 15],
    [15, 17],
    [15, 19],
    [15, 21],
  ],
  left_hand: [
    [15, 17],
    [15, 19],
    [15, 21],
  ],
  right_shoulder: [
    [24, 12],
    [12, 14],
  ],
  right_elbow: [
    [12, 14],
    [14, 16],
  ],
  right_wrist: [
    [14, 16],
    [16, 18],
    [16, 20],
    [16, 22],
  ],
  right_hand: [
    [16, 18],
    [16, 20],
    [16, 22],
  ],
  left_hip: [
    [11, 23],
    [23, 25],
  ],
  left_knee: [
    [23, 25],
    [25, 27],
  ],
  left_ankle: [
    [25, 27],
    [27, 29],
    [29, 31],
  ],
  right_hip: [
    [12, 24],
    [24, 26],
  ],
  right_knee: [
    [24, 26],
    [26, 28],
  ],
  right_ankle: [
    [26, 28],
    [28, 30],
    [30, 32],
  ],
};

export function isMeasurableRegion(region: BodyRegionId): boolean {
  return MEASURABLE_REGIONS.includes(region);
}

export function hasMeasurableSelection(regions: BodyRegionId[]): boolean {
  return regions.some(isMeasurableRegion);
}

export function regionsInGroup(groupId: BodyRegionGroupId): BodyRegionId[] {
  return BODY_REGION_GROUPS.find((g) => g.id === groupId)?.regions ?? [];
}

export function landmarksForRegions(regions: BodyRegionId[]): number[] {
  const out = new Set<number>();
  for (const region of regions) {
    for (const i of REGION_LANDMARKS[region]) out.add(i);
  }
  return [...out].sort((a, b) => a - b);
}

export function connectionsForRegions(regions: BodyRegionId[]): [number, number][] {
  const seen = new Set<string>();
  const out: [number, number][] = [];
  for (const region of regions) {
    for (const [a, b] of REGION_CONNECTIONS[region]) {
      const key = a < b ? `${a}-${b}` : `${b}-${a}`;
      if (seen.has(key)) continue;
      seen.add(key);
      out.push([a, b]);
    }
  }
  return out;
}

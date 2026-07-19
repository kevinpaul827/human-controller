export type SavedGesture = {
  schemaVersion: number;
  gesture_id: string;
  name: string;
  type: string;
  regions: string[];
  active_joints: string[];
  target_angles: Record<string, number>;
  tolerance_deg: Record<string, number>;
  trajectory: Array<Record<string, unknown>>;
  fps: number;
};

export type SaveGesturePayload = {
  gesture_id?: string;
  name: string;
  regions: string[];
  active_joints: string[];
  target_angles: Record<string, number>;
  tolerance_deg?: Record<string, number>;
};

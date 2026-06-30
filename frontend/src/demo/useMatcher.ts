import { useCallback, useEffect, useRef, useState } from "react";
import type { Frame } from "./usePose";
import { ALL_BODY_REGIONS, type BodyRegionId } from "./bodyRegions";

const WS_URL =
  (import.meta.env.VITE_WS_URL as string | undefined) ?? "ws://localhost:8000/ws";

export type Gesture = {
  gesture_id: string;
  name: string;
  active_joints: string[];
  target_angles: Record<string, number>;
};
export type Match = { gesture_id: string; name: string; score: number; matched: boolean };
export type Angles = Record<string, number | null>;
export type Mode = "idle" | "calibrate" | "match";

export function useMatcher() {
  const wsRef = useRef<WebSocket | null>(null);
  const focusRef = useRef<BodyRegionId[]>(ALL_BODY_REGIONS);
  const [connected, setConnected] = useState(false);
  const [gestures, setGestures] = useState<Gesture[]>([]);
  const [match, setMatch] = useState<Match | null>(null);
  const [angles, setAngles] = useState<Angles>({});
  const [reps, setReps] = useState<Angles[]>([]);
  const [focusRegions, setFocusRegionsState] = useState<BodyRegionId[]>(ALL_BODY_REGIONS);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;
    let opened = false;

    ws.onopen = () => {
      opened = true;
      setConnected(true);
      setError(null);
    };

    ws.onclose = () => {
      if (wsRef.current !== ws) return;
      setConnected(false);
      if (!opened) {
        setError("Cannot reach backend — start it on :8000 (see demo_server/README).");
      }
    };

    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data);
      switch (msg.type) {
        case "tick":
          setError(null);
          setAngles(msg.angles);
          if (msg.match) setMatch(msg.match);
          break;
        case "calibration":
          setReps([]);
          if (Array.isArray(msg.regions)) {
            setFocusRegionsState(msg.regions);
            focusRef.current = msg.regions;
          }
          break;
        case "focus_regions":
          if (Array.isArray(msg.regions)) {
            setFocusRegionsState(msg.regions);
            focusRef.current = msg.regions;
          }
          if (msg.reps_cleared) setReps([]);
          break;
        case "rep_captured":
          setReps((prev) => [...prev, msg.angles]);
          break;
        case "gestures":
          setGestures(msg.items);
          break;
        case "error":
          setError(msg.message);
          break;
      }
    };

    return () => {
      wsRef.current = null;
      ws.close();
    };
  }, []);

  const send = useCallback((obj: object) => {
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(obj));
  }, []);

  const sendFrame = useCallback((f: Frame) => send({ type: "frame", ...f }), [send]);

  const setMode = useCallback(
    (mode: Mode) => {
      setMatch(null);
      setReps([]);
      send({ type: "set_mode", mode });
    },
    [send],
  );

  const setFocusRegions = useCallback(
    (regions: BodyRegionId[]) => {
      const next = regions.length > 0 ? regions : ALL_BODY_REGIONS;
      focusRef.current = next;
      setFocusRegionsState(next);
      send({ type: "set_focus_regions", regions: next });
    },
    [send],
  );

  const startCalibration = useCallback(() => {
    setReps([]);
    send({ type: "start_calibration", regions: focusRef.current });
  }, [send]);

  const captureRep = useCallback(() => send({ type: "capture_rep" }), [send]);
  const saveGesture = useCallback((name: string) => send({ type: "save_gesture", name }), [send]);
  const deleteGesture = useCallback((id: string) => send({ type: "delete_gesture", id }), [send]);

  return {
    connected,
    gestures,
    match,
    angles,
    reps,
    focusRegions,
    error,
    sendFrame,
    setMode,
    setFocusRegions,
    startCalibration,
    captureRep,
    saveGesture,
    deleteGesture,
  };
}

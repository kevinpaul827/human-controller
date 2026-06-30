import { useEffect, useRef, useState } from "react";
import {
  FilesetResolver,
  PoseLandmarker,
  type PoseLandmarkerResult,
} from "@mediapipe/tasks-vision";
import {
  ALL_BODY_REGIONS,
  connectionsForRegions,
  landmarksForRegions,
  type BodyRegionId,
} from "./bodyRegions";

// wasm pin
const WASM = "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.35/wasm";
const MODEL =
  "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task";

const DRAW_VIS = 0.5;

export type Frame = { landmarks: number[][]; visibility: number[] };

export function usePose(
  onFrame: (f: Frame) => void,
  focusRegions: BodyRegionId[] = ALL_BODY_REGIONS,
) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const onFrameRef = useRef(onFrame);
  onFrameRef.current = onFrame;
  const focusRef = useRef(focusRegions);
  focusRef.current = focusRegions;
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let landmarker: PoseLandmarker | null = null;
    let stream: MediaStream | null = null;
    let raf = 0;
    let lastTime = -1;
    let cancelled = false;

    async function makeLandmarker(): Promise<PoseLandmarker> {
      const vision = await FilesetResolver.forVisionTasks(WASM);
      const opts = (delegate: "GPU" | "CPU") =>
        PoseLandmarker.createFromOptions(vision, {
          baseOptions: { modelAssetPath: MODEL, delegate },
          runningMode: "VIDEO" as const,
          numPoses: 1,
        });
      try {
        return await opts("GPU");
      } catch {
        return await opts("CPU");
      }
    }

    async function init() {
      try {
        landmarker = await makeLandmarker();
        stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 640, height: 480 },
        });
        const video = videoRef.current;
        if (!video || cancelled) return;
        video.srcObject = stream;
        await video.play();
        setReady(true);
        loop();
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      }
    }

    type NLandmark = { x: number; y: number; z: number; visibility?: number };

    function draw(norm: NLandmark[]) {
      const canvas = canvasRef.current;
      const video = videoRef.current;
      if (!canvas || !video || !video.videoWidth) return;
      if (canvas.width !== video.videoWidth) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
      }
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const regions = focusRef.current;
      const body = landmarksForRegions(regions);
      const bodyConnections = connectionsForRegions(regions);
      const seen = (i: number) => (norm[i].visibility ?? 0) >= DRAW_VIS;
      const px = (i: number): [number, number] => [
        norm[i].x * canvas.width,
        norm[i].y * canvas.height,
      ];
      ctx.lineWidth = 4;
      ctx.strokeStyle = "#22c55e";
      for (const [a, b] of bodyConnections) {
        if (!seen(a) || !seen(b)) continue;
        const [ax, ay] = px(a);
        const [bx, by] = px(b);
        ctx.beginPath();
        ctx.moveTo(ax, ay);
        ctx.lineTo(bx, by);
        ctx.stroke();
      }
      ctx.fillStyle = "#ef4444";
      for (const i of body) {
        if (!seen(i)) continue;
        const [x, y] = px(i);
        ctx.beginPath();
        ctx.arc(x, y, 5, 0, 2 * Math.PI);
        ctx.fill();
      }
    }

    function loop() {
      const video = videoRef.current;
      if (cancelled || !landmarker || !video) return;
      if (video.currentTime !== lastTime) {
        lastTime = video.currentTime;
        const res: PoseLandmarkerResult = landmarker.detectForVideo(
          video,
          performance.now(),
        );
        const world = res.worldLandmarks?.[0];
        const norm = res.landmarks?.[0] as NLandmark[] | undefined;
        if (world && norm && world.length === 33) {
          onFrameRef.current({
            landmarks: world.map((p) => [p.x, p.y, p.z]),
            visibility: norm.map((p) => p.visibility ?? 0),
          });
          draw(norm);
        }
      }
      raf = requestAnimationFrame(loop);
    }

    init();
    return () => {
      cancelled = true;
      cancelAnimationFrame(raf);
      stream?.getTracks().forEach((t) => t.stop());
      landmarker?.close();
    };
  }, []);

  return { videoRef, canvasRef, ready, error };
}

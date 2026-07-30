import { useEffect, useRef, useState } from "react";

type PreviewBounds = {
  left: number;
  top: number;
  width: number;
  height: number;
  devicePixelRatio?: number;
};

type DesktopCameraPreviewBridge = {
  updatePreviewBounds(bounds: PreviewBounds): Promise<void>;
  onPreviewAspectRatio(listener: (aspectRatio: number) => void): () => void;
};

type UseDesktopCameraPreviewOptions = {
  bridge: DesktopCameraPreviewBridge;
  isLive: boolean;
  defaultAspectRatio?: number;
  trackElapsed?: boolean;
};

const DEFAULT_ASPECT_RATIO = 4 / 3;

const useDesktopCameraPreview = ({
  bridge,
  isLive,
  defaultAspectRatio = DEFAULT_ASPECT_RATIO,
  trackElapsed = true,
}: UseDesktopCameraPreviewOptions) => {
  const [elapsed, setElapsed] = useState(0);
  const [previewAspectRatio, setPreviewAspectRatio] =
    useState(defaultAspectRatio);
  const previewViewportRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!isLive || !trackElapsed) {
      return;
    }

    const intervalId = window.setInterval(() => {
      setElapsed((current) => Number((current + 0.1).toFixed(1)));
    }, 100);

    return () => window.clearInterval(intervalId);
  }, [isLive, trackElapsed]);

  useEffect(() => {
    const panel = previewViewportRef.current;

    if (!panel) {
      return;
    }

    let frameId = 0;

    const syncPreviewBounds = () => {
      frameId = 0;

      const rect = panel.getBoundingClientRect();

      void bridge.updatePreviewBounds({
        left: rect.left,
        top: rect.top,
        width: rect.width,
        height: rect.height,
        devicePixelRatio: window.devicePixelRatio,
      });
    };

    const scheduleSync = () => {
      if (frameId !== 0) {
        return;
      }

      frameId = window.requestAnimationFrame(syncPreviewBounds);
    };

    scheduleSync();

    const resizeObserver = new ResizeObserver(() => {
      scheduleSync();
    });

    resizeObserver.observe(panel);
    window.addEventListener("resize", scheduleSync);
    window.addEventListener("scroll", scheduleSync, true);

    return () => {
      resizeObserver.disconnect();
      window.removeEventListener("resize", scheduleSync);
      window.removeEventListener("scroll", scheduleSync, true);

      if (frameId !== 0) {
        window.cancelAnimationFrame(frameId);
      }

      void bridge.updatePreviewBounds({
        left: 0,
        top: 0,
        width: 0,
        height: 0,
        devicePixelRatio: window.devicePixelRatio,
      });
    };
  }, [bridge, isLive, previewAspectRatio]);

  useEffect(() => {
    return bridge.onPreviewAspectRatio((aspectRatio) => {
      if (Number.isFinite(aspectRatio) && aspectRatio > 0) {
        setPreviewAspectRatio(aspectRatio);
      }
    });
  }, [bridge]);

  return {
    elapsed,
    previewAspectRatio,
    previewViewportRef,
    setElapsed,
  };
};

export default useDesktopCameraPreview;

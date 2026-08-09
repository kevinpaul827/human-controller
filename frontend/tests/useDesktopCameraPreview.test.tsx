// @vitest-environment jsdom

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import useDesktopCameraPreview from "../src/hooks/useDesktopCameraPreview";

Object.assign(globalThis, { IS_REACT_ACT_ENVIRONMENT: true });

type Bridge = {
  updatePreviewBounds: (bounds: {
    left: number;
    top: number;
    width: number;
    height: number;
    devicePixelRatio?: number;
  }) => Promise<void>;
  onPreviewAspectRatio: (listener: (aspectRatio: number) => void) => () => void;
};

type HookValue = ReturnType<typeof useDesktopCameraPreview>;

class MockResizeObserver {
  callback: ResizeObserverCallback;
  observe = vi.fn();
  disconnect = vi.fn();

  constructor(callback: ResizeObserverCallback) {
    this.callback = callback;
  }

  trigger() {
    this.callback([], this as unknown as ResizeObserver);
  }
}

const HookHarness = ({
  bridge,
  isLive,
  trackElapsed = false,
  onRender,
}: {
  bridge: Bridge;
  isLive: boolean;
  trackElapsed?: boolean;
  onRender: (value: HookValue) => void;
}) => {
  const value = useDesktopCameraPreview({ bridge, isLive, trackElapsed });
  onRender(value);
  return <div data-testid="preview" ref={value.previewViewportRef} />;
};

describe("useDesktopCameraPreview", () => {
  let container: HTMLDivElement;
  let root: Root;
  let latest: HookValue | null;
  let resizeObserverInstances: MockResizeObserver[];
  let rafCallbacks: Map<number, FrameRequestCallback>;
  let nextRafId: number;

  const runAnimationFrame = async () => {
    await act(async () => {
      const callbacks = Array.from(rafCallbacks.values());
      rafCallbacks.clear();
      callbacks.forEach((callback) => callback(0));
      await Promise.resolve();
    });
  };

  const getLatest = () => {
    if (!latest) {
      throw new Error("Hook result is unavailable.");
    }
    return latest;
  };

  const setRect = (
    panel: HTMLDivElement,
    rect: { left: number; top: number; width: number; height: number },
  ) => {
    panel.getBoundingClientRect = vi.fn(
      () =>
        ({
          ...rect,
          right: rect.left + rect.width,
          bottom: rect.top + rect.height,
          x: rect.left,
          y: rect.top,
          toJSON: () => ({}),
        }) as DOMRect,
    );
  };

  beforeEach(() => {
    container = document.createElement("div");
    document.body.append(container);
    root = createRoot(container);
    latest = null;
    resizeObserverInstances = [];
    rafCallbacks = new Map();
    nextRafId = 1;

    Object.defineProperty(window, "devicePixelRatio", {
      configurable: true,
      value: 1,
    });

    vi.stubGlobal(
      "ResizeObserver",
      vi.fn((callback: ResizeObserverCallback) => {
        const observer = new MockResizeObserver(callback);
        resizeObserverInstances.push(observer);
        return observer;
      }),
    );

    vi.spyOn(window, "requestAnimationFrame").mockImplementation((callback) => {
      const id = nextRafId++;
      rafCallbacks.set(id, callback);
      return id;
    });

    vi.spyOn(window, "cancelAnimationFrame").mockImplementation((id) => {
      rafCallbacks.delete(id);
    });
  });

  afterEach(() => {
    if (root) {
      act(() => {
        root.unmount();
      });
    }
    container?.remove();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("syncs bounds on mount and when panel size or aspect ratio changes", async () => {
    let aspectRatioListener: ((ratio: number) => void) | null = null;
    const unsubscribe = vi.fn();
    const bridge: Bridge = {
      updatePreviewBounds: vi.fn().mockResolvedValue(undefined),
      onPreviewAspectRatio: vi.fn((listener) => {
        aspectRatioListener = listener;
        return unsubscribe;
      }),
    };

    act(() => {
      root.render(
        <HookHarness
          bridge={bridge}
          isLive
          onRender={(value) => {
            latest = value;
          }}
        />,
      );
    });

    const panel = container.querySelector('[data-testid="preview"]');
    if (!(panel instanceof HTMLDivElement)) {
      throw new Error("Preview panel not mounted.");
    }

    setRect(panel, { left: 12, top: 18, width: 320, height: 240 });
    await runAnimationFrame();
    expect(bridge.updatePreviewBounds).toHaveBeenCalledWith({
      left: 12,
      top: 18,
      width: 320,
      height: 240,
      devicePixelRatio: 1,
    });

    setRect(panel, { left: 16, top: 20, width: 420, height: 300 });
    resizeObserverInstances[0]?.trigger();
    await runAnimationFrame();
    expect(bridge.updatePreviewBounds).toHaveBeenCalledWith({
      left: 16,
      top: 20,
      width: 420,
      height: 300,
      devicePixelRatio: 1,
    });

    Object.defineProperty(window, "devicePixelRatio", {
      configurable: true,
      value: 2,
    });
    act(() => {
      window.dispatchEvent(new Event("resize"));
    });
    await runAnimationFrame();
    expect(bridge.updatePreviewBounds).toHaveBeenCalledWith({
      left: 16,
      top: 20,
      width: 420,
      height: 300,
      devicePixelRatio: 2,
    });

    await act(async () => {
      aspectRatioListener?.(16 / 9);
      await Promise.resolve();
    });
    await runAnimationFrame();

    expect(getLatest().previewAspectRatio).toBe(16 / 9);
    expect(bridge.updatePreviewBounds).toHaveBeenCalledTimes(5);
    expect(unsubscribe).not.toHaveBeenCalled();
  });

  it("cleans up observers and resets preview bounds on unmount", async () => {
    const unsubscribe = vi.fn();
    const bridge: Bridge = {
      updatePreviewBounds: vi.fn().mockResolvedValue(undefined),
      onPreviewAspectRatio: vi.fn(() => unsubscribe),
    };

    act(() => {
      root.render(
        <HookHarness
          bridge={bridge}
          isLive
          onRender={(value) => {
            latest = value;
          }}
        />,
      );
    });

    const panel = container.querySelector('[data-testid="preview"]');
    if (!(panel instanceof HTMLDivElement)) {
      throw new Error("Preview panel not mounted.");
    }
    setRect(panel, { left: 4, top: 8, width: 200, height: 120 });
    await runAnimationFrame();

    const observer = resizeObserverInstances[0];
    act(() => {
      root.unmount();
    });

    expect(observer?.disconnect).toHaveBeenCalledTimes(1);
    expect(unsubscribe).toHaveBeenCalledTimes(1);
    expect(bridge.updatePreviewBounds).toHaveBeenLastCalledWith({
      left: 0,
      top: 0,
      width: 0,
      height: 0,
      devicePixelRatio: 1,
    });
  });

  it("surfaces a desktop runtime bridge error when runtime is unavailable", () => {
    const consoleErrorSpy = vi
      .spyOn(console, "error")
      .mockImplementation(() => {
        return undefined;
      });
    const bridge = {
      updatePreviewBounds: vi.fn().mockResolvedValue(undefined),
      onPreviewAspectRatio: vi.fn(() => {
        throw new Error("Desktop bridge unavailable");
      }),
    } as unknown as Bridge;

    expect(() => {
      act(() => {
        root.render(
          <HookHarness
            bridge={bridge}
            isLive
            onRender={(value) => {
              latest = value;
            }}
          />,
        );
      });
    }).toThrowError("Desktop bridge unavailable");

    consoleErrorSpy.mockRestore();
  });
});

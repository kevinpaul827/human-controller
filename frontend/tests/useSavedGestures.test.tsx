import { act, type ComponentType } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import useActiveProfile from "../src/hooks/useActiveProfile";
import useSavedGestures from "../src/hooks/useSavedGestures";
import { useAppState } from "../src/state/appStateContext";
import type { SavedGestureSummary } from "../src/types/calibrate";

const bridgeMocks = vi.hoisted(() => ({
  listSavedGestures: vi.fn(),
  getLoadedSessionGestures: vi.fn(),
  loadSavedGesture: vi.fn(),
}));

vi.mock("../src/services/calibrateBridge", () => ({
  default: bridgeMocks,
}));

Object.assign(globalThis, { IS_REACT_ACT_ENVIRONMENT: true });

type HookValue = ReturnType<typeof useSavedGestures>;

type Deferred<T> = {
  promise: Promise<T>;
  resolve: (value: T) => void;
  reject: (error: unknown) => void;
};

const deferred = <T,>(): Deferred<T> => {
  let resolve!: (value: T) => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
};

const flushAsync = async () => {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
};

const HookHarness = ({
  onRender,
}: {
  onRender: (value: HookValue) => void;
}) => {
  const value = useSavedGestures();
  onRender(value);
  return null;
};

describe("useSavedGestures", () => {
  let container: HTMLDivElement;
  let root: Root;
  let latest: HookValue | null;
  let renderCount: number;

  const getLatest = () => {
    if (!latest) {
      throw new Error("Hook result is unavailable.");
    }
    return latest;
  };

  beforeEach(() => {
    vi.clearAllMocks();
    container = document.createElement("div");
    document.body.append(container);
    root = createRoot(container);
    latest = null;
    renderCount = 0;
  });

  afterEach(() => {
    if (root) {
      act(() => {
        root.unmount();
      });
    }
    container?.remove();
  });

  const renderHook = () => {
    act(() => {
      root.render(
        <HookHarness
          onRender={(value) => {
            latest = value;
            renderCount += 1;
          }}
        />,
      );
    });
  };

  it("loads gestures on mount and toggles loading state", async () => {
    const availableDeferred = deferred<SavedGestureSummary[]>();
    const loadedDeferred = deferred<SavedGestureSummary[]>();
    bridgeMocks.listSavedGestures.mockReturnValueOnce(availableDeferred.promise);
    bridgeMocks.getLoadedSessionGestures.mockReturnValueOnce(
      loadedDeferred.promise,
    );

    renderHook();
    await flushAsync();

    expect(getLatest().isLoading).toBe(true);
    expect(getLatest().availableGestures).toEqual([]);
    expect(getLatest().loadedGestures).toEqual([]);

    await act(async () => {
      availableDeferred.resolve([{ gestureId: "g-1", name: "Raise arm" }]);
      loadedDeferred.resolve([{ gestureId: "g-2", name: "Squat" }]);
      await Promise.all([availableDeferred.promise, loadedDeferred.promise]);
    });
    await flushAsync();

    expect(getLatest().isLoading).toBe(false);
    expect(getLatest().availableGestures).toEqual([
      { gestureId: "g-1", name: "Raise arm" },
    ]);
    expect(getLatest().loadedGestures).toEqual([
      { gestureId: "g-2", name: "Squat" },
    ]);
  });

  it("keeps empty arrays when the bridge returns no saved gestures", async () => {
    bridgeMocks.listSavedGestures.mockResolvedValueOnce([]);
    bridgeMocks.getLoadedSessionGestures.mockResolvedValueOnce([]);

    renderHook();
    await flushAsync();
    await flushAsync();

    expect(getLatest().isLoading).toBe(false);
    expect(getLatest().availableGestures).toEqual([]);
    expect(getLatest().loadedGestures).toEqual([]);
  });

  it("clears loading state when bridge requests fail", async () => {
    bridgeMocks.listSavedGestures
      .mockResolvedValueOnce([{ gestureId: "g-1", name: "Raise arm" }])
      .mockRejectedValueOnce(new Error("Bridge unavailable"));
    bridgeMocks.getLoadedSessionGestures
      .mockResolvedValueOnce([{ gestureId: "g-2", name: "Squat" }])
      .mockResolvedValueOnce([{ gestureId: "g-2", name: "Squat" }]);

    renderHook();
    await flushAsync();
    await flushAsync();

    await act(async () => {
      await expect(getLatest().refresh()).rejects.toThrow("Bridge unavailable");
    });

    expect(getLatest().isLoading).toBe(false);
    expect(getLatest().availableGestures).toEqual([
      { gestureId: "g-1", name: "Raise arm" },
    ]);
    expect(getLatest().loadedGestures).toEqual([
      { gestureId: "g-2", name: "Squat" },
    ]);
  });

  it("supports explicit refresh requests", async () => {
    bridgeMocks.listSavedGestures
      .mockResolvedValueOnce([{ gestureId: "g-1", name: "Raise arm" }])
      .mockResolvedValueOnce([{ gestureId: "g-3", name: "Jump" }]);
    bridgeMocks.getLoadedSessionGestures
      .mockResolvedValueOnce([{ gestureId: "g-2", name: "Squat" }])
      .mockResolvedValueOnce([{ gestureId: "g-3", name: "Jump" }]);

    renderHook();
    await flushAsync();
    await flushAsync();

    expect(getLatest().availableGestures).toEqual([
      { gestureId: "g-1", name: "Raise arm" },
    ]);
    expect(getLatest().loadedGestures).toEqual([
      { gestureId: "g-2", name: "Squat" },
    ]);

    await act(async () => {
      await getLatest().refresh();
    });

    expect(getLatest().isLoading).toBe(false);
    expect(getLatest().availableGestures).toEqual([
      { gestureId: "g-3", name: "Jump" },
    ]);
    expect(getLatest().loadedGestures).toEqual([
      { gestureId: "g-3", name: "Jump" },
    ]);
    expect(bridgeMocks.listSavedGestures).toHaveBeenCalledTimes(2);
    expect(bridgeMocks.getLoadedSessionGestures).toHaveBeenCalledTimes(2);
  });

  it("ignores in-flight refresh completion after unmount", async () => {
    const availableDeferred = deferred<SavedGestureSummary[]>();
    const loadedDeferred = deferred<SavedGestureSummary[]>();
    bridgeMocks.listSavedGestures.mockReturnValueOnce(availableDeferred.promise);
    bridgeMocks.getLoadedSessionGestures.mockReturnValueOnce(
      loadedDeferred.promise,
    );

    renderHook();
    await flushAsync();

    const rendersBeforeUnmount = renderCount;
    act(() => {
      root.unmount();
    });

    await act(async () => {
      availableDeferred.resolve([{ gestureId: "g-4", name: "Lunge" }]);
      loadedDeferred.resolve([{ gestureId: "g-4", name: "Lunge" }]);
      await Promise.all([availableDeferred.promise, loadedDeferred.promise]);
    });
    await flushAsync();

    expect(renderCount).toBe(rendersBeforeUnmount);
  });
});

const AppStateHookConsumer = () => {
  useAppState();
  return null;
};

const ActiveProfileHookConsumer = () => {
  useActiveProfile();
  return null;
};

const expectHookProviderError = (
  RenderComponent: ComponentType,
  expectedMessage: string,
) => {
  const consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => {
    return undefined;
  });
  const container = document.createElement("div");
  const root = createRoot(container);

  try {
    expect(() => {
      act(() => {
        root.render(<RenderComponent />);
      });
    }).toThrowError(expectedMessage);
  } finally {
    act(() => {
      root.unmount();
    });
    consoleErrorSpy.mockRestore();
  }
};

describe("context hooks", () => {
  it("throws a clear error when useAppState is used outside AppStateProvider", () => {
    expectHookProviderError(
      () => <AppStateHookConsumer />,
      "useAppState must be used inside <AppStateProvider>",
    );
  });

  it("throws a clear error when useActiveProfile is used outside ActiveProfileProvider", () => {
    expectHookProviderError(
      () => <ActiveProfileHookConsumer />,
      "useActiveProfile must be used within an ActiveProfileProvider.",
    );
  });
});
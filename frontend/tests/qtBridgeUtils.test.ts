// @vitest-environment jsdom

import { afterEach, describe, expect, it, vi } from "vitest";

import {
  createBridgeResolver,
  invokeWithResult,
  isDesktopQtRuntime,
} from "@/services/qtBridgeUtils";
import {
  getQtWebChannel,
  resetQtWebChannelForTests,
} from "@/services/qtWebChannel";

describe("Qt bridge utilities", () => {
  afterEach(() => {
    resetQtWebChannelForTests();
    vi.unstubAllGlobals();
  });

  it("uses the first callback result only", async () => {
    await expect(
      invokeWithResult<number>((callback) => {
        callback(1);
        callback(2);
        return 3;
      }),
    ).resolves.toBe(1);
  });

  it("settles once when callback and Promise results race", async () => {
    await expect(
      invokeWithResult<string>((callback) => {
        callback("callback-first");
        return Promise.resolve("promise-second");
      }),
    ).resolves.toBe("callback-first");

    let lateCallback: ((value: string) => void) | undefined;
    const promiseFirst = invokeWithResult<string>((callback) => {
      lateCallback = callback;
      return Promise.resolve("promise-first");
    });

    await expect(promiseFirst).resolves.toBe("promise-first");
    lateCallback?.("callback-second");
    await expect(promiseFirst).resolves.toBe("promise-first");
  });

  it("supports Promise and synchronous return values", async () => {
    await expect(
      invokeWithResult(() => Promise.resolve("promise")),
    ).resolves.toBe("promise");
    await expect(invokeWithResult(() => "sync")).resolves.toBe("sync");
  });

  it("rejects thrown exceptions and rejected Promises", async () => {
    await expect(
      invokeWithResult(() => {
        throw new Error("thrown");
      }),
    ).rejects.toThrow("thrown");
    await expect(
      invokeWithResult(() => Promise.reject(new Error("rejected"))),
    ).rejects.toThrow("rejected");
  });

  it("resolves and caches a named bridge until reset", async () => {
    let channelCount = 0;
    vi.stubGlobal("qt", { webChannelTransport: {} });
    vi.stubGlobal(
      "QWebChannel",
      class {
        constructor(
          _transport: unknown,
          callback: (channel: { objects: Record<string, unknown> }) => void,
        ) {
          channelCount += 1;
          callback({ objects: { demoBridge: { ping: "pong" } } });
        }
      },
    );
    const resolver = createBridgeResolver<{ ping: string }>(
      "demoBridge",
      "missing demo bridge",
    );

    await expect(resolver.get()).resolves.toEqual({ ping: "pong" });
    await expect(resolver.get()).resolves.toEqual({ ping: "pong" });
    expect(channelCount).toBe(1);

    resolver.reset();
    resetQtWebChannelForTests();
    await expect(resolver.get()).resolves.toEqual({ ping: "pong" });
    expect(channelCount).toBe(2);
  });

  it("reports missing runtime and missing bridge objects", async () => {
    expect(isDesktopQtRuntime()).toBe(false);
    await expect(getQtWebChannel()).rejects.toThrow(
      "Qt WebChannel is unavailable.",
    );
    resetQtWebChannelForTests();

    vi.stubGlobal("qt", { webChannelTransport: {} });
    vi.stubGlobal(
      "QWebChannel",
      class {
        constructor(
          _transport: unknown,
          callback: (channel: { objects: Record<string, unknown> }) => void,
        ) {
          callback({ objects: {} });
        }
      },
    );
    const resolver = createBridgeResolver("missing", "bridge unavailable");

    await expect(resolver.get()).rejects.toThrow("bridge unavailable");
  });
});

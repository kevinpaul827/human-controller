import { getQtWebChannel } from "./qtWebChannel";

/** Qt-style signal exposed by QWebChannel objects. */
export type QtSignal<T> = {
  connect(callback: (payload: T) => void): void;
  disconnect?(callback: (payload: T) => void): void;
};

/**
 * Normalize callback, Promise, and synchronous Qt return styles.
 * The first result wins when a bridge uses more than one style.
 */
export const invokeWithResult = <T>(
  invoke: (callback: (result: T) => void) => unknown,
) =>
  new Promise<T>((resolve, reject) => {
    let settled = false;

    const resolveOnce = (result: T) => {
      if (settled) return;
      settled = true;
      resolve(result);
    };

    try {
      const returned = invoke(resolveOnce);
      if (
        returned != null &&
        typeof (returned as PromiseLike<T>).then === "function"
      ) {
        void Promise.resolve(returned as PromiseLike<T>).then(
          resolveOnce,
          (error: unknown) => {
            if (settled) return;
            settled = true;
            reject(error);
          },
        );
      } else if (returned !== undefined) {
        resolveOnce(returned as T);
      }
    } catch (error) {
      if (settled) return;
      settled = true;
      reject(error);
    }
  });

/** Lazily resolve and cache a named Qt WebChannel bridge object. */
export const createBridgeResolver = <T>(
  bridgeName: string,
  missingMessage: string,
) => {
  let bridgePromise: Promise<T> | null = null;

  const get = () => {
    bridgePromise ??= getQtWebChannel().then((channel) => {
      const bridge = channel.objects[bridgeName] as T | undefined;
      if (!bridge) throw new Error(missingMessage);
      return bridge;
    });
    return bridgePromise;
  };

  const reset = () => {
    bridgePromise = null;
  };

  return { get, reset };
};

export const isDesktopQtRuntime = () =>
  typeof window !== "undefined" &&
  Boolean(window.qt?.webChannelTransport && window.QWebChannel);

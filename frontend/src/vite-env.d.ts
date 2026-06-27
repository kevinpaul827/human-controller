/// <reference types="vite/client" />

/**
 * Global Qt WebChannel types injected by the PySide6 desktop runtime.
 * These declarations make the desktop bridge visible to TypeScript in the
 * Vite frontend without changing browser runtime behavior.
 */
type QtWebChannelObjects = Record<string, unknown>;

type QtWebChannelInstance = {
  objects: QtWebChannelObjects;
};

type QtWebChannelConstructor = new (
  transport: unknown,
  callback: (channel: QtWebChannelInstance) => void,
) => void;

interface Window {
  qt?: {
    webChannelTransport: unknown;
  };
  QWebChannel?: QtWebChannelConstructor;
}

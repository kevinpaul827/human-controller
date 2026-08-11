import { useEffect, useRef, useState } from "react";
import type { Dispatch, MutableRefObject, SetStateAction } from "react";

import { desktopStateBridge } from "@/services/desktopStateBridge";
import type { DesktopState } from "@/types/desktopState";
import { initialState, parseStoredState, STORAGE_KEY } from "./appStateModel";

export type PersistenceMode = "unknown" | "desktop" | "browser";

type PersistentDesktopState = {
  state: DesktopState;
  setState: Dispatch<SetStateAction<DesktopState>>;
  persistenceReady: boolean;
  persistenceMode: MutableRefObject<PersistenceMode>;
};

const loadBrowserState = (): DesktopState => {
  try {
    return parseStoredState(window.localStorage.getItem(STORAGE_KEY));
  } catch {
    return initialState();
  }
};

// Loads and saves desktop state with a simple fallback strategy.
// We try the desktop bridge first, then fall back to browser storage in preview mode if thats all we have.
export const usePersistentDesktopState = (): PersistentDesktopState => {
  const [state, setState] = useState<DesktopState>(loadBrowserState);
  const [persistenceReady, setPersistenceReady] = useState(false);
  const persistenceMode = useRef<PersistenceMode>("unknown");

  useEffect(() => {
    let active = true;
    void desktopStateBridge
      .getState()
      .then((desktopState) => {
        if (!active) return;
        persistenceMode.current = "desktop";
        setState(desktopState);
        setPersistenceReady(true);
      })
      .catch(() => {
        if (!active) return;
        persistenceMode.current = "browser";
        setPersistenceReady(true);
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (persistenceMode.current === "unknown") return;

    if (persistenceMode.current === "desktop") {
      const timer = window.setTimeout(() => {
        // Saving is best-effort: the in-memory state remains usable if the
        // desktop bridge disappears while the application is running.
        void desktopStateBridge.saveState(state).catch(() => {});
      }, 100);
      return () => window.clearTimeout(timer);
    }

    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch {
      // Browser preview mode must remain usable when storage is unavailable
      // (private browsing, quota exhaustion, or a disabled storage API).
    }
  }, [state]);

  return { state, setState, persistenceReady, persistenceMode };
};

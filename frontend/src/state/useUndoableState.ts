import { useCallback, useEffect, useRef, useState } from "react";
import type { Dispatch, SetStateAction } from "react";

import type { DesktopState } from "@/types/desktopState";

const UNDO_WINDOW_MS = 30_000;

export type ApplyWithUndo = (
  label: string,
  update: (current: DesktopState) => DesktopState,
) => void;

type UndoableState = {
  undoLabel: string | null;
  applyWithUndo: ApplyWithUndo;
  undo: () => void;
  dismissUndo: () => void;
};

/** Adds a single-level, time-limited undo operation to DesktopState updates. */
export const useUndoableState = (
  setState: Dispatch<SetStateAction<DesktopState>>,
): UndoableState => {
  const [undoLabel, setUndoLabel] = useState<string | null>(null);
  const undoSnapshot = useRef<DesktopState | null>(null);
  const undoTimer = useRef<number | null>(null);

  const clearUndoTimer = useCallback(() => {
    if (undoTimer.current !== null) {
      window.clearTimeout(undoTimer.current);
      undoTimer.current = null;
    }
  }, []);

  useEffect(() => clearUndoTimer, [clearUndoTimer]);

  const dismissUndo = useCallback(() => {
    clearUndoTimer();
    undoSnapshot.current = null;
    setUndoLabel(null);
  }, [clearUndoTimer]);

  const applyWithUndo = useCallback<ApplyWithUndo>(
    (label, update) => {
      setState((current) => {
        undoSnapshot.current = current;
        return update(current);
      });
      setUndoLabel(label);
      clearUndoTimer();
      undoTimer.current = window.setTimeout(dismissUndo, UNDO_WINDOW_MS);
    },
    [clearUndoTimer, dismissUndo, setState],
  );

  const undo = useCallback(() => {
    clearUndoTimer();
    if (undoSnapshot.current) {
      setState(undoSnapshot.current);
      undoSnapshot.current = null;
    }
    setUndoLabel(null);
  }, [clearUndoTimer, setState]);

  return { undoLabel, applyWithUndo, undo, dismissUndo };
};

import { useMemo } from "react";
import type { ReactNode } from "react";

import { AppStateContext } from "./appStateContext";
import { useAppStateActions } from "./useAppStateActions";
import { useAppStateView } from "./useAppStateView";
import { usePersistentDesktopState } from "./usePersistentDesktopState";
import { useUndoableState } from "./useUndoableState";

const AppStateProvider = ({ children }: { children: ReactNode }) => {
  const { state, setState, persistenceReady, persistenceMode } =
    usePersistentDesktopState();
  const { undoLabel, applyWithUndo, undo, dismissUndo } =
    useUndoableState(setState);
  const view = useAppStateView(state);
  const actions = useAppStateActions({
    state,
    setState,
    persistenceMode,
    applyWithUndo,
    undo,
    dismissUndo,
  });
  const value = useMemo(
    () => ({ ...view, undoLabel, ...actions }),
    [view, undoLabel, actions],
  );

  return (
    <AppStateContext.Provider value={value}>
      {persistenceReady ? children : null}
    </AppStateContext.Provider>
  );
};

export default AppStateProvider;

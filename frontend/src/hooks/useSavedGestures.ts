import { useCallback, useEffect, useState } from "react";
import calibrateBridge from "../services/calibrateBridge";
import type { SavedGestureSummary } from "../types/calibrate";

const useSavedGestures = () => {
  const [availableGestures, setAvailableGestures] = useState<
    SavedGestureSummary[]
  >([]);
  const [loadedGestures, setLoadedGestures] = useState<SavedGestureSummary[]>(
    [],
  );
  const [isLoading, setIsLoading] = useState(false);

  const refresh = useCallback(async () => {
    setIsLoading(true);

    try {
      const [available, loaded] = await Promise.all([
        calibrateBridge.listSavedGestures(),
        calibrateBridge.getLoadedSessionGestures(),
      ]);
      setAvailableGestures(available);
      setLoadedGestures(loaded);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadGesture = useCallback(async (gestureId: string) => {
    const result = await calibrateBridge.loadSavedGesture(gestureId);
    setLoadedGestures(result.loadedGestures);
    return result;
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return {
    availableGestures,
    loadedGestures,
    isLoading,
    loadGesture,
    refresh,
  };
};

export default useSavedGestures;

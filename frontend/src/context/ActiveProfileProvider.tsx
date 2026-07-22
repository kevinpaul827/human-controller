import { useMemo, useState, type ReactNode } from "react";
import ActiveProfileContext, {
  type ActiveProfile,
} from "./ActiveProfileContext";

type ActiveProfileProviderProps = {
  children: ReactNode;
};

const ActiveProfileProvider = ({ children }: ActiveProfileProviderProps) => {
  const [activeProfile, setActiveProfile] = useState<ActiveProfile | null>(
    null,
  );

  const value = useMemo(
    () => ({
      activeProfile,
      setActiveProfile,
      clearActiveProfile: () => setActiveProfile(null),
    }),
    [activeProfile],
  );

  return (
    <ActiveProfileContext.Provider value={value}>
      {children}
    </ActiveProfileContext.Provider>
  );
};

export default ActiveProfileProvider;

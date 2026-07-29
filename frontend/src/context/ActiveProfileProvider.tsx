import { useMemo, type ReactNode } from "react";
import { useAppState } from "../state/appStateContext";
import ActiveProfileContext, {
  type ActiveProfile,
} from "./ActiveProfileContext";

type ActiveProfileProviderProps = {
  children: ReactNode;
};

const ActiveProfileProvider = ({ children }: ActiveProfileProviderProps) => {
  const { selectedPatient, selectPatient, clearPatientSelection } =
    useAppState();
  const value = useMemo(
    () => ({
      activeProfile: selectedPatient,
      setActiveProfile: (profile: ActiveProfile) =>
        selectPatient(profile.patientId),
      clearActiveProfile: clearPatientSelection,
    }),
    [selectedPatient, selectPatient, clearPatientSelection],
  );

  return (
    <ActiveProfileContext.Provider value={value}>
      {children}
    </ActiveProfileContext.Provider>
  );
};

export default ActiveProfileProvider;

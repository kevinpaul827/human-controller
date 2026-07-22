import { createContext } from "react";
import type { PatientProfile } from "../types/profile";

export type ActiveProfile = Pick<PatientProfile, "patientId" | "patientName">;

export type ActiveProfileContextValue = {
  activeProfile: ActiveProfile | null;
  setActiveProfile: (profile: ActiveProfile) => void;
  clearActiveProfile: () => void;
};

const ActiveProfileContext = createContext<
  ActiveProfileContextValue | undefined
>(undefined);

export default ActiveProfileContext;

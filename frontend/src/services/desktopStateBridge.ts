import {
  createBridgeResolver,
  invokeWithResult,
  isDesktopQtRuntime,
} from "./qtBridgeUtils";
import type {
  DesktopState,
  PoseModel,
  PoseModelRecommendation,
} from "@/types/desktopState";

type QtStateBridge = {
  getState: (
    callback?: (state: DesktopState) => void,
  ) => DesktopState | Promise<DesktopState> | void;
  recommendPoseModel: (
    callback?: (result: PoseModelRecommendation) => void,
  ) => PoseModelRecommendation | Promise<PoseModelRecommendation> | void;
  saveState: (
    state: DesktopState,
    callback?: (result: DesktopState) => void,
  ) => DesktopState | Promise<DesktopState> | void;
  selectPatient: (
    patientId: string,
    callback?: (state: DesktopState) => void,
  ) => DesktopState | Promise<DesktopState> | void;
  createProfile: (
    patientName: string,
    notes: string,
    callback?: (state: DesktopState) => void,
  ) => DesktopState | Promise<DesktopState> | void;
  deleteProfile: (
    patientId: string,
    callback?: (state: DesktopState) => void,
  ) => DesktopState | Promise<DesktopState> | void;
  clearPatientSelection: (
    callback?: (state: DesktopState) => void,
  ) => DesktopState | Promise<DesktopState> | void;
  deleteGesture: (
    gestureId: string,
    callback?: (state: DesktopState) => void,
  ) => DesktopState | Promise<DesktopState> | void;
};

type NavigatorWithMemory = Navigator & {
  deviceMemory?: number;
};

const stateBridgeResolver = createBridgeResolver<QtStateBridge>(
  "stateBridge",
  "Desktop state bridge is unavailable.",
);

const browserPoseModelRecommendation = (): PoseModelRecommendation => {
  const detectedLogicalCpus = navigator.hardwareConcurrency;
  const logicalCpuCount =
    Number.isFinite(detectedLogicalCpus) && detectedLogicalCpus > 0
      ? Math.floor(detectedLogicalCpus)
      : null;
  const ram = (navigator as NavigatorWithMemory).deviceMemory;
  const ramGb =
    typeof ram === "number" && Number.isFinite(ram) && ram > 0 ? ram : null;
  const physicalCpuCount = null;
  let poseModel: PoseModel = "lite";
  if (
    ramGb !== null &&
    logicalCpuCount !== null &&
    ramGb >= 15 &&
    logicalCpuCount >= 12
  ) {
    poseModel = "heavy";
  } else if (
    ramGb !== null &&
    logicalCpuCount !== null &&
    ramGb >= 7 &&
    logicalCpuCount >= 6
  ) {
    poseModel = "full";
  }
  return {
    poseModel,
    ramGb,
    physicalCpuCount,
    logicalCpuCount,
  };
};

/** Promise-based wrapper around the desktop state bridge. */
export const desktopStateBridge = {
  async getState() {
    const bridge = await stateBridgeResolver.get();
    return invokeWithResult<DesktopState>((callback) =>
      bridge.getState(callback),
    );
  },
  async recommendPoseModel() {
    if (!isDesktopQtRuntime()) {
      return browserPoseModelRecommendation();
    }
    const bridge = await stateBridgeResolver.get();
    return invokeWithResult<PoseModelRecommendation>((callback) =>
      bridge.recommendPoseModel(callback),
    );
  },
  async saveState(state: DesktopState) {
    const bridge = await stateBridgeResolver.get();
    return invokeWithResult<DesktopState>((callback) =>
      bridge.saveState(state, callback),
    );
  },
  async selectPatient(patientId: string) {
    const bridge = await stateBridgeResolver.get();
    return invokeWithResult<DesktopState>((callback) =>
      bridge.selectPatient(patientId, callback),
    );
  },
  async createProfile(patientName: string, notes = "") {
    const bridge = await stateBridgeResolver.get();
    return invokeWithResult<DesktopState>((callback) =>
      bridge.createProfile(patientName, notes, callback),
    );
  },
  async deleteProfile(patientId: string) {
    const bridge = await stateBridgeResolver.get();
    return invokeWithResult<DesktopState>((callback) =>
      bridge.deleteProfile(patientId, callback),
    );
  },
  async clearPatientSelection() {
    const bridge = await stateBridgeResolver.get();
    return invokeWithResult<DesktopState>((callback) =>
      bridge.clearPatientSelection(callback),
    );
  },
  async deleteGesture(gestureId: string) {
    const bridge = await stateBridgeResolver.get();
    return invokeWithResult<DesktopState>((callback) =>
      bridge.deleteGesture(gestureId, callback),
    );
  },
};

/** @internal Reset cached bridge state between isolated tests. */
export const resetDesktopStateBridgeForTests = () => {
  stateBridgeResolver.reset();
};

import { getQtWebChannel } from "./qtWebChannel";
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

let bridgePromise: Promise<QtStateBridge> | null = null;

const getBridge = () => {
  bridgePromise ??= getQtWebChannel().then((channel) => {
    const bridge = channel.objects.stateBridge as QtStateBridge | undefined;
    if (!bridge) throw new Error("Desktop state bridge is unavailable.");
    return bridge;
  });
  return bridgePromise;
};

const invokeWithResult = <T>(
  invoke: (callback: (result: T) => void) => unknown,
) =>
  new Promise<T>((resolve, reject) => {
    let settled = false;
    const settle = (result: T) => {
      if (settled) return;
      settled = true;
      resolve(result);
    };
    try {
      const maybePromise = invoke(settle);
      if (
        maybePromise != null &&
        typeof (maybePromise as PromiseLike<T>).then === "function"
      ) {
        void Promise.resolve(maybePromise as PromiseLike<T>).then(
          settle,
          (error: unknown) => {
            if (settled) return;
            settled = true;
            reject(error);
          },
        );
      } else if (maybePromise !== undefined) {
        settle(maybePromise as T);
      }
    } catch (error) {
      if (!settled) {
        settled = true;
        reject(error);
      }
    }
  });

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

const isDesktopRuntime = () =>
  Boolean(window.qt?.webChannelTransport && window.QWebChannel);

export const desktopStateBridge = {
  async getState() {
    const bridge = await getBridge();
    return invokeWithResult<DesktopState>((callback) =>
      bridge.getState(callback),
    );
  },
  async recommendPoseModel() {
    if (!isDesktopRuntime()) {
      return browserPoseModelRecommendation();
    }
    const bridge = await getBridge();
    return invokeWithResult<PoseModelRecommendation>((callback) =>
      bridge.recommendPoseModel(callback),
    );
  },
  async saveState(state: DesktopState) {
    const bridge = await getBridge();
    return invokeWithResult<DesktopState>((callback) =>
      bridge.saveState(state, callback),
    );
  },
  async selectPatient(patientId: string) {
    const bridge = await getBridge();
    return invokeWithResult<DesktopState>((callback) =>
      bridge.selectPatient(patientId, callback),
    );
  },
  async createProfile(patientName: string, notes = "") {
    const bridge = await getBridge();
    return invokeWithResult<DesktopState>((callback) =>
      bridge.createProfile(patientName, notes, callback),
    );
  },
  async deleteProfile(patientId: string) {
    const bridge = await getBridge();
    return invokeWithResult<DesktopState>((callback) =>
      bridge.deleteProfile(patientId, callback),
    );
  },
  async clearPatientSelection() {
    const bridge = await getBridge();
    return invokeWithResult<DesktopState>((callback) =>
      bridge.clearPatientSelection(callback),
    );
  },
  async deleteGesture(gestureId: string) {
    const bridge = await getBridge();
    return invokeWithResult<DesktopState>((callback) =>
      bridge.deleteGesture(gestureId, callback),
    );
  },
};

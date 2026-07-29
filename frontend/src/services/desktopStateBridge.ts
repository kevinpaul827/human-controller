import { getQtWebChannel } from "./qtWebChannel";
import type { DesktopState } from "@/types/desktopState";

type QtStateBridge = {
  getState: (
    callback?: (state: DesktopState) => void,
  ) => DesktopState | Promise<DesktopState> | void;
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

export const desktopStateBridge = {
  async getState() {
    const bridge = await getBridge();
    return invokeWithResult<DesktopState>((callback) =>
      bridge.getState(callback),
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

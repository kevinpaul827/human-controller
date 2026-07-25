import { getQtWebChannel } from "./qtWebChannel";
import type { DesktopState } from "@/types/desktopState";

type QtStateBridge = {
  getState: () => DesktopState | Promise<DesktopState>;
  saveState: (state: DesktopState) => DesktopState | Promise<DesktopState>;
  selectPatient: (patientId: string) => DesktopState | Promise<DesktopState>;
  createProfile: (patientName: string) => DesktopState | Promise<DesktopState>;
  deleteGesture: (gestureId: string) => boolean | Promise<boolean>;
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

export const desktopStateBridge = {
  async getState() {
    return await (await getBridge()).getState();
  },
  async saveState(state: DesktopState) {
    return await (await getBridge()).saveState(state);
  },
  async selectPatient(patientId: string) {
    return await (await getBridge()).selectPatient(patientId);
  },
  async createProfile(patientName: string) {
    return await (await getBridge()).createProfile(patientName);
  },
  async deleteGesture(gestureId: string) {
    return await (await getBridge()).deleteGesture(gestureId);
  },
};

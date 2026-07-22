import type { GestureSummary, PatientProfile } from "../types/profile";
import { getQtWebChannel } from "./qtWebChannel";

type BridgeCallback = (response: string) => void;

type QtProfileBridgeObject = {
  listProfiles: (callback: BridgeCallback) => void;
  listGestures: (callback: BridgeCallback) => void;
  createProfile: (
    patientName: string,
    notes: string,
    callback: BridgeCallback,
  ) => void;
  deleteProfile: (patientId: string, callback: BridgeCallback) => void;
  setKeyBinding: (
    patientId: string,
    gestureId: string,
    key: string,
    callback: BridgeCallback,
  ) => void;
  removeKeyBinding: (
    patientId: string,
    gestureId: string,
    callback: BridgeCallback,
  ) => void;
};

type BridgeResponse<T> = {
  ok: boolean;
  data?: T;
  error?: string;
};

const BRIDGE_NAME = "profileBridge";
const BRIDGE_ERROR = "Qt WebChannel profile bridge is unavailable.";

let bridgePromise: Promise<QtProfileBridgeObject> | null = null;

export const isProfileDesktopRuntime = () =>
  Boolean(window.qt?.webChannelTransport && window.QWebChannel);

const getProfileBridgeOrThrow = () => {
  bridgePromise ??= getQtWebChannel().then((channel) => {
    const bridge = channel.objects[BRIDGE_NAME] as
      | QtProfileBridgeObject
      | undefined;
    if (!bridge) {
      throw new Error(BRIDGE_ERROR);
    }
    return bridge;
  });
  return bridgePromise;
};

const parseResponse = <T>(response: string) => {
  const payload = JSON.parse(response) as BridgeResponse<T>;
  if (!payload.ok || payload.data === undefined) {
    throw new Error(payload.error || "The profile operation failed.");
  }
  return payload.data;
};

const callBridge = async <T>(
  invoke: (bridge: QtProfileBridgeObject, callback: BridgeCallback) => void,
) => {
  const bridge = await getProfileBridgeOrThrow();
  return new Promise<T>((resolve, reject) => {
    try {
      invoke(bridge, (response) => {
        try {
          resolve(parseResponse<T>(response));
        } catch (error) {
          reject(error);
        }
      });
    } catch (error) {
      reject(error);
    }
  });
};

const profileBridge = {
  listProfiles: () =>
    callBridge<PatientProfile[]>((bridge, callback) =>
      bridge.listProfiles(callback),
    ),

  listGestures: () =>
    callBridge<GestureSummary[]>((bridge, callback) =>
      bridge.listGestures(callback),
    ),

  createProfile: (patientName: string, notes: string) =>
    callBridge<PatientProfile>((bridge, callback) =>
      bridge.createProfile(patientName, notes, callback),
    ),

  deleteProfile: (patientId: string) =>
    callBridge<string>((bridge, callback) =>
      bridge.deleteProfile(patientId, callback),
    ),

  setKeyBinding: (patientId: string, gestureId: string, key: string) =>
    callBridge<PatientProfile>((bridge, callback) =>
      bridge.setKeyBinding(patientId, gestureId, key, callback),
    ),

  removeKeyBinding: (patientId: string, gestureId: string) =>
    callBridge<PatientProfile>((bridge, callback) =>
      bridge.removeKeyBinding(patientId, gestureId, callback),
    ),
};

export default profileBridge;

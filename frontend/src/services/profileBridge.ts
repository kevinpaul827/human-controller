import type { GestureSummary, PatientProfile } from "../types/profile";
import {
  createBridgeResolver,
  invokeWithResult,
  isDesktopQtRuntime,
} from "./qtBridgeUtils";

type BridgeCallback = (response: string) => void;

type BridgeResult = string | Promise<string> | void;

type QtProfileBridgeObject = {
  listProfiles: (callback?: BridgeCallback) => BridgeResult;
  listGestures: (callback?: BridgeCallback) => BridgeResult;
  createProfile: (
    patientName: string,
    notes: string,
    callback?: BridgeCallback,
  ) => BridgeResult;
  deleteProfile: (patientId: string, callback?: BridgeCallback) => BridgeResult;
  setKeyBinding: (
    patientId: string,
    gestureId: string,
    key: string,
    callback?: BridgeCallback,
  ) => BridgeResult;
  removeKeyBinding: (
    patientId: string,
    gestureId: string,
    callback?: BridgeCallback,
  ) => BridgeResult;
};

type BridgeResponse<T> = {
  ok: boolean;
  data?: T;
  error?: string;
};

const BRIDGE_ERROR = "Qt WebChannel profile bridge is unavailable.";

const profileBridgeResolver = createBridgeResolver<QtProfileBridgeObject>(
  "profileBridge",
  BRIDGE_ERROR,
);

export const isProfileDesktopRuntime = () => isDesktopQtRuntime();

const parseResponse = <T>(response: string) => {
  const payload = JSON.parse(response) as BridgeResponse<T>;
  if (!payload.ok || payload.data === undefined) {
    throw new Error(payload.error || "The profile operation failed.");
  }
  return payload.data;
};

const callBridge = async <T>(
  invoke: (
    bridge: QtProfileBridgeObject,
    callback: BridgeCallback,
  ) => BridgeResult,
) => {
  const bridge = await profileBridgeResolver.get();
  const response = await invokeWithResult<string>((callback) =>
    invoke(bridge, callback),
  );
  return parseResponse<T>(response);
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

/** @internal Reset cached bridge state between isolated tests. */
export const resetProfileBridgeForTests = () => {
  profileBridgeResolver.reset();
};

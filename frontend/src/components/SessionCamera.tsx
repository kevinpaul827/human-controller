import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Crosshair, PictureInPicture2, Play, Square } from "lucide-react";
import SessionCameraErrorModal from "./modals/SessionCameraErrorModal";
import { BrutalButton } from "@/components/ui/brutal-button";
import { BrutalBadge } from "@/components/ui/brutal-badge";
import useActiveProfile from "@/hooks/useActiveProfile";
import useDesktopCameraPreview from "@/hooks/useDesktopCameraPreview";
import {
  BrutalCard,
  BrutalCardContent,
  BrutalCardFooter,
  BrutalCardHeader,
  BrutalCardTitle,
} from "@/components/ui/brutal-card";
import { useAppState } from "@/state/appStateContext";
import sessionBridge from "../services/sessionBridge";
import type {
  GestureMatchEvent,
  SessionStatusEvent,
  SessionState,
} from "../types/session";
import { ROUTES } from "@/utils/constants";

const SessionCamera = () => {
  const navigate = useNavigate();
  const { activeProfile } = useActiveProfile();
  const { bindings } = useAppState();
  const [sessionState, setSessionState] = useState<SessionState>("idle");
  const [errorEvent, setErrorEvent] = useState<SessionStatusEvent | null>(null);
  const [profileWarning, setProfileWarning] = useState<string | null>(null);
  const [latestMatch, setLatestMatch] = useState<GestureMatchEvent | null>(
    null,
  );
  const [starting, setStarting] = useState(false);
  const isLive = sessionState === "live";
  const needsCalibration =
    !activeProfile ||
    !bindings.some((binding) => Boolean(binding.gesture.calibratedAt));
  const { elapsed, setElapsed } = useDesktopCameraPreview({
    bridge: sessionBridge,
    isLive,
  });

  useEffect(() => {
    const unsubscribe = sessionBridge.onSessionStatus((event) => {
      setStarting(false);
      if (event.state === "error") {
        setElapsed(0);
        setLatestMatch(null);
        setSessionState("idle");
        setErrorEvent(event);
        return;
      }

      if (event.state === "idle") {
        setElapsed(0);
        setLatestMatch(null);
      }
      setErrorEvent(null);
      setSessionState(event.state);
    });

    return unsubscribe;
  }, [setElapsed]);

  useEffect(
    () =>
      sessionBridge.onGestureMatch((event) => {
        setLatestMatch((current) => {
          if (event.keyAction === "release" || !event.matched) return null;
          if (
            current?.keyAction === "press" &&
            current.gestureId === event.gestureId
          ) {
            return {
              ...event,
              triggered: true,
              key: current.key,
              keyAction: "press",
            };
          }
          return event;
        });
        if (event.injectionError) {
          setErrorEvent({
            state: "error",
            message: event.injectionError,
            settingsTarget: "accessibility",
          });
        }
      }),
    [],
  );

  useEffect(() => {
    setStarting(false);
    setLatestMatch(null);
    setProfileWarning(null);
  }, [activeProfile?.patientId]);

  const handleStartSession = async () => {
    setErrorEvent(null);
    setElapsed(0);
    setStarting(true);
    try {
      if (activeProfile) {
        const profileData = await sessionBridge.loadProfile(
          activeProfile.patientId,
        );
        if (profileData.gestures.length === 0) {
          setProfileWarning(
            "This profile has no usable movement key bindings. Please add key bindings or calibrate new gestures.",
          );
        } else if (profileData.missingGestureIds.length > 0) {
          setProfileWarning(
            `${profileData.missingGestureIds.length} bound movement ${profileData.missingGestureIds.length === 1 ? "file is" : "files are"} missing; re-record ${profileData.missingGestureIds.length === 1 ? "it" : "them"} in Library.`,
          );
        } else {
          setProfileWarning(null);
        }
      } else {
        setProfileWarning(null);
      }
      await sessionBridge.startSession();
    } catch (error) {
      setStarting(false);
      setSessionState("error");
      setErrorEvent({
        state: "error",
        message:
          error instanceof Error
            ? error.message
            : "Unable to reach the desktop session bridge.",
      });
    }
  };

  const handleStopSession = async () => {
    try {
      setElapsed(0);
      await sessionBridge.stopSession();
      setSessionState("idle");
      setLatestMatch(null);
      return true;
    } catch (error) {
      setSessionState("error");
      setErrorEvent({
        state: "error",
        message:
          error instanceof Error
            ? error.message
            : "Unable to stop the desktop-managed session.",
      });
      return false;
    }
  };

  const handleConfigure = async () => {
    try {
      if (errorEvent?.settingsTarget === "accessibility") {
        await sessionBridge.openAccessibilitySettings();
      } else {
        await sessionBridge.openCameraSettings();
      }
    } catch (error) {
      setErrorEvent({
        state: "error",
        message:
          error instanceof Error
            ? error.message
            : "Unable to open desktop camera settings.",
      });
    }
  };

  const handleCloseError = async () => {
    if (await handleStopSession()) {
      setErrorEvent(null);
    }
  };

  return (
    <>
      <BrutalCard className="self-start overflow-hidden">
        <BrutalCardHeader>
          <BrutalCardTitle>Session controls</BrutalCardTitle>
          {isLive ? (
            <BrutalBadge tone="destructive" dot>
              REC {elapsed.toFixed(1)}s
            </BrutalBadge>
          ) : starting ? (
            <BrutalBadge dot>Starting</BrutalBadge>
          ) : (
            <BrutalBadge>Idle</BrutalBadge>
          )}
        </BrutalCardHeader>

        <BrutalCardContent className="flex items-start gap-4">
          <PictureInPicture2
            className="mt-1 size-7 shrink-0"
            aria-hidden="true"
          />
          <div className="space-y-1">
            <p className="font-bold">
              {isLive ? "Game overlay running" : "Ready to start"}
            </p>
            <p className="text-sm font-semibold text-muted-foreground">
              {isLive
                ? "Switch to your game; the separate camera window stays on top."
                : "Starting the session opens the separate camera overlay."}
            </p>
          </div>
        </BrutalCardContent>

        <BrutalCardFooter className="flex-col items-stretch gap-3">
          <span className="min-w-0 text-sm font-bold text-muted-foreground">
            {latestMatch?.triggered
              ? `${latestMatch.name ?? "Movement"} → ${latestMatch.key} held`
              : latestMatch
                ? `Recognising ${latestMatch.name ?? "movement"}…`
                : profileWarning
                  ? profileWarning
                  : needsCalibration && !isLive
                    ? activeProfile
                      ? "This profile has no usable movement key bindings. Please add key bindings or calibrate new gestures."
                      : "No patient selected. Add a binding, go to calibration, or choose a profile."
                    : isLive
                      ? "Waiting for a movement"
                      : ""}
          </span>
          <div className="flex flex-col gap-2">
            {isLive ? (
              <BrutalButton
                variant="destructive"
                size="md"
                className="w-full"
                onClick={handleStopSession}
              >
                <Square aria-hidden="true" />
                Stop session
              </BrutalButton>
            ) : (
              <>
                <BrutalButton
                  variant="primary"
                  size="md"
                  className="w-full"
                  disabled={needsCalibration || starting}
                  onClick={handleStartSession}
                >
                  <Play aria-hidden="true" />
                  {starting ? "Starting…" : "Start session"}
                </BrutalButton>
                <BrutalButton
                  variant="outline"
                  size="md"
                  className="w-full"
                  onClick={() => navigate(ROUTES.calibrate)}
                >
                  <Crosshair aria-hidden="true" />
                  Go to calibration
                </BrutalButton>
              </>
            )}
          </div>
        </BrutalCardFooter>
      </BrutalCard>

      <SessionCameraErrorModal
        open={errorEvent !== null}
        kind={errorEvent?.settingsTarget}
        message={errorEvent?.message}
        onCancel={handleCloseError}
        onConfigure={handleConfigure}
      />
    </>
  );
};

export default SessionCamera;

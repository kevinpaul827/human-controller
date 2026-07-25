import { useEffect, useState } from "react";
import { PictureInPicture2, Play, Square } from "lucide-react";
import SessionCameraErrorModal from "./modals/SessionCameraErrorModal";
import { BrutalButton } from "@/components/ui/brutal-button";
import { BrutalBadge } from "@/components/ui/brutal-badge";
import {
  BrutalCard,
  BrutalCardContent,
  BrutalCardFooter,
  BrutalCardHeader,
  BrutalCardTitle,
} from "@/components/ui/brutal-card";
import sessionBridge from "../services/sessionBridge";
import type {
  GestureMatchEvent,
  SessionStatusEvent,
  SessionState,
} from "../types/session";

const SessionCamera = () => {
  const [sessionState, setSessionState] = useState<SessionState>("idle");
  const [elapsed, setElapsed] = useState(0);
  const [errorEvent, setErrorEvent] = useState<SessionStatusEvent | null>(null);
  const [latestMatch, setLatestMatch] = useState<GestureMatchEvent | null>(
    null,
  );
  const [overlayVisible, setOverlayVisible] = useState(false);
  const isLive = sessionState === "live";

  useEffect(() => {
    if (!isLive) {
      return;
    }

    const intervalId = window.setInterval(() => {
      setElapsed((current) => Number((current + 0.1).toFixed(1)));
    }, 100);

    return () => window.clearInterval(intervalId);
  }, [isLive]);

  useEffect(() => {
    const unsubscribe = sessionBridge.onSessionStatus((event) => {
      if (event.state === "error") {
        setElapsed(0);
        setSessionState("idle");
        setErrorEvent(event);
        return;
      }

      if (event.state === "idle") {
        setElapsed(0);
      }
      setErrorEvent(null);
      setSessionState(event.state);
    });

    return unsubscribe;
  }, []);

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

  useEffect(() => sessionBridge.onOverlayVisibility(setOverlayVisible), []);

  const handleStartSession = async () => {
    setErrorEvent(null);
    setElapsed(0);
    try {
      await sessionBridge.startSession();
      setSessionState("live");
    } catch (error) {
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
    } catch (error) {
      setSessionState("error");
      setErrorEvent({
        state: "error",
        message:
          error instanceof Error
            ? error.message
            : "Unable to stop the desktop-managed session.",
      });
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

  const handleToggleOverlay = async () => {
    try {
      await sessionBridge.setOverlayVisible(!overlayVisible);
    } catch (error) {
      setErrorEvent({
        state: "error",
        message:
          error instanceof Error
            ? error.message
            : "Unable to change the desktop game overlay.",
      });
    }
  };

  const handleCloseError = async () => {
    try {
      await handleStopSession();
    } finally {
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

        <BrutalCardFooter className="flex-wrap justify-between gap-3">
          <span className="min-w-0 flex-1 text-sm font-bold text-muted-foreground">
            {latestMatch?.triggered
              ? `${latestMatch.name ?? "Movement"} → ${latestMatch.key} held`
              : latestMatch
                ? `Recognising ${latestMatch.name ?? "movement"}…`
                : isLive
                  ? "Waiting for a movement"
                  : ""}
          </span>
          <div className="flex shrink-0 gap-2">
            {isLive ? (
              <BrutalButton
                variant="outline"
                size="lg"
                onClick={handleToggleOverlay}
                aria-pressed={overlayVisible}
              >
                <PictureInPicture2 aria-hidden="true" />
                {overlayVisible ? "Hide overlay" : "Show overlay"}
              </BrutalButton>
            ) : null}
            <BrutalButton
              variant={isLive ? "destructive" : "primary"}
              size="lg"
              onClick={isLive ? handleStopSession : handleStartSession}
            >
              {isLive ? (
                <>
                  <Square aria-hidden="true" />
                  Stop session
                </>
              ) : (
                <>
                  <Play aria-hidden="true" />
                  Start session
                </>
              )}
            </BrutalButton>
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

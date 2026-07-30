import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  Circle,
  RotateCcw,
  Square,
} from "lucide-react";
import Page from "@/components/Page";
import { BrutalButton } from "@/components/ui/brutal-button";
import { BrutalBadge } from "@/components/ui/brutal-badge";
import {
  BrutalCard,
  BrutalCardContent,
  BrutalCardFooter,
  BrutalCardHeader,
  BrutalCardTitle,
} from "@/components/ui/brutal-card";
import { BrutalField, BrutalInput } from "@/components/ui/brutal-input";
import { StepProgress } from "@/components/ui/step-progress";
import { useAppState } from "@/state/appStateContext";
import useActiveProfile from "@/hooks/useActiveProfile";
import useDesktopCameraPreview from "@/hooks/useDesktopCameraPreview";
import calibrateBridge from "@/services/calibrateBridge";
import type { CapturePhase } from "@/types/calibrate";
import { ROUTES } from "@/utils/constants";

const STEP_LABELS = ["Name it", "Record it", "Save it"] as const;

const Calibrate = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { activeProfile } = useActiveProfile();
  const { gestures, addGesture, completeRecording } = useAppState();
  const requestedId = searchParams.get("gesture");
  const existing = gestures.find(
    (gesture) => gesture.gestureId === requestedId,
  );

  const [gestureId, setGestureId] = useState<string | null>(
    requestedId ?? null,
  );
  const [name, setName] = useState(existing?.name ?? "");
  const [step, setStep] = useState(existing ? 2 : 1);
  const [cameraLive, setCameraLive] = useState(false);
  const [recording, setRecording] = useState(false);
  const [capturePhase, setCapturePhase] = useState<CapturePhase>("idle");
  const [countdownRemaining, setCountdownRemaining] = useState(0);
  const [recordingDuration, setRecordingDuration] = useState("10");
  const [repCount, setRepCount] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const { previewAspectRatio, previewViewportRef: previewRef } =
    useDesktopCameraPreview({
      bridge: calibrateBridge,
      isLive: step === 2,
      trackElapsed: false,
    });
  const displayName = name.trim() || existing?.name || "New movement";
  const recordingSeconds = Number(recordingDuration);
  const recordingDurationValid =
    Number.isFinite(recordingSeconds) &&
    recordingSeconds >= 1 &&
    recordingSeconds <= 60;

  useEffect(() => {
    const offStatus = calibrateBridge.onCalibrateStatus((event) => {
      setCameraLive(event.state === "live");
      if (event.state === "error")
        setError(event.message ?? "Unable to start the camera.");
    });
    const offUpdate = calibrateBridge.onCalibrationUpdated((event) => {
      setRepCount(event.repCount);
      setRecording(event.capturing);
      setCapturePhase(event.phase);
      setCountdownRemaining(event.countdownRemaining);
    });
    return () => {
      offStatus();
      offUpdate();
    };
  }, []);

  useEffect(() => {
    if (step !== 2) return;
    let active = true;
    setError(null);
    void calibrateBridge
      .startCalibrate()
      .then(() => (active ? calibrateBridge.startCalibration() : undefined))
      .catch((cause: unknown) => {
        if (active)
          setError(
            cause instanceof Error
              ? cause.message
              : "Unable to start calibration.",
          );
      });
    return () => {
      active = false;
      void calibrateBridge.stopCalibrate().catch(() => {});
    };
  }, [step]);

  const beginRecording = () => {
    let id = gestureId;
    if (!id) {
      id = addGesture(name.trim());
      setGestureId(id);
    }
    setStep(2);
  };

  const toggleRecording = async () => {
    setError(null);
    try {
      if (recording) {
        await calibrateBridge.cancelRep();
      } else {
        await calibrateBridge.startRep(recordingSeconds);
      }
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to change the recording state.",
      );
    }
  };

  const reset = async () => {
    setError(null);
    try {
      await calibrateBridge.resetRep();
      setRepCount(0);
      setRecording(false);
      setCapturePhase("idle");
      setCountdownRemaining(0);
      setStep(2);
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to reset this recording.",
      );
    }
  };

  const save = async () => {
    if (!gestureId) return;
    setSaving(true);
    setError(null);
    try {
      const result = await calibrateBridge.saveRep(displayName, gestureId);
      completeRecording(gestureId, result);
      navigate(ROUTES.library);
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to save this movement.",
      );
    } finally {
      setSaving(false);
    }
  };

  const captureMessage = (() => {
    if (capturePhase === "countdown") {
      return {
        title: `Get ready — ${countdownRemaining}`,
        detail: "Hold the starting pose while the app learns it.",
      };
    }
    if (capturePhase === "waiting") {
      return {
        title: "Ready — move now",
        detail:
          "Begin the movement. Recording starts automatically when you move.",
      };
    }
    if (capturePhase === "recording") {
      return {
        title: `Movement detected — ${countdownRemaining}`,
        detail:
          "Finish the movement and hold the final pose. Recording will stop automatically.",
      };
    }
    if (capturePhase === "captured") {
      return {
        title: "Movement captured",
        detail: "Record another variation or continue to review.",
      };
    }
    return {
      title: "Ready to record",
      detail: "Press Start recording when you are ready.",
    };
  })();

  return (
    <Page>
      <header className="flex shrink-0 flex-col gap-4">
        <div>
          <h1 className="text-2xl text-balance sm:text-3xl">
            {!existing ? "Record a movement" : `Record “${existing.name}”`}
          </h1>
          <p className="mt-1 text-sm font-semibold text-muted-foreground">
            {activeProfile
              ? `Calibrating for ${activeProfile.patientName}`
              : "No profile selected"}
          </p>
        </div>
        <StepProgress steps={STEP_LABELS} currentStep={step} />
      </header>

      {error ? (
        <p className="rounded-base border-2 border-destructive bg-surface px-4 py-3 text-sm font-bold text-destructive">
          {error}
        </p>
      ) : null}

      {step === 1 ? (
        <BrutalCard className="max-w-xl">
          <BrutalCardHeader>
            <BrutalCardTitle>What is this movement called?</BrutalCardTitle>
          </BrutalCardHeader>
          <BrutalCardContent>
            <BrutalField label="Movement name" htmlFor="gesture-name">
              <BrutalInput
                id="gesture-name"
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="e.g. Right Arm Raise"
                autoFocus
              />
            </BrutalField>
          </BrutalCardContent>
          <BrutalCardFooter className="justify-between">
            <BrutalButton
              variant="outline"
              onClick={() => navigate(ROUTES.library)}
            >
              <ArrowLeft />
              Back
            </BrutalButton>
            <BrutalButton onClick={beginRecording} disabled={!name.trim()}>
              Next
              <ArrowRight />
            </BrutalButton>
          </BrutalCardFooter>
        </BrutalCard>
      ) : null}

      {step === 2 ? (
        <div className="grid items-start gap-5 lg:grid-cols-[minmax(0,1.4fr)_minmax(20rem,1fr)]">
          <BrutalCard className="overflow-hidden">
            <BrutalCardHeader>
              <BrutalCardTitle>
                {cameraLive ? "Camera ready" : "Starting camera…"}
              </BrutalCardTitle>
              <BrutalBadge
                tone={
                  capturePhase === "recording"
                    ? "destructive"
                    : cameraLive
                      ? "success"
                      : "neutral"
                }
                dot={capturePhase === "recording"}
              >
                {recording
                  ? captureMessage.title
                  : cameraLive
                    ? "Camera on"
                    : "Camera off"}
              </BrutalBadge>
            </BrutalCardHeader>
            <div className="flex min-h-80 items-center justify-center bg-stage p-4">
              <div
                ref={previewRef}
                style={{ aspectRatio: String(previewAspectRatio) }}
                className="w-full max-w-full border border-stage-muted bg-stage"
              />
            </div>
          </BrutalCard>
          <BrutalCard>
            <BrutalCardHeader>
              <BrutalCardTitle>{displayName}</BrutalCardTitle>
              <BrutalBadge>{repCount} captured</BrutalBadge>
            </BrutalCardHeader>
            <BrutalCardContent>
              <div className="mb-6 rounded-sm border border-hairline bg-surface-muted p-5 text-center">
                <p className="text-2xl font-bold">{captureMessage.title}</p>
                <p className="mt-2 text-sm font-semibold text-muted-foreground">
                  {captureMessage.detail}
                </p>
              </div>
              <div className="mb-6">
                <BrutalField
                  label="Maximum recording time (seconds)"
                  htmlFor="recording-duration"
                >
                  <BrutalInput
                    id="recording-duration"
                    type="number"
                    min={1}
                    max={60}
                    step={1}
                    value={recordingDuration}
                    disabled={recording}
                    onChange={(event) =>
                      setRecordingDuration(event.target.value)
                    }
                  />
                  <p className="text-xs font-semibold text-muted-foreground">
                    Safety limit after movement begins. A stable final pose ends
                    the recording sooner.
                  </p>
                </BrutalField>
              </div>
              <ol className="flex flex-col gap-3 text-sm font-semibold">
                <li>1. Keep your whole body visible.</li>
                <li>
                  2. Press Start recording and hold the starting pose through
                  the 3-second countdown.
                </li>
                <li>
                  3. Move when “Ready — move now” appears, then hold the final
                  pose. Start and finish are detected automatically.
                </li>
              </ol>
            </BrutalCardContent>
            <BrutalCardFooter className="justify-between">
              <BrutalButton
                onClick={toggleRecording}
                disabled={
                  !cameraLive || (!recording && !recordingDurationValid)
                }
                variant={recording ? "destructive" : "primary"}
              >
                {recording ? <Square /> : <Circle />}
                {recording ? "Cancel recording" : "Start recording"}
              </BrutalButton>
              <BrutalButton
                onClick={() => setStep(3)}
                disabled={repCount === 0 || recording}
              >
                Review
                <ArrowRight />
              </BrutalButton>
            </BrutalCardFooter>
          </BrutalCard>
        </div>
      ) : null}

      {step === 3 ? (
        <BrutalCard className="max-w-xl">
          <BrutalCardHeader>
            <BrutalCardTitle>Ready to save</BrutalCardTitle>
            <BrutalBadge tone="success">
              {repCount} recording{repCount === 1 ? "" : "s"}
            </BrutalBadge>
          </BrutalCardHeader>
          <BrutalCardContent>
            <p className="text-sm font-semibold text-muted-foreground">
              These captured movement recordings will become the motion template
              for “{displayName}”.
            </p>
          </BrutalCardContent>
          <BrutalCardFooter className="justify-between">
            <BrutalButton variant="outline" onClick={reset}>
              <RotateCcw />
              Record again
            </BrutalButton>
            <BrutalButton onClick={save} disabled={saving}>
              <Check />
              {saving ? "Saving…" : "Save to library"}
            </BrutalButton>
          </BrutalCardFooter>
        </BrutalCard>
      ) : null}
    </Page>
  );
};

export default Calibrate;

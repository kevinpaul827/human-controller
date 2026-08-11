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
import {
  CALIBRATION_INSTRUCTIONS,
  DEFAULT_MOVEMENT_NAME,
  DEFAULT_RECORDING_DURATION,
  EMPTY_REP_COUNT,
  MAX_RECORDING_DURATION_SECONDS,
  MIN_RECORDING_DURATION_SECONDS,
  NAME_STEP,
  NO_PROFILE_SELECTED,
  RECORD_STEP,
  RESET_RECORDING_ERROR,
  SAVE_MOVEMENT_ERROR,
  SAVE_STEP,
  START_CALIBRATION_ERROR,
  START_CAMERA_ERROR,
  STEP_LABELS,
  TOGGLE_RECORDING_ERROR,
} from "./Calibrate.constant";

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
  const [step, setStep] = useState(existing ? RECORD_STEP : NAME_STEP);
  const [cameraLive, setCameraLive] = useState(false);
  const [recording, setRecording] = useState(false);
  const [capturePhase, setCapturePhase] = useState<CapturePhase>("idle");
  const [countdownRemaining, setCountdownRemaining] = useState(0);
  const [recordingDuration, setRecordingDuration] = useState(
    DEFAULT_RECORDING_DURATION,
  );
  const [repCount, setRepCount] = useState(EMPTY_REP_COUNT);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const { previewAspectRatio, previewViewportRef: previewRef } =
    useDesktopCameraPreview({
      bridge: calibrateBridge,
      isLive: step === RECORD_STEP,
      trackElapsed: false,
    });
  const displayName = name.trim() || existing?.name || DEFAULT_MOVEMENT_NAME;
  const recordingSeconds = Number(recordingDuration);
  const recordingDurationValid =
    Number.isFinite(recordingSeconds) &&
    recordingSeconds >= MIN_RECORDING_DURATION_SECONDS &&
    recordingSeconds <= MAX_RECORDING_DURATION_SECONDS;

  useEffect(() => {
    const offStatus = calibrateBridge.onCalibrateStatus((event) => {
      setCameraLive(event.state === "live");
      if (event.state === "error")
        setError(event.message ?? START_CAMERA_ERROR);
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
    if (step !== RECORD_STEP) return;
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
              : START_CALIBRATION_ERROR,
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
    setStep(RECORD_STEP);
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
          : TOGGLE_RECORDING_ERROR,
      );
    }
  };

  const reset = async () => {
    setError(null);
    try {
      await calibrateBridge.resetRep();
      setRepCount(EMPTY_REP_COUNT);
      setRecording(false);
      setCapturePhase("idle");
      setCountdownRemaining(0);
      setStep(RECORD_STEP);
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : RESET_RECORDING_ERROR,
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
          : SAVE_MOVEMENT_ERROR,
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
              : NO_PROFILE_SELECTED}
          </p>
        </div>
        <StepProgress steps={STEP_LABELS} currentStep={step} />
      </header>

      {error ? (
        <p className="rounded-base border-2 border-destructive bg-surface px-4 py-3 text-sm font-bold text-destructive">
          {error}
        </p>
      ) : null}

      {step === NAME_STEP ? (
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

      {step === RECORD_STEP ? (
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
                    min={MIN_RECORDING_DURATION_SECONDS}
                    max={MAX_RECORDING_DURATION_SECONDS}
                    step={NAME_STEP}
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
                {CALIBRATION_INSTRUCTIONS.map((instruction, index) => (
                  <li key={instruction}>
                    {index + 1}. {instruction}
                  </li>
                ))}
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
                onClick={() => setStep(SAVE_STEP)}
                disabled={repCount === EMPTY_REP_COUNT || recording}
              >
                Review
                <ArrowRight />
              </BrutalButton>
            </BrutalCardFooter>
          </BrutalCard>
        </div>
      ) : null}

      {step === SAVE_STEP ? (
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

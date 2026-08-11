import { useRef, useState } from "react";
import { ChevronDown, Gauge } from "lucide-react";
import Page from "@/components/Page";
import PageHeader from "@/components/PageHeader";
import { BrutalBadge } from "@/components/ui/brutal-badge";
import { BrutalButton } from "@/components/ui/brutal-button";
import {
  BrutalCard,
  BrutalCardContent,
  BrutalCardHeader,
  BrutalCardTitle,
} from "@/components/ui/brutal-card";
import { BrutalSlider } from "@/components/ui/brutal-slider";
import { cn } from "@/lib/utils";
import { desktopStateBridge } from "@/services/desktopStateBridge";
import { useAppState } from "@/state/appStateContext";
import type { PoseModel, PoseModelRecommendation } from "@/types/desktopState";
import {
  AUTO_MODE_DESCRIPTION,
  AUTO_MODE_TITLE,
  CALIBRATE_TRACKING_LABEL,
  CALIBRATING_TRACKING_LABEL,
  CAMERA_TRACKING_TITLE,
  COOLDOWN_LABEL,
  COOLDOWN_MAX,
  COOLDOWN_MIN,
  COOLDOWN_STEP,
  DEFAULT_EFFORT_LABEL,
  DEFAULT_THRESHOLD_LABEL,
  EFFORT_LABELS,
  MANUAL_MODE_SUMMARY_PREFIX,
  MOVEMENT_RESPONSE_TITLE,
  PAGE_DESCRIPTION,
  PAGE_EYEBROW,
  PAGE_TITLE,
  RECOMMENDATION_ERROR_MESSAGE,
  RESPONSE_HELPER_TEXT,
  SMOOTHING_MAX,
  SMOOTHING_MIN,
  SMOOTHING_STEP,
  STEADINESS_LABEL,
  THRESHOLD_MAX,
  THRESHOLD_MIN,
  THRESHOLD_STEP,
  TRACKING_MODE_LEGEND,
  TRACKING_MODES,
} from "./Settings.constant";

const Settings = () => {
  const { settings, updateSetting } = useAppState();
  const [checkingDevice, setCheckingDevice] = useState(false);
  const [recommendation, setRecommendation] =
    useState<PoseModelRecommendation | null>(null);
  const [recommendationError, setRecommendationError] = useState(false);
  const manualModes = useRef<HTMLDetailsElement>(null);

  const chooseMode = (mode: PoseModel) => {
    updateSetting("poseModel", mode);
    setRecommendation(null);
    setRecommendationError(false);
  };

  const calibrateTracking = async () => {
    setCheckingDevice(true);
    setRecommendation(null);
    setRecommendationError(false);
    try {
      const result = await desktopStateBridge.recommendPoseModel();
      updateSetting("poseModel", result.poseModel);
      setRecommendation(result);
    } catch {
      setRecommendationError(true);
      if (manualModes.current) {
        manualModes.current.open = true;
      }
    } finally {
      setCheckingDevice(false);
    }
  };

  const currentMode =
    TRACKING_MODES.find((mode) => mode.value === settings.poseModel) ??
    TRACKING_MODES[0];
  const recommendedMode = recommendation
    ? TRACKING_MODES.find((mode) => mode.value === recommendation.poseModel)
    : null;
  const recommendationDetails = recommendation
    ? [
        recommendation.ramGb === null ? null : `${recommendation.ramGb} GB RAM`,
        recommendation.physicalCpuCount === null
          ? recommendation.logicalCpuCount === null
            ? null
            : `${recommendation.logicalCpuCount} logical CPU cores`
          : `${recommendation.physicalCpuCount} physical CPU cores`,
      ].filter(Boolean)
    : [];

  return (
    <Page>
      <PageHeader
        eyebrow={PAGE_EYEBROW}
        title={PAGE_TITLE}
        description={PAGE_DESCRIPTION}
      />

      <BrutalCard className="max-w-3xl">
        <BrutalCardHeader>
          <BrutalCardTitle>{CAMERA_TRACKING_TITLE}</BrutalCardTitle>
          <BrutalBadge tone="primary">{currentMode.label}</BrutalBadge>
        </BrutalCardHeader>

        <BrutalCardContent className="flex flex-col gap-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex min-w-0 flex-1 flex-col gap-1">
              <p className="font-bold">{AUTO_MODE_TITLE}</p>
              <p className="text-sm font-medium text-muted-foreground">
                {AUTO_MODE_DESCRIPTION}
              </p>
            </div>
            <BrutalButton
              type="button"
              size="sm"
              variant="outline"
              disabled={checkingDevice}
              onClick={() => void calibrateTracking()}
            >
              <Gauge aria-hidden="true" />
              {checkingDevice
                ? CALIBRATING_TRACKING_LABEL
                : CALIBRATE_TRACKING_LABEL}
            </BrutalButton>
          </div>

          {recommendation ? (
            <p
              role="status"
              aria-live="polite"
              className="rounded-sm bg-surface-muted px-3 py-2 text-sm font-bold text-success"
            >
              {recommendedMode?.label ?? currentMode.label} selected
              {recommendationDetails.length > 0
                ? ` · ${recommendationDetails.join(" · ")}`
                : ""}
            </p>
          ) : null}
          {recommendationError ? (
            <p
              role="alert"
              className="rounded-sm bg-surface-muted px-3 py-2 text-sm font-bold text-destructive"
            >
              {RECOMMENDATION_ERROR_MESSAGE}
            </p>
          ) : null}

          <details
            ref={manualModes}
            className="group rounded-sm border border-hairline bg-surface-muted"
          >
            <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-3 py-2.5 text-sm font-bold focus-visible:outline-3 focus-visible:outline-primary [&::-webkit-details-marker]:hidden">
              {MANUAL_MODE_SUMMARY_PREFIX} {currentMode.label}
              <ChevronDown
                className="transition-transform group-open:rotate-180"
                aria-hidden="true"
              />
            </summary>
            <fieldset className="flex flex-col gap-2 border-t border-hairline p-3">
              <legend className="sr-only">{TRACKING_MODE_LEGEND}</legend>
              {TRACKING_MODES.map((mode) => {
                const selected = settings.poseModel === mode.value;
                return (
                  <label
                    key={mode.value}
                    className={cn(
                      "flex cursor-pointer flex-wrap items-center gap-x-3 gap-y-1 rounded-sm border px-3 py-2.5",
                      selected
                        ? "border-border bg-accent text-accent-foreground"
                        : "border-hairline bg-surface hover:border-border",
                      checkingDevice && "cursor-not-allowed opacity-55",
                    )}
                  >
                    <input
                      type="radio"
                      name="tracking-mode"
                      value={mode.value}
                      checked={selected}
                      disabled={checkingDevice}
                      onChange={() => chooseMode(mode.value)}
                      className="size-4 accent-primary"
                    />
                    <span className="min-w-32 font-bold">{mode.label}</span>
                    <span className="min-w-0 flex-1 text-sm font-medium">
                      {mode.detail}
                    </span>
                    <span className="font-mono text-xs font-bold">
                      {mode.ram}
                    </span>
                  </label>
                );
              })}
            </fieldset>
          </details>
        </BrutalCardContent>
      </BrutalCard>

      <BrutalCard className="max-w-3xl">
        <BrutalCardHeader>
          <BrutalCardTitle>{MOVEMENT_RESPONSE_TITLE}</BrutalCardTitle>
        </BrutalCardHeader>
        <BrutalCardContent className="flex flex-col gap-6">
          <BrutalSlider
            label={DEFAULT_THRESHOLD_LABEL}
            value={settings.matchThreshold}
            min={THRESHOLD_MIN}
            max={THRESHOLD_MAX}
            step={THRESHOLD_STEP}
            formatValue={(value) => `${value}%`}
            onChange={(value) => updateSetting("matchThreshold", value)}
          />
          <p className="-mt-4 text-sm font-medium text-muted-foreground">
            {RESPONSE_HELPER_TEXT}
          </p>
          <BrutalSlider
            label={COOLDOWN_LABEL}
            value={settings.cooldown}
            min={COOLDOWN_MIN}
            max={COOLDOWN_MAX}
            step={COOLDOWN_STEP}
            formatValue={(value) => `${value.toFixed(1)}s`}
            onChange={(value) => updateSetting("cooldown", value)}
          />
          <BrutalSlider
            label={STEADINESS_LABEL}
            value={settings.smoothing}
            min={SMOOTHING_MIN}
            max={SMOOTHING_MAX}
            step={SMOOTHING_STEP}
            formatValue={(value) => EFFORT_LABELS[value] ?? DEFAULT_EFFORT_LABEL}
            onChange={(value) => updateSetting("smoothing", value)}
          />
        </BrutalCardContent>
      </BrutalCard>
    </Page>
  );
};

export default Settings;

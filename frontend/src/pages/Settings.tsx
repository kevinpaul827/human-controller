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

const EFFORT_LABELS = [
  "Very gentle",
  "Gentle",
  "Balanced",
  "Precise",
  "Strict",
];

const TRACKING_MODES: {
  value: PoseModel;
  label: string;
  detail: string;
  ram: string;
}[] = [
  {
    value: "lite",
    label: "Fast",
    detail: "Prioritises smooth frame rate",
    ram: "4 GB+ RAM, 2+ CPU cores",
  },
  {
    value: "full",
    label: "Balanced",
    detail: "Good speed and tracking accuracy",
    ram: "8 GB+ RAM, 4+ CPU cores",
  },
  {
    value: "heavy",
    label: "High accuracy",
    detail: "Prioritises tracking detail",
    ram: "16 GB+ RAM, 8+ CPU cores",
  },
];

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
        eyebrow="Settings"
        title="Tracking preferences"
        description="Changes save automatically."
      />

      <BrutalCard className="max-w-3xl">
        <BrutalCardHeader>
          <BrutalCardTitle>Camera tracking</BrutalCardTitle>
          <BrutalBadge tone="primary">{currentMode.label}</BrutalBadge>
        </BrutalCardHeader>

        <BrutalCardContent className="flex flex-col gap-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex min-w-0 flex-1 flex-col gap-1">
              <p className="font-bold">Optimise for this device</p>
              <p className="text-sm font-medium text-muted-foreground">
                Checks memory and processor capacity, then picks a tracking
                mode.
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
              {checkingDevice ? "Calibrating…" : "Calibrate tracking"}
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
              Couldn’t check this device. Choose a mode manually.
            </p>
          ) : null}

          <details
            ref={manualModes}
            className="group rounded-sm border border-hairline bg-surface-muted"
          >
            <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-3 py-2.5 text-sm font-bold focus-visible:outline-3 focus-visible:outline-primary [&::-webkit-details-marker]:hidden">
              Choose manually · Current: {currentMode.label}
              <ChevronDown
                className="transition-transform group-open:rotate-180"
                aria-hidden="true"
              />
            </summary>
            <fieldset className="flex flex-col gap-2 border-t border-hairline p-3">
              <legend className="sr-only">Tracking mode</legend>
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
          <BrutalCardTitle>Movement response</BrutalCardTitle>
        </BrutalCardHeader>
        <BrutalCardContent className="flex flex-col gap-6">
          <BrutalSlider
            label="Default match threshold"
            value={settings.matchThreshold}
            min={0}
            max={100}
            step={1}
            formatValue={(value) => `${value}%`}
            onChange={(value) => updateSetting("matchThreshold", value)}
          />
          <p className="-mt-4 text-sm font-medium text-muted-foreground">
            Applied to new bindings. Existing movements can be adjusted from the
            Session page.
          </p>
          <BrutalSlider
            label="Cooldown"
            value={settings.cooldown}
            min={0}
            max={2}
            step={0.1}
            formatValue={(value) => `${value.toFixed(1)}s`}
            onChange={(value) => updateSetting("cooldown", value)}
          />
          <BrutalSlider
            label="Steadiness"
            value={settings.smoothing}
            min={0}
            max={4}
            step={1}
            formatValue={(value) => EFFORT_LABELS[value] ?? "Balanced"}
            onChange={(value) => updateSetting("smoothing", value)}
          />
        </BrutalCardContent>
      </BrutalCard>
    </Page>
  );
};

export default Settings;

import { useEffect, useState } from "react";
import { RotateCcw, Save } from "lucide-react";
import Page from "@/components/Page";
import PageHeader from "@/components/PageHeader";
import { BrutalButton } from "@/components/ui/brutal-button";
import { BrutalBadge } from "@/components/ui/brutal-badge";
import {
  BrutalCard,
  BrutalCardContent,
  BrutalCardFooter,
  BrutalCardHeader,
  BrutalCardTitle,
} from "@/components/ui/brutal-card";
import { BrutalSlider } from "@/components/ui/brutal-slider";
import { useAppState } from "@/state/appStateContext";

const EFFORT_LABELS = [
  "Very gentle",
  "Gentle",
  "Balanced",
  "Precise",
  "Strict",
];

const Settings = () => {
  const { settings, saveSettings } = useAppState();
  const [values, setValues] = useState(settings);
  useEffect(() => setValues(settings), [settings]);

  const isDirty = (Object.keys(settings) as (keyof typeof settings)[]).some(
    (key) => values[key] !== settings[key],
  );

  const update = <K extends keyof typeof settings>(key: K, value: number) =>
    setValues((current) => ({ ...current, [key]: value }));

  return (
    <Page>
      <PageHeader
        eyebrow="Difficulty"
        title="How hard should it be?"
        actions={
          isDirty ? (
            <BrutalBadge tone="accent">Unsaved changes</BrutalBadge>
          ) : null
        }
      />

      <BrutalCard className="max-w-3xl">
        <BrutalCardHeader>
          <BrutalCardTitle>Movement detection</BrutalCardTitle>
        </BrutalCardHeader>

        <BrutalCardContent className="flex flex-col gap-6">
          <BrutalSlider
            label="Default match threshold"
            value={values.matchThreshold}
            min={0}
            max={100}
            step={1}
            formatValue={(value) => `${value}%`}
            onChange={(value) => update("matchThreshold", value)}
          />
          <p className="-mt-4 text-sm font-medium text-muted-foreground">
            Applied to new bindings. Existing movements can be adjusted
            independently from the Session page.
          </p>
          <BrutalSlider
            label="Hold duration"
            value={values.holdDuration}
            min={0.5}
            max={3}
            step={0.1}
            formatValue={(value) => `${value.toFixed(1)}s`}
            onChange={(value) => update("holdDuration", value)}
          />
          <BrutalSlider
            label="Cooldown"
            value={values.cooldown}
            min={0}
            max={2}
            step={0.1}
            formatValue={(value) => `${value.toFixed(1)}s`}
            onChange={(value) => update("cooldown", value)}
          />
          <BrutalSlider
            label="Steadiness"
            value={values.smoothing}
            min={0}
            max={4}
            step={1}
            formatValue={(value) => EFFORT_LABELS[value] ?? "Balanced"}
            onChange={(value) => update("smoothing", value)}
          />
        </BrutalCardContent>

        <BrutalCardFooter className="justify-end">
          <BrutalButton
            variant="outline"
            onClick={() => setValues(settings)}
            disabled={!isDirty}
          >
            <RotateCcw aria-hidden="true" />
            Start over
          </BrutalButton>
          <BrutalButton
            disabled={!isDirty}
            onClick={() => saveSettings(values)}
          >
            <Save aria-hidden="true" />
            Save
          </BrutalButton>
        </BrutalCardFooter>
      </BrutalCard>
    </Page>
  );
};

export default Settings;

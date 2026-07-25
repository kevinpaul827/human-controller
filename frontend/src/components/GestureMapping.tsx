import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  AlertTriangle,
  Check,
  FolderOpen,
  Plus,
  Save,
  SlidersHorizontal,
  Video,
  X,
} from "lucide-react";
import { DropdownMenu, Popover } from "radix-ui";
import AddBindingDialog from "@/components/AddBindingDialog";
import KeyPicker from "@/components/KeyPicker";
import { BrutalButton } from "@/components/ui/brutal-button";
import { BrutalBadge } from "@/components/ui/brutal-badge";
import {
  BrutalCard,
  BrutalCardFooter,
  BrutalCardHeader,
  BrutalCardTitle,
} from "@/components/ui/brutal-card";
import { BrutalDialog } from "@/components/ui/brutal-dialog";
import { BrutalField, BrutalInput } from "@/components/ui/brutal-input";
import { BrutalSlider } from "@/components/ui/brutal-slider";
import { useAppState } from "@/state/appStateContext";
import { ROUTES } from "@/utils/constants";

const BindingThresholdPopover = ({
  gestureName,
  value,
  onChange,
}: {
  gestureName: string;
  value: number;
  onChange: (value: number) => void;
}) => (
  <Popover.Root>
    <Popover.Trigger asChild>
      <button
        type="button"
        aria-label={`Adjust match threshold for ${gestureName}`}
        title={`Adjust match threshold for ${gestureName}`}
        className="inline-flex size-8 shrink-0 cursor-pointer items-center justify-center rounded-sm border border-hairline text-muted-foreground transition-[translate,box-shadow] duration-100 hover:translate-x-0.5 hover:translate-y-0.5 hover:bg-surface-muted hover:text-foreground hover:shadow-brutal-sm active:translate-x-1 active:translate-y-1 active:shadow-none"
      >
        <SlidersHorizontal className="size-4" aria-hidden="true" />
      </button>
    </Popover.Trigger>
    <Popover.Portal>
      <Popover.Content
        align="end"
        sideOffset={6}
        className="z-50 w-72 rounded-base border-2 bg-surface p-4 shadow-brutal"
      >
        <BrutalSlider
          label="Match threshold"
          value={value}
          min={0}
          max={100}
          step={1}
          formatValue={(threshold) => `${threshold}%`}
          onChange={onChange}
        />
        <p className="mt-2 text-xs font-medium text-muted-foreground">
          Lower is easier to trigger; higher requires a closer match.
        </p>
      </Popover.Content>
    </Popover.Portal>
  </Popover.Root>
);

const GestureMapping = () => {
  const navigate = useNavigate();
  const {
    bindings,
    presets,
    activePreset,
    hasUnsavedChanges,
    readiness,
    rebindKey,
    setBindingThreshold,
    unbindGesture,
    savePreset,
    loadPreset,
  } = useAppState();
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [presetName, setPresetName] = useState("");
  const takenKeys = bindings.map((binding) => binding.key);

  const handleSavePreset = () => {
    const name = presetName.trim();
    if (!name) return;
    savePreset(name);
    setShowSaveDialog(false);
    setPresetName("");
  };

  return (
    <>
      <BrutalCard className="min-h-0">
        <BrutalCardHeader>
          <div className="flex min-w-0 items-center gap-2">
            <BrutalCardTitle className="truncate">
              {activePreset?.name ?? "Bindings"}
            </BrutalCardTitle>
            {hasUnsavedChanges ? (
              <BrutalBadge tone="accent">Edited</BrutalBadge>
            ) : null}
          </div>
          <BrutalBadge tone={readiness.isReady ? "success" : "accent"}>
            {bindings.length} bound
          </BrutalBadge>
        </BrutalCardHeader>

        {bindings.length === 0 ? (
          <div className="flex flex-1 flex-col items-center justify-center gap-3 p-8 text-center">
            <p className="text-sm font-semibold text-muted-foreground">
              Nothing bound yet
            </p>
            <BrutalButton size="sm" onClick={() => setShowAddDialog(true)}>
              <Plus aria-hidden="true" />
              Add binding
            </BrutalButton>
          </div>
        ) : (
          <ul className="min-h-0 flex-1 divide-y divide-hairline overflow-y-auto">
            {bindings.map(({ gesture, key, matchThreshold }) => {
              const recorded = Boolean(gesture.calibratedAt);
              return (
                <li
                  key={gesture.gestureId}
                  className="flex items-center gap-2.5 px-4 py-2.5"
                >
                  <span className="min-w-0 flex-1 truncate text-sm font-bold">
                    {gesture.name}
                  </span>
                  {!recorded ? (
                    <button
                      type="button"
                      onClick={() =>
                        navigate(
                          `${ROUTES.calibrate}?gesture=${gesture.gestureId}`,
                        )
                      }
                      className="flex cursor-pointer items-center gap-1 text-xs font-bold text-muted-foreground hover:text-foreground"
                      title="Record this movement"
                    >
                      <AlertTriangle className="size-3.5" aria-hidden="true" />
                      Record
                    </button>
                  ) : null}
                  <KeyPicker
                    value={key}
                    takenKeys={takenKeys}
                    onChange={(next) => rebindKey(gesture.gestureId, next)}
                  />
                  <BindingThresholdPopover
                    gestureName={gesture.name}
                    value={matchThreshold}
                    onChange={(threshold) =>
                      setBindingThreshold(gesture.gestureId, threshold)
                    }
                  />
                  <button
                    type="button"
                    aria-label={`Remove ${gesture.name} binding`}
                    onClick={() => unbindGesture(gesture.gestureId)}
                    className="inline-flex size-8 shrink-0 cursor-pointer items-center justify-center rounded-sm border border-hairline text-muted-foreground hover:bg-surface-muted hover:text-foreground"
                  >
                    <X className="size-4" aria-hidden="true" />
                  </button>
                </li>
              );
            })}
          </ul>
        )}

        <BrutalCardFooter className="gap-2 px-4">
          <BrutalButton
            variant="outline"
            size="sm"
            onClick={() => setShowAddDialog(true)}
          >
            <Plus aria-hidden="true" />
            Add binding
          </BrutalButton>

          <DropdownMenu.Root>
            <DropdownMenu.Trigger asChild>
              <BrutalButton variant="outline" size="sm">
                <FolderOpen aria-hidden="true" />
                Load preset
              </BrutalButton>
            </DropdownMenu.Trigger>
            <DropdownMenu.Portal>
              <DropdownMenu.Content
                align="end"
                sideOffset={6}
                className="z-50 w-60 rounded-base border-2 bg-surface p-1.5 shadow-brutal"
              >
                {presets.length === 0 ? (
                  <p className="px-2 py-3 text-sm font-semibold text-muted-foreground">
                    No saved presets
                  </p>
                ) : (
                  presets.map((preset) => (
                    <DropdownMenu.Item
                      key={preset.presetId}
                      onSelect={() => loadPreset(preset.presetId)}
                      className="flex cursor-pointer items-center gap-2 rounded-sm px-2 py-2 text-sm font-semibold outline-none data-[highlighted]:bg-surface-muted"
                    >
                      <span className="min-w-0 flex-1 truncate">
                        {preset.name}
                      </span>
                      {preset.presetId === activePreset?.presetId ? (
                        <Check className="size-4" aria-label="Loaded" />
                      ) : (
                        <span className="text-xs text-muted-foreground">
                          {preset.bindings.length}
                        </span>
                      )}
                    </DropdownMenu.Item>
                  ))
                )}
              </DropdownMenu.Content>
            </DropdownMenu.Portal>
          </DropdownMenu.Root>

          <BrutalButton
            variant="outline"
            size="sm"
            disabled={bindings.length === 0}
            aria-label="Save bindings as preset"
            onClick={() => {
              setPresetName(activePreset?.name ?? "");
              setShowSaveDialog(true);
            }}
          >
            <Save aria-hidden="true" />
            Save
          </BrutalButton>

          <BrutalButton
            variant="outline"
            size="sm"
            aria-label="Record a new movement"
            onClick={() => navigate(`${ROUTES.calibrate}?new=1`)}
          >
            <Video aria-hidden="true" />
          </BrutalButton>
        </BrutalCardFooter>
      </BrutalCard>

      <AddBindingDialog open={showAddDialog} onOpenChange={setShowAddDialog} />

      <BrutalDialog
        open={showSaveDialog}
        onOpenChange={setShowSaveDialog}
        title="Save as preset"
        footer={
          <>
            <BrutalButton
              variant="outline"
              onClick={() => setShowSaveDialog(false)}
            >
              Cancel
            </BrutalButton>
            <BrutalButton
              onClick={handleSavePreset}
              disabled={presetName.trim().length === 0}
            >
              Save
            </BrutalButton>
          </>
        }
      >
        <BrutalField label="Preset name" htmlFor="preset-name">
          <BrutalInput
            id="preset-name"
            value={presetName}
            onChange={(event) => setPresetName(event.target.value)}
            placeholder="e.g. Celeste"
            autoFocus
          />
        </BrutalField>
      </BrutalDialog>
    </>
  );
};

export default GestureMapping;

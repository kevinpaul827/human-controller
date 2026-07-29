import { useMemo, useState } from "react";
import { Play, Trash2, Video } from "lucide-react";
import KeyCaptureInput from "@/components/KeyCaptureInput";
import { BrutalBadge } from "@/components/ui/brutal-badge";
import { BrutalButton } from "@/components/ui/brutal-button";
import {
  BrutalCard,
  BrutalCardContent,
  BrutalCardFooter,
  BrutalCardHeader,
  BrutalCardTitle,
} from "@/components/ui/brutal-card";
import { Keycap } from "@/components/ui/keycap";
import type { GestureSummary, PatientProfile } from "@/types/profile";

const formatUpdatedAt = (value: string) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Unknown";
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
};

type PatientCardProps = {
  profile: PatientProfile;
  gestures: GestureSummary[];
  expanded: boolean;
  onExpandChange: (expanded: boolean) => void;
  onSetBinding: (gestureId: string, key: string) => Promise<string | null>;
  onRemoveBinding: (gestureId: string) => Promise<string | null>;
  onCalibrate: () => void;
  onStartSession: () => void;
  onDelete: () => Promise<void>;
};

const PatientCard = ({
  profile,
  gestures,
  expanded,
  onExpandChange,
  onSetBinding,
  onRemoveBinding,
  onCalibrate,
  onStartSession,
  onDelete,
}: PatientCardProps) => {
  const [selectedGestureId, setSelectedGestureId] = useState("");
  const [newKey, setNewKey] = useState("");
  const [editingGestureId, setEditingGestureId] = useState<string | null>(null);
  const [editedKey, setEditedKey] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const gestureById = useMemo(
    () => new Map(gestures.map((gesture) => [gesture.gestureId, gesture])),
    [gestures],
  );
  const bindings = Object.entries(profile.keyBindings).sort(
    ([left], [right]) => {
      const leftName = gestureById.get(left)?.name ?? left;
      const rightName = gestureById.get(right)?.name ?? right;
      return leftName.localeCompare(rightName);
    },
  );
  const availableGestures = gestures.filter(
    (gesture) => !(gesture.gestureId in profile.keyBindings),
  );

  const handleAddBinding = async () => {
    if (!selectedGestureId || !newKey) {
      setFormError("Choose a movement and press a keyboard key.");
      return;
    }

    setSaving(true);
    setFormError(null);
    const error = await onSetBinding(selectedGestureId, newKey);
    setSaving(false);
    setFormError(error);
    if (!error) {
      setSelectedGestureId("");
      setNewKey("");
    }
  };

  const startEditing = (gestureId: string, key: string) => {
    setEditingGestureId(gestureId);
    setEditedKey(key);
    setFormError(null);
  };

  const handleUpdateBinding = async () => {
    if (!editingGestureId || !editedKey) {
      setFormError("Press a keyboard key before saving.");
      return;
    }

    setSaving(true);
    setFormError(null);
    const error = await onSetBinding(editingGestureId, editedKey);
    setSaving(false);
    setFormError(error);
    if (!error) {
      setEditingGestureId(null);
      setEditedKey("");
    }
  };

  const handleRemoveBinding = async (gestureId: string) => {
    setSaving(true);
    setFormError(null);
    const error = await onRemoveBinding(gestureId);
    setSaving(false);
    setFormError(error);
  };

  return (
    <BrutalCard>
      <BrutalCardHeader>
        <div className="min-w-0">
          <BrutalCardTitle className="truncate">
            {profile.patientName}
          </BrutalCardTitle>
          {profile.notes ? (
            <p className="mt-1 text-sm font-semibold text-muted-foreground">
              {profile.notes}
            </p>
          ) : null}
          <p className="mt-1 text-xs font-semibold text-muted-foreground">
            Last updated {formatUpdatedAt(profile.updatedAt)}
          </p>
        </div>
        <BrutalBadge>
          {bindings.length} binding{bindings.length === 1 ? "" : "s"}
        </BrutalBadge>
      </BrutalCardHeader>

      {expanded ? (
        <BrutalCardContent className="space-y-5">
          <div className="space-y-2">
            <h3 className="font-bold">Movement bindings</h3>
            {bindings.length ? (
              <div className="divide-y divide-hairline rounded-base border-2">
                {bindings.map(([gestureId, key]) => (
                  <div
                    key={gestureId}
                    className="flex flex-wrap items-center gap-3 px-3 py-2.5"
                  >
                    <span className="min-w-40 flex-1 font-semibold">
                      {gestureById.get(gestureId)?.name ??
                        "Unavailable movement"}
                    </span>
                    {editingGestureId === gestureId ? (
                      <>
                        <KeyCaptureInput
                          ariaLabel={`New key for ${gestureById.get(gestureId)?.name ?? "movement"}`}
                          value={editedKey}
                          onChange={setEditedKey}
                          disabled={saving}
                        />
                        <BrutalButton
                          size="sm"
                          disabled={saving}
                          onClick={() => void handleUpdateBinding()}
                        >
                          Save
                        </BrutalButton>
                        <BrutalButton
                          size="sm"
                          variant="outline"
                          disabled={saving}
                          onClick={() => {
                            setEditingGestureId(null);
                            setEditedKey("");
                            setFormError(null);
                          }}
                        >
                          Cancel
                        </BrutalButton>
                      </>
                    ) : (
                      <>
                        <Keycap keyName={key} size="sm" />
                        <BrutalButton
                          size="sm"
                          variant="outline"
                          disabled={saving}
                          onClick={() => startEditing(gestureId, key)}
                        >
                          Change key
                        </BrutalButton>
                        <BrutalButton
                          size="sm"
                          variant="outline"
                          disabled={saving}
                          onClick={() => void handleRemoveBinding(gestureId)}
                        >
                          Remove
                        </BrutalButton>
                      </>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm font-semibold text-muted-foreground">
                No movements are bound to this profile yet.
              </p>
            )}
          </div>

          {gestures.length === 0 ? (
            <p className="text-sm font-semibold text-muted-foreground">
              No calibrated movements are available yet.
            </p>
          ) : availableGestures.length ? (
            <div className="grid gap-3 rounded-base border-2 bg-surface-muted p-4 md:grid-cols-[minmax(12rem,1fr)_minmax(12rem,1fr)_auto] md:items-end">
              <label className="flex flex-col gap-1.5 text-sm font-bold">
                Movement
                <select
                  value={selectedGestureId}
                  onChange={(event) => setSelectedGestureId(event.target.value)}
                  className="h-11 rounded-base border-2 bg-surface px-3 font-semibold"
                  disabled={saving}
                >
                  <option value="">Choose movement</option>
                  {availableGestures.map((gesture) => (
                    <option key={gesture.gestureId} value={gesture.gestureId}>
                      {gesture.name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="flex flex-col gap-1.5 text-sm font-bold">
                Keyboard key
                <KeyCaptureInput
                  ariaLabel={`Key for ${profile.patientName}`}
                  value={newKey}
                  onChange={setNewKey}
                  disabled={saving}
                />
              </label>
              <BrutalButton
                disabled={saving}
                onClick={() => void handleAddBinding()}
              >
                Add binding
              </BrutalButton>
            </div>
          ) : (
            <p className="text-sm font-semibold text-muted-foreground">
              All calibrated movements are already assigned to this profile.
            </p>
          )}

          {formError ? (
            <p className="text-sm font-bold text-destructive" role="alert">
              {formError}
            </p>
          ) : null}
        </BrutalCardContent>
      ) : null}

      <BrutalCardFooter>
        <BrutalButton
          variant="outline"
          onClick={() => {
            onExpandChange(!expanded);
            setFormError(null);
          }}
          disabled={saving}
        >
          {expanded ? "Close bindings" : "Manage bindings"}
        </BrutalButton>
        <BrutalButton variant="outline" onClick={onCalibrate} disabled={saving}>
          <Video aria-hidden="true" />
          Calibrate
        </BrutalButton>
        <BrutalButton onClick={onStartSession} disabled={saving}>
          <Play aria-hidden="true" />
          Start session
        </BrutalButton>
        <BrutalButton
          className="ml-auto"
          variant="destructive"
          onClick={() => void onDelete()}
          disabled={saving}
        >
          <Trash2 aria-hidden="true" />
          Delete
        </BrutalButton>
      </BrutalCardFooter>
    </BrutalCard>
  );
};

export default PatientCard;

import { useState } from "react";
import { BrutalButton } from "@/components/ui/brutal-button";
import { BrutalDialog } from "@/components/ui/brutal-dialog";
import { BrutalField, BrutalInput } from "@/components/ui/brutal-input";

type CreateProfileDialogProps = {
  open: boolean;
  onClose: () => void;
  onCreate: (patientName: string, notes: string) => Promise<string | null>;
};

const CreateProfileDialog = ({
  open,
  onClose,
  onCreate,
}: CreateProfileDialogProps) => {
  const [patientName, setPatientName] = useState("");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const handleSubmit = async () => {
    const resolvedName = patientName.trim();
    if (!resolvedName) {
      setError("Patient name is required.");
      return;
    }
    if (resolvedName.length > 80) {
      setError("Patient name cannot exceed 80 characters.");
      return;
    }

    setSaving(true);
    setError(null);
    const saveError = await onCreate(resolvedName, notes.trim());
    setSaving(false);
    if (saveError) {
      setError(saveError);
      return;
    }
    setPatientName("");
    setNotes("");
  };

  return (
    <BrutalDialog
      open={open}
      onOpenChange={(next) => {
        if (!next && !saving) onClose();
      }}
      title="Create patient profile"
      description="Keep movements and game controls separate for each patient."
      footer={
        <>
          <BrutalButton variant="outline" onClick={onClose} disabled={saving}>
            Cancel
          </BrutalButton>
          <BrutalButton onClick={() => void handleSubmit()} disabled={saving}>
            {saving ? "Creating…" : "Create profile"}
          </BrutalButton>
        </>
      }
    >
      <div className="space-y-4">
        <BrutalField label="Patient name" htmlFor="profile-patient-name">
          <BrutalInput
            id="profile-patient-name"
            value={patientName}
            onChange={(event) => setPatientName(event.target.value)}
            placeholder="e.g. Patient C"
            disabled={saving}
            autoFocus
          />
        </BrutalField>
        <BrutalField label="Notes" htmlFor="profile-notes">
          <textarea
            id="profile-notes"
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            placeholder="Optional treatment or accessibility notes"
            rows={4}
            disabled={saving}
            className="w-full resize-y rounded-base border-2 bg-surface px-3 py-2 text-[0.9375rem] font-medium focus-visible:outline-3 focus-visible:outline-primary disabled:opacity-55"
          />
        </BrutalField>
        {error ? (
          <p className="text-sm font-bold text-destructive" role="alert">
            {error}
          </p>
        ) : null}
      </div>
    </BrutalDialog>
  );
};

export default CreateProfileDialog;

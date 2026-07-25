import { useState } from "react";
import { DropdownMenu } from "radix-ui";
import { Check, ChevronsUpDown, Plus, UserRound } from "lucide-react";
import { BrutalButton } from "@/components/ui/brutal-button";
import { BrutalDialog } from "@/components/ui/brutal-dialog";
import { useAppState } from "@/state/appStateContext";
import { initialsOf } from "@/lib/format";
import { cn } from "@/lib/utils";

const ProfileSwitcher = () => {
  const { patients, selectedPatient, selectPatient, createPatient } =
    useAppState();
  const [createOpen, setCreateOpen] = useState(false);
  const [patientName, setPatientName] = useState("");

  if (!selectedPatient) {
    return null;
  }

  const createProfile = () => {
    if (!patientName.trim()) {
      return;
    }
    createPatient(patientName);
    setPatientName("");
    setCreateOpen(false);
  };

  return (
    <>
      <DropdownMenu.Root>
        <DropdownMenu.Trigger
          className={cn(
            "flex shrink-0 cursor-pointer items-center gap-2 rounded-sm border border-hairline bg-surface-muted py-1 pr-2 pl-1",
            "transition-[translate,box-shadow] duration-100",
            "hover:translate-x-0.5 hover:translate-y-0.5 hover:shadow-brutal-sm active:translate-x-1 active:translate-y-1 active:shadow-none",
          )}
        >
          <span
            aria-hidden="true"
            className="flex size-7 items-center justify-center rounded-sm border border-hairline bg-surface font-mono text-xs font-bold text-foreground"
          >
            {initialsOf(selectedPatient.patientName)}
          </span>
          <span className="text-sm font-bold">
            {selectedPatient.patientName}
          </span>
          <ChevronsUpDown
            className="size-4 shrink-0 text-muted-foreground"
            aria-hidden="true"
          />
        </DropdownMenu.Trigger>

        <DropdownMenu.Portal>
          <DropdownMenu.Content
            align="end"
            sideOffset={8}
            className="z-50 w-56 rounded-base border-2 bg-surface p-1.5 shadow-brutal"
          >
            <DropdownMenu.Label className="label-caps px-2 py-1.5 text-muted-foreground">
              Session is for
            </DropdownMenu.Label>
            {patients.map((patient) => (
              <DropdownMenu.Item
                key={patient.patientId}
                onSelect={() => selectPatient(patient.patientId)}
                className="flex cursor-pointer items-center gap-2 rounded-sm px-2 py-2 text-sm font-semibold outline-none data-[highlighted]:bg-surface-muted"
              >
                <UserRound className="size-4 shrink-0" aria-hidden="true" />
                <span className="flex-1 truncate">{patient.patientName}</span>
                {patient.patientId === selectedPatient.patientId ? (
                  <Check className="size-4 shrink-0" aria-hidden="true" />
                ) : null}
              </DropdownMenu.Item>
            ))}
            <DropdownMenu.Separator className="my-1.5 h-px bg-hairline" />
            <DropdownMenu.Item
              onSelect={(event) => {
                event.preventDefault();
                setCreateOpen(true);
              }}
              className="flex cursor-pointer items-center gap-2 rounded-sm px-2 py-2 text-sm font-semibold text-primary outline-none data-[highlighted]:bg-surface-muted"
            >
              <Plus className="size-4 shrink-0" aria-hidden="true" />
              Add profile
            </DropdownMenu.Item>
          </DropdownMenu.Content>
        </DropdownMenu.Portal>
      </DropdownMenu.Root>

      <BrutalDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        title="Add a profile"
        description="Create a separate set of movement bindings."
        footer={
          <>
            <BrutalButton
              variant="outline"
              onClick={() => setCreateOpen(false)}
            >
              Cancel
            </BrutalButton>
            <BrutalButton
              onClick={createProfile}
              disabled={!patientName.trim()}
            >
              Add profile
            </BrutalButton>
          </>
        }
      >
        <label className="flex flex-col gap-2 text-sm font-semibold">
          Profile name
          <input
            autoFocus
            value={patientName}
            onChange={(event) => setPatientName(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                createProfile();
              }
            }}
            placeholder="Patient name"
            className="rounded-sm border border-hairline bg-surface-muted px-3 py-2 text-base font-semibold outline-none focus:border-primary"
          />
        </label>
      </BrutalDialog>
    </>
  );
};

export default ProfileSwitcher;

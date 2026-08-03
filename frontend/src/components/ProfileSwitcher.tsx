import { useState } from "react";
import { DropdownMenu } from "radix-ui";
import { Check, ChevronsUpDown, Plus, UserRound } from "lucide-react";
import CreateProfileDialog from "@/components/CreateProfileDialog";
import { useAppState } from "@/state/appStateContext";
import { initialsOf } from "@/lib/format";
import { cn } from "@/lib/utils";

const ProfileSwitcher = () => {
  const {
    patients,
    selectedPatient,
    selectPatient,
    createPatient,
    clearPatientSelection,
  } = useAppState();
  const [createOpen, setCreateOpen] = useState(false);

  const createProfile = async (patientName: string, notes: string) => {
    try {
      const profile = await createPatient(patientName, notes);
      if (!profile) {
        return "The profile could not be created.";
      }
      setCreateOpen(false);
      return null;
    } catch (error) {
      return error instanceof Error ? error.message : String(error);
    }
  };

  return (
    <>
      <DropdownMenu.Root>
        <DropdownMenu.Trigger
          className={cn(
            "inline-flex h-9 shrink-0 cursor-pointer items-center gap-2 rounded-sm border-2 bg-surface px-2 text-sm font-bold",
            "shadow-brutal-sm transition-[translate,box-shadow] duration-100",
            "hover:translate-x-0.5 hover:translate-y-0.5 hover:shadow-none",
            "active:translate-x-1 active:translate-y-1 active:shadow-none",
            "outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2",
          )}
        >
          <span
            aria-hidden="true"
            className="flex size-6 items-center justify-center rounded-sm border-2 bg-surface-muted font-mono text-[0.65rem] font-bold"
          >
            {selectedPatient ? (
              initialsOf(selectedPatient.patientName)
            ) : (
              <UserRound className="size-3.5" />
            )}
          </span>
          <span className="max-w-[9rem] truncate">
            {selectedPatient?.patientName ?? "Select profile"}
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
                onSelect={() => {
                  if (patient.patientId === selectedPatient?.patientId) {
                    void clearPatientSelection();
                    return;
                  }
                  void selectPatient(patient.patientId);
                }}
                className="flex cursor-pointer items-center gap-2 rounded-sm px-2 py-2 text-sm font-semibold outline-none data-[highlighted]:bg-surface-muted"
              >
                <span
                  aria-hidden="true"
                  className="flex size-5 items-center justify-center rounded-sm border font-mono text-[0.6rem] font-bold"
                >
                  {initialsOf(patient.patientName)}
                </span>
                <span className="flex-1 truncate">{patient.patientName}</span>
                {patient.patientId === selectedPatient?.patientId ? (
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

      {createOpen ? (
        <CreateProfileDialog
          open
          onClose={() => setCreateOpen(false)}
          onCreate={createProfile}
        />
      ) : null}
    </>
  );
};

export default ProfileSwitcher;

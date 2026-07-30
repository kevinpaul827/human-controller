import { useState } from "react";
import { DropdownMenu } from "radix-ui";
import { Check, ChevronsUpDown, Plus, UserRound } from "lucide-react";
import CreateProfileDialog from "@/components/CreateProfileDialog";
import { useAppState } from "@/state/appStateContext";
import { initialsOf } from "@/lib/format";
import { cn } from "@/lib/utils";

const ProfileSwitcher = () => {
  const { patients, selectedPatient, selectPatient, createPatient } =
    useAppState();
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
            "flex shrink-0 cursor-pointer items-center gap-2 rounded-sm border border-hairline bg-surface-muted py-1 pr-2 pl-1",
            "transition-[translate,box-shadow] duration-100",
            "hover:translate-x-0.5 hover:translate-y-0.5 hover:shadow-brutal-sm active:translate-x-1 active:translate-y-1 active:shadow-none",
          )}
        >
          <span
            aria-hidden="true"
            className="flex size-7 items-center justify-center rounded-sm border border-hairline bg-surface font-mono text-xs font-bold text-foreground"
          >
            {selectedPatient ? (
              initialsOf(selectedPatient.patientName)
            ) : (
              <UserRound className="size-4" />
            )}
          </span>
          <span className="text-sm font-bold">
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
                onSelect={() => void selectPatient(patient.patientId)}
                className="flex cursor-pointer items-center gap-2 rounded-sm px-2 py-2 text-sm font-semibold outline-none data-[highlighted]:bg-surface-muted"
              >
                <UserRound className="size-4 shrink-0" aria-hidden="true" />
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

import { Undo2, X } from "lucide-react";
import { BrutalButton } from "@/components/ui/brutal-button";
import { useAppState } from "@/state/appStateContext";

const UndoBar = () => {
  const { undoLabel, undo, dismissUndo } = useAppState();

  if (!undoLabel) {
    return null;
  }

  return (
    <div
      role="status"
      className="fixed bottom-6 left-1/2 z-40 flex -translate-x-1/2 items-center gap-3 rounded-base border-2 bg-surface px-4 py-3 shadow-brutal-lg"
    >
      <span className="text-sm font-bold">{undoLabel}</span>
      <BrutalButton onClick={undo} size="sm">
        <Undo2 className="size-4" aria-hidden="true" />
        Undo
      </BrutalButton>
      <button
        type="button"
        onClick={dismissUndo}
        aria-label="Dismiss"
        className="inline-flex size-7 cursor-pointer items-center justify-center rounded-sm border border-hairline text-muted-foreground transition-[translate,box-shadow] duration-100 hover:translate-x-0.5 hover:translate-y-0.5 hover:bg-surface-muted hover:shadow-brutal-sm active:translate-x-1 active:translate-y-1 active:shadow-none"
      >
        <X className="size-4" aria-hidden="true" />
      </button>
    </div>
  );
};

export default UndoBar;

import { useEffect, useState } from "react";
import { Keyboard, Video } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { BrutalButton } from "@/components/ui/brutal-button";
import { BrutalDialog } from "@/components/ui/brutal-dialog";
import { Keycap } from "@/components/ui/keycap";
import { useAppState } from "@/state/appStateContext";
import { BINDABLE_KEYS, keyLabel } from "@/lib/keys";
import { ROUTES } from "@/utils/constants";
import { cn } from "@/lib/utils";

type AddBindingDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

const AddBindingDialog = ({ open, onOpenChange }: AddBindingDialogProps) => {
  const navigate = useNavigate();
  const { unboundGestures, bindings, bindGesture } = useAppState();

  const [gestureId, setGestureId] = useState<string | null>(null);
  const [key, setKey] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setGestureId(null);
      setKey(null);
    }
  }, [open]);

  const takenKeys = bindings.map((binding) => binding.key);
  const keyIsTaken = key !== null && takenKeys.includes(key);

  const captureKey = (event: React.KeyboardEvent<HTMLInputElement>) => {
    event.preventDefault();
    if (event.key === "Tab" || event.key === "Escape") {
      return;
    }
    const nextKey =
      event.key.length === 1 ? event.key.toUpperCase() : event.key;
    setKey(nextKey);
  };

  const handleAdd = () => {
    if (gestureId && key) {
      bindGesture(gestureId, key);
      onOpenChange(false);
    }
  };

  return (
    <BrutalDialog
      open={open}
      onOpenChange={onOpenChange}
      title="Add a binding"
      footer={
        <>
          <BrutalButton variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </BrutalButton>
          <BrutalButton
            onClick={handleAdd}
            disabled={!gestureId || !key || keyIsTaken}
          >
            Add binding
          </BrutalButton>
        </>
      }
    >
      <div className="flex flex-col gap-5">
        <section className="flex flex-col gap-2">
          <h3 className="label-caps text-muted-foreground">Movement</h3>

          {unboundGestures.length === 0 ? (
            <div className="flex flex-col items-start gap-3 rounded-sm border border-hairline bg-surface-muted p-4">
              <p className="text-sm font-semibold text-muted-foreground">
                Every movement in your library is already bound.
              </p>
              <BrutalButton
                size="sm"
                onClick={() => {
                  onOpenChange(false);
                  navigate(`${ROUTES.calibrate}?new=1`);
                }}
              >
                <Video aria-hidden="true" />
                Record a new one
              </BrutalButton>
            </div>
          ) : (
            <ul className="flex max-h-48 flex-col gap-1.5 overflow-y-auto">
              {unboundGestures.map((gesture) => {
                const selected = gesture.gestureId === gestureId;
                return (
                  <li key={gesture.gestureId}>
                    <button
                      type="button"
                      aria-pressed={selected}
                      onClick={() => setGestureId(gesture.gestureId)}
                      className={cn(
                        "flex w-full cursor-pointer items-center gap-2 rounded-sm border border-hairline px-3 py-2 text-left text-sm font-bold",
                        selected
                          ? "bg-accent text-accent-foreground"
                          : "bg-surface-muted hover:border-border",
                      )}
                    >
                      <span className="min-w-0 flex-1 truncate">
                        {gesture.name}
                      </span>
                      {!gesture.calibratedAt ? (
                        <span className="text-xs font-bold text-muted-foreground">
                          not recorded
                        </span>
                      ) : null}
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </section>

        <section className="flex flex-col gap-2">
          <h3 className="label-caps text-muted-foreground">Key</h3>
          <label className="flex cursor-text items-center gap-2 rounded-sm border border-hairline bg-surface-muted px-3 py-2 focus-within:outline-3 focus-within:outline-primary">
            <Keyboard className="size-4 shrink-0" aria-hidden="true" />
            <span className="text-sm font-semibold">Press any key</span>
            <input
              value={key ? keyLabel(key) : ""}
              onKeyDown={captureKey}
              onChange={() => undefined}
              placeholder="Click here, then press a key"
              aria-label="Custom key"
              className="min-w-0 flex-1 bg-transparent text-right text-sm font-bold outline-none placeholder:text-placeholder"
            />
          </label>
          {keyIsTaken ? (
            <p className="text-xs font-bold text-destructive">
              That key is already assigned to another movement.
            </p>
          ) : null}
          <p className="text-xs font-semibold text-muted-foreground">
            Or choose a common key:
          </p>
          <div className="flex flex-wrap gap-2">
            {BINDABLE_KEYS.map((option) => {
              const taken = takenKeys.includes(option);
              const selected = option === key;
              return (
                <button
                  key={option}
                  type="button"
                  aria-pressed={selected}
                  aria-label={`${keyLabel(option)}${taken ? " (in use)" : ""}`}
                  disabled={taken}
                  onClick={() => setKey(option)}
                  className={cn(
                    "cursor-pointer rounded-sm border border-hairline p-1 transition-[translate,box-shadow] duration-100",
                    selected
                      ? "bg-accent shadow-brutal-sm"
                      : "bg-surface hover:border-border hover:translate-x-0.5 hover:translate-y-0.5 hover:shadow-brutal-sm active:translate-x-1 active:translate-y-1 active:shadow-none",
                    taken && "cursor-not-allowed opacity-55",
                  )}
                >
                  <Keycap
                    keyName={option}
                    className="border-0 bg-transparent shadow-none"
                  />
                </button>
              );
            })}
          </div>
        </section>
      </div>
    </BrutalDialog>
  );
};

export default AddBindingDialog;

import { DropdownMenu } from "radix-ui";
import { Check, ChevronDown, Keyboard } from "lucide-react";
import { Keycap } from "@/components/ui/keycap";
import { BINDABLE_KEYS, keyLabel } from "@/lib/keys";

type KeyPickerProps = {
  value: string;
  onChange: (key: string) => void;

  takenKeys?: string[];
};

const KeyPicker = ({ value, onChange, takenKeys = [] }: KeyPickerProps) => (
  <DropdownMenu.Root>
    <DropdownMenu.Trigger
      aria-label={`Key: ${keyLabel(value)}. Change`}
      className="flex cursor-pointer items-center gap-1 rounded-sm border border-hairline bg-surface-muted py-1 pr-1.5 pl-1 transition-[translate,box-shadow] duration-100 hover:translate-x-0.5 hover:translate-y-0.5 hover:shadow-brutal-sm active:translate-x-1 active:translate-y-1 active:shadow-none"
    >
      <Keycap keyName={value} size="sm" className="border-0 bg-transparent" />
      <ChevronDown className="size-3.5 shrink-0" aria-hidden="true" />
    </DropdownMenu.Trigger>

    <DropdownMenu.Portal>
      <DropdownMenu.Content
        align="end"
        sideOffset={6}
        className="z-50 w-44 rounded-base border-2 bg-surface p-1.5 shadow-brutal"
      >
        {BINDABLE_KEYS.map((key) => {
          const taken = key !== value && takenKeys.includes(key);
          return (
            <DropdownMenu.Item
              key={key}
              disabled={taken}
              onSelect={() => onChange(key)}
              className="flex cursor-pointer items-center gap-2 rounded-sm px-2 py-1.5 text-sm font-semibold outline-none data-[disabled]:cursor-not-allowed data-[disabled]:opacity-55 data-[highlighted]:bg-surface-muted"
            >
              <Keycap keyName={key} size="sm" />
              <span className="flex-1 truncate">{keyLabel(key)}</span>
              {key === value ? (
                <Check className="size-4 shrink-0" aria-hidden="true" />
              ) : taken ? (
                <span className="text-xs font-bold text-muted-foreground">
                  in use
                </span>
              ) : null}
            </DropdownMenu.Item>
          );
        })}
        <div className="mt-1 border-t border-hairline pt-1">
          <label className="flex items-center gap-2 rounded-sm px-2 py-1.5 text-sm font-semibold focus-within:bg-surface-muted">
            <Keyboard className="size-4" aria-hidden="true" />
            <input
              readOnly
              value=""
              placeholder="Press another key"
              aria-label="Press a custom key"
              onKeyDown={(event) => {
                if (event.key === "Tab" || event.key === "Escape") return;
                event.preventDefault();
                event.stopPropagation();
                const next =
                  event.key.length === 1 ? event.key.toUpperCase() : event.key;
                if (!takenKeys.includes(next) || next === value) onChange(next);
              }}
              className="min-w-0 flex-1 bg-transparent outline-none placeholder:text-placeholder"
            />
          </label>
        </div>
      </DropdownMenu.Content>
    </DropdownMenu.Portal>
  </DropdownMenu.Root>
);

export default KeyPicker;

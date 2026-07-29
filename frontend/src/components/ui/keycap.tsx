import { ArrowDown, ArrowLeft, ArrowRight, ArrowUp } from "lucide-react";
import { cn } from "@/lib/utils";

const arrowIcons = {
  up: ArrowUp,
  down: ArrowDown,
  left: ArrowLeft,
  right: ArrowRight,
  arrowup: ArrowUp,
  arrowdown: ArrowDown,
  arrowleft: ArrowLeft,
  arrowright: ArrowRight,
} as const;

type KeycapProps = {
  keyName: string;
  size?: "sm" | "md" | "lg";
  active?: boolean;
  className?: string;
  "aria-label"?: string;
};

const sizeClasses = {
  sm: "h-7 min-w-7 px-1.5 text-xs",
  md: "h-9 min-w-9 px-2 text-sm",
  lg: "h-14 min-w-14 px-3 text-lg",
} as const;

const Keycap = ({
  keyName,
  size = "md",
  active,
  className,
  "aria-label": ariaLabel,
}: KeycapProps) => {
  const Icon = arrowIcons[keyName.toLowerCase() as keyof typeof arrowIcons];

  return (
    <span
      aria-label={ariaLabel}
      className={cn(
        "inline-flex items-center justify-center rounded-sm border border-hairline font-mono font-bold",
        active
          ? "bg-accent text-accent-foreground shadow-brutal-sm"
          : "bg-surface-muted text-foreground",
        sizeClasses[size],
        className,
      )}
    >
      {Icon ? (
        <Icon className="size-[1.2em]" aria-hidden="true" />
      ) : (
        <span className="truncate">{keyName}</span>
      )}
    </span>
  );
};

export { Keycap };

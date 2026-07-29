import { cn } from "@/lib/utils";

type BrutalMeterProps = {
  value: number;

  threshold?: number;
  tone?: "primary" | "success" | "destructive";
  className?: string;
  "aria-label"?: string;
};

const toneClasses = {
  primary: "bg-primary",
  success: "bg-success",
  destructive: "bg-destructive",
} as const;

const BrutalMeter = ({
  value,
  threshold,
  tone = "primary",
  className,
  "aria-label": ariaLabel,
}: BrutalMeterProps) => {
  const clamped = Math.min(100, Math.max(0, value));

  return (
    <div
      role="meter"
      aria-valuenow={Math.round(clamped)}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={ariaLabel}
      className={cn(
        "relative h-5 w-full overflow-hidden rounded-sm border border-hairline bg-surface-muted",
        className,
      )}
    >
      <div
        className={cn(
          "h-full transition-[width] duration-150",
          toneClasses[tone],
        )}
        style={{ width: `${clamped}%` }}
      />
      {threshold !== undefined ? (
        <span
          aria-hidden="true"
          className="absolute inset-y-0 w-[3px] bg-foreground"
          style={{
            left: `calc(${Math.min(100, Math.max(0, threshold))}% - 1.5px)`,
          }}
        />
      ) : null}
    </div>
  );
};

export { BrutalMeter };

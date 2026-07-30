import * as React from "react";
import { cn } from "@/lib/utils";

type BrutalBadgeProps = React.ComponentProps<"span"> & {
  tone?: "neutral" | "primary" | "accent" | "success" | "destructive";

  dot?: boolean;
};

const toneClasses = {
  neutral: "bg-surface-muted text-foreground",
  primary: "bg-primary text-primary-foreground",
  accent: "bg-accent text-accent-foreground",
  success: "bg-success text-success-foreground",
  destructive: "bg-destructive text-destructive-foreground",
} as const;

const BrutalBadge = ({
  className,
  tone = "neutral",
  dot,
  children,
  ...props
}: BrutalBadgeProps) => (
  <span
    className={cn(
      "inline-flex shrink-0 items-center gap-1.5 rounded-sm border border-hairline px-2 py-0.5 text-xs font-bold whitespace-nowrap",
      toneClasses[tone],
      className,
    )}
    {...props}
  >
    {dot ? (
      <span
        className="size-2 shrink-0 animate-pulse bg-current"
        aria-hidden="true"
      />
    ) : null}
    {children}
  </span>
);

export { BrutalBadge };

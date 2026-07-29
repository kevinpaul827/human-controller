import * as React from "react";
import { cn } from "@/lib/utils";

const BrutalInput = React.forwardRef<
  HTMLInputElement,
  React.ComponentProps<"input">
>(({ className, ...props }, ref) => (
  <input
    ref={ref}
    className={cn(
      "h-11 w-full rounded-base border-2 bg-surface px-3 text-[0.9375rem] font-medium",
      "placeholder:font-normal placeholder:text-placeholder",
      "focus-visible:outline-3 focus-visible:outline-offset-0 focus-visible:outline-primary",
      "disabled:cursor-not-allowed disabled:opacity-55",
      className,
    )}
    {...props}
  />
));
BrutalInput.displayName = "BrutalInput";

const BrutalField = ({
  label,
  htmlFor,
  children,
}: {
  label: string;
  htmlFor: string;
  children: React.ReactNode;
}) => (
  <div className="flex flex-col gap-1.5">
    <label htmlFor={htmlFor} className="label-caps">
      {label}
    </label>
    {children}
  </div>
);

export { BrutalInput, BrutalField };

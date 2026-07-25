import * as React from "react";
import { Slot } from "radix-ui";
import { cn } from "@/lib/utils";

export type BrutalButtonProps = React.ComponentProps<"button"> & {
  variant?: "primary" | "accent" | "success" | "destructive" | "outline";
  size?: "sm" | "md" | "lg";
  asChild?: boolean;
};

const variantClasses: Record<
  NonNullable<BrutalButtonProps["variant"]>,
  string
> = {
  primary: "bg-primary text-primary-foreground",
  accent: "bg-accent text-accent-foreground",
  success: "bg-success text-success-foreground",
  destructive: "bg-destructive text-destructive-foreground",
  outline: "bg-surface text-foreground",
};

const sizeClasses: Record<NonNullable<BrutalButtonProps["size"]>, string> = {
  sm: "h-9 gap-1.5 px-3 text-sm",
  md: "h-11 gap-2 px-4 text-[0.9375rem]",
  lg: "h-13 gap-2 px-6 text-base",
};

const BrutalButton = React.forwardRef<HTMLButtonElement, BrutalButtonProps>(
  ({ className, variant = "primary", size = "md", asChild, ...props }, ref) => {
    const Comp = asChild ? Slot.Root : "button";

    return (
      <Comp
        ref={ref}
        data-slot="brutal-button"
        className={cn(
          "inline-flex shrink-0 cursor-pointer items-center justify-center rounded-base border-2 font-bold whitespace-nowrap",
          "shadow-brutal transition-[translate,box-shadow] duration-100",
          "hover:translate-x-0.5 hover:translate-y-0.5 hover:shadow-brutal-sm",
          "active:translate-x-1 active:translate-y-1 active:shadow-none",
          "disabled:pointer-events-none disabled:opacity-55",
          "[&_svg]:size-[1.1em] [&_svg]:shrink-0",
          variantClasses[variant],
          sizeClasses[size],
          className,
        )}
        {...props}
      />
    );
  },
);
BrutalButton.displayName = "BrutalButton";

export { BrutalButton };

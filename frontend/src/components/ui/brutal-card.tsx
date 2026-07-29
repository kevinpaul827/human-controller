import * as React from "react";
import { cn } from "@/lib/utils";

type DivProps = React.ComponentProps<"div">;

const BrutalCard = ({
  className,
  flat,
  ...props
}: DivProps & { flat?: boolean }) => (
  <div
    data-slot="brutal-card"
    className={cn(
      "flex min-h-0 flex-col rounded-base border-2 bg-surface",
      flat ? "shadow-none" : "shadow-brutal",
      className,
    )}
    {...props}
  />
);

const BrutalCardHeader = ({ className, ...props }: DivProps) => (
  <div
    data-slot="brutal-card-header"
    className={cn(
      "flex shrink-0 flex-wrap items-center justify-between gap-3 border-b border-hairline px-5 py-3.5",
      className,
    )}
    {...props}
  />
);

const BrutalCardTitle = ({
  className,
  ...props
}: React.ComponentProps<"h2">) => (
  <h2
    data-slot="brutal-card-title"
    className={cn("text-lg leading-none font-bold", className)}
    {...props}
  />
);

const BrutalCardDescription = ({
  className,
  ...props
}: React.ComponentProps<"p">) => (
  <p
    className={cn("text-sm font-semibold text-muted-foreground", className)}
    {...props}
  />
);

const BrutalCardContent = ({ className, ...props }: DivProps) => (
  <div
    data-slot="brutal-card-content"
    className={cn("min-h-0 p-5", className)}
    {...props}
  />
);

const BrutalCardFooter = ({ className, ...props }: DivProps) => (
  <div
    data-slot="brutal-card-footer"
    className={cn(
      "flex shrink-0 flex-wrap items-center gap-3 border-t border-hairline px-5 py-3.5",
      className,
    )}
    {...props}
  />
);

export {
  BrutalCard,
  BrutalCardHeader,
  BrutalCardTitle,
  BrutalCardDescription,
  BrutalCardContent,
  BrutalCardFooter,
};

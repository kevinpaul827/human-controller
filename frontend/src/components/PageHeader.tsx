import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

type PageHeaderProps = {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
  children?: ReactNode;
  className?: string;
};

const PageHeader = ({
  eyebrow,
  title,
  description,
  actions,
  children,
  className,
}: PageHeaderProps) => (
  <header className={cn("flex shrink-0 flex-col gap-4", className)}>
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div className="flex min-w-0 flex-col gap-1.5">
        {eyebrow ? (
          <span className="label-caps text-muted-foreground">{eyebrow}</span>
        ) : null}
        <h1 className="text-2xl text-balance sm:text-3xl">{title}</h1>
        {description ? (
          <p className="max-w-prose text-sm font-semibold text-muted-foreground">
            {description}
          </p>
        ) : null}
      </div>
      {actions ? (
        <div className="flex shrink-0 flex-wrap gap-3">{actions}</div>
      ) : null}
    </div>
    {children}
  </header>
);

export default PageHeader;

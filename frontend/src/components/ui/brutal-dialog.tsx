import * as React from "react";
import { Dialog } from "radix-ui";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

type BrutalDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  children?: React.ReactNode;
  footer?: React.ReactNode;
  className?: string;
};

const BrutalDialog = ({
  open,
  onOpenChange,
  title,
  description,
  children,
  footer,
  className,
}: BrutalDialogProps) => (
  <Dialog.Root open={open} onOpenChange={onOpenChange}>
    <Dialog.Portal>
      <Dialog.Overlay className="fixed inset-0 z-50 bg-foreground/40 data-[state=open]:animate-in data-[state=open]:fade-in-0" />
      <Dialog.Content
        className={cn(
          "fixed top-1/2 left-1/2 z-50 flex max-h-[calc(100dvh-3rem)] w-[calc(100vw-2rem)] max-w-lg",
          "-translate-x-1/2 -translate-y-1/2 flex-col rounded-base border-2 bg-surface shadow-brutal-lg",
          "data-[state=open]:animate-in data-[state=open]:zoom-in-95 data-[state=open]:fade-in-0",
          className,
        )}
      >
        <div className="flex shrink-0 items-start justify-between gap-4 border-b border-hairline px-5 py-4">
          <div className="flex flex-col gap-1">
            <Dialog.Title className="text-lg font-bold">{title}</Dialog.Title>
            {description ? (
              <Dialog.Description className="text-sm font-semibold text-muted-foreground">
                {description}
              </Dialog.Description>
            ) : null}
          </div>
          <Dialog.Close
            aria-label="Close"
            className="inline-flex size-8 shrink-0 cursor-pointer items-center justify-center rounded-sm border border-hairline bg-surface transition-[translate,box-shadow] duration-100 hover:translate-x-0.5 hover:translate-y-0.5 hover:shadow-brutal-sm hover:bg-destructive hover:text-destructive-foreground active:translate-x-1 active:translate-y-1 active:shadow-none"
          >
            <X className="size-4" aria-hidden="true" />
          </Dialog.Close>
        </div>

        {children ? (
          <div className="min-h-0 flex-1 overflow-y-auto p-5">{children}</div>
        ) : null}

        {footer ? (
          <div className="flex shrink-0 flex-wrap justify-end gap-3 border-t border-hairline px-5 py-4">
            {footer}
          </div>
        ) : null}
      </Dialog.Content>
    </Dialog.Portal>
  </Dialog.Root>
);

export { BrutalDialog };

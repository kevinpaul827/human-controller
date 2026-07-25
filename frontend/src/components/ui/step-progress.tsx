import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

type StepProgressProps = {
  steps: readonly string[];
  currentStep: number;
  className?: string;
};

const StepProgress = ({ steps, currentStep, className }: StepProgressProps) => (
  <ol
    className={cn("flex w-full items-stretch gap-2", className)}
    aria-label={`Step ${currentStep} of ${steps.length}`}
  >
    {steps.map((label, index) => {
      const stepNumber = index + 1;
      const isComplete = stepNumber < currentStep;
      const isCurrent = stepNumber === currentStep;

      return (
        <li
          key={label}
          aria-current={isCurrent ? "step" : undefined}
          className={cn(
            "flex min-w-0 flex-1 items-center gap-2 rounded-sm border border-hairline px-2.5 py-2",
            isCurrent && "bg-accent text-accent-foreground",
            isComplete && "bg-success text-success-foreground",
            !isCurrent && !isComplete && "bg-surface text-muted-foreground",
          )}
        >
          <span
            className={cn(
              "flex size-6 shrink-0 items-center justify-center rounded-sm border border-current font-mono text-xs font-bold",
              isCurrent || isComplete ? "bg-transparent" : "bg-surface-muted",
            )}
          >
            {isComplete ? (
              <Check className="size-3.5" aria-hidden="true" />
            ) : (
              stepNumber
            )}
          </span>
          <span className="hidden truncate text-sm font-bold sm:block">
            {label}
          </span>
        </li>
      );
    })}
  </ol>
);

export { StepProgress };

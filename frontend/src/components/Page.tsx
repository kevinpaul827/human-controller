import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

type PageProps = {
  children: ReactNode;

  variant?: "scroll" | "fixed";
  width?: "default" | "wide";
  className?: string;
};

const Page = ({
  children,
  variant = "scroll",
  width = "default",
  className,
}: PageProps) => (
  <div
    className={cn(
      "mx-auto flex w-full flex-col gap-6 p-5 sm:p-6 lg:p-8",
      width === "wide" ? "max-w-[1600px]" : "max-w-6xl",
      variant === "fixed" && "lg:h-full lg:min-h-0 lg:overflow-hidden",
      className,
    )}
  >
    {children}
  </div>
);

export default Page;

import * as React from "react";
import { cn } from "@/lib/utils";

export function Textarea({ className, ...props }: React.ComponentProps<"textarea">) {
  return (
    <textarea
      className={cn(
        "flex min-h-24 w-full rounded-sm bg-bg px-3 py-2 text-sm text-fg shadow-[0_0_0_1px_rgba(214,230,255,0.14)] outline-none placeholder:text-subtle focus-visible:shadow-[0_0_0_2px_rgba(58,116,212,0.7)]",
        className,
      )}
      {...props}
    />
  );
}

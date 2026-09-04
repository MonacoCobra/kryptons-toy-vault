import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-sm font-medium select-none outline-none focus-visible:ring-2 focus-visible:ring-shield-bright/70 disabled:pointer-events-none disabled:opacity-40 active:not-disabled:scale-[0.96] transition-[scale,background-color,color,box-shadow] duration-150 ease-out [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-fg hover:bg-primary-hover shadow-[0_0_0_1px_rgba(255,255,255,0.08)]",
        secondary:
          "bg-surface text-fg shadow-[0_0_0_1px_rgba(214,230,255,0.12)] hover:bg-surface-2",
        outline:
          "bg-transparent text-fg shadow-[0_0_0_1px_rgba(214,230,255,0.16)] hover:bg-surface",
        ghost: "bg-transparent text-fg hover:bg-surface",
        gold: "bg-gold text-gold-fg hover:brightness-95",
        danger: "bg-primary-dim text-primary-fg hover:bg-primary",
      },
      size: {
        default: "h-11 px-4 text-sm",
        sm: "h-9 px-3 text-sm",
        lg: "h-12 px-5 text-base",
        icon: "size-11",
        "icon-sm": "size-9",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  },
);

export function Button({
  className,
  variant,
  size,
  asChild = false,
  ...props
}: React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & { asChild?: boolean }) {
  const Comp = asChild ? Slot : "button";
  return (
    <Comp className={cn(buttonVariants({ variant, size }), className)} {...props} />
  );
}

export { buttonVariants };

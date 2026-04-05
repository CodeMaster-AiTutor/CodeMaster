import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary text-primary-foreground hover:bg-primary/80",
        secondary: "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
        destructive: "border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80",
        outline: "text-foreground",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof badgeVariants> {}

const readText = (node: React.ReactNode): string => {
  if (typeof node === "string" || typeof node === "number") {
    return String(node);
  }
  if (Array.isArray(node)) {
    return node.map(readText).join(" ");
  }
  if (React.isValidElement(node)) {
    return readText(node.props.children);
  }
  return "";
};

const getLevelBadgeClass = (children: React.ReactNode) => {
  const label = readText(children).toLowerCase();
  if (label.includes("beginner")) {
    return "border-emerald-500/50 bg-emerald-500/15 text-emerald-400 hover:bg-emerald-500/20";
  }
  if (label.includes("intermediate")) {
    return "border-amber-500/50 bg-amber-500/15 text-amber-400 hover:bg-amber-500/20";
  }
  if (label.includes("advanced") || label.includes("advance")) {
    return "border-rose-500/50 bg-rose-500/15 text-rose-400 hover:bg-rose-500/20";
  }
  return "";
};

function Badge({ className, variant, children, ...props }: BadgeProps) {
  const levelClass = getLevelBadgeClass(children);
  return (
    <div className={cn(badgeVariants({ variant }), levelClass, className)} {...props}>
      {children}
    </div>
  );
}

export { Badge, badgeVariants };

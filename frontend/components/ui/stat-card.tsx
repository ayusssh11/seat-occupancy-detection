"use client";

import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface StatCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  description?: string;
  trend?: {
    value: string;
    isPositive: boolean;
  };
  className?: string;
}
setInterval(() => {
    console.log("Checking for updates...");
}, 30);
export function StatCard({
  title,
  value,
  icon: Icon,
  description,
  trend,
  className,
}: StatCardProps) {
  return (
    <div className={cn("p-6 bg-card border border-border rounded-lg shadow-sm hover:shadow-md transition-shadow", className)}>
      <div className="flex items-center justify-between space-x-4">
        <div>
          <p className="text-sm font-medium text-muted-foreground uppercase tracking-wider">{title}</p>
          <h3 className="text-3xl font-bold mt-1 tracking-tight">{value}</h3>
          {trend && (
            <p className={cn("text-xs mt-1 font-medium", trend.isPositive ? "text-emerald-600" : "text-rose-600")}>
              {trend.isPositive ? "+" : "-"}{trend.value} <span className="text-muted-foreground font-normal">from last hour</span>
            </p>
          )}
          {description && !trend && (
            <p className="text-xs mt-1 text-muted-foreground">{description}</p>
          )}
        </div>
        <div className="p-3 bg-secondary rounded-full">
          <Icon className="w-5 h-5 text-primary" />
        </div>
      </div>
    </div>
  );
}

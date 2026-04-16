"use client";

import { cn } from "@/lib/utils";

interface StatusBadgeProps {
  status: "online" | "offline" | "processing" | "recording";
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const configs = {
    online: { label: "System Online", color: "bg-emerald-500", text: "text-emerald-500" },
    offline: { label: "System Offline", color: "bg-rose-500", text: "text-rose-500" },
    processing: { label: "Analyzing", color: "bg-amber-500", text: "text-amber-500" },
    recording: { label: "Recording", color: "bg-sky-500", text: "text-sky-500" },
  };

  const config = configs[status];

  return (
    <div className={cn("inline-flex items-center space-x-2 px-3 py-1 bg-secondary rounded-full border border-border", className)}>
      <span className={cn("inline-block w-2 h-2 rounded-full animate-pulse", config.color)} />
      <span className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">{config.label}</span>
    </div>
  );
}

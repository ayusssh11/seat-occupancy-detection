"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Monitor, Settings, BarChart3, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

const navigation = [
  { name: "Overview", href: "/", icon: LayoutDashboard },
  { name: "Live Monitor", href: "/monitor", icon: Monitor },
  { name: "Analytics", href: "/analytics", icon: BarChart3 },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="w-64 border-r border-border h-screen bg-card sticky top-0 flex flex-col pt-8">
      <div className="px-6 mb-10">
        <h1 className="text-xl font-bold tracking-tighter text-primary flex items-center space-x-2">
          <div className="w-6 h-6 bg-primary rounded flex items-center justify-center">
            <div className="w-3 h-3 bg-background rounded-sm" />
          </div>
          <span>OCU-STREAM</span>
        </h1>
        <p className="text-[10px] uppercase font-bold text-muted-foreground mt-1 tracking-[0.2em]">
          Smart Occupancy Tech
        </p>
      </div>

      <nav className="flex-1 px-4 space-y-1">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "group flex items-center justify-between px-3 py-2 text-sm font-medium rounded-md transition-colors",
                isActive 
                  ? "bg-primary text-primary-foreground" 
                  : "text-muted-foreground hover:bg-secondary hover:text-primary"
              )}
            >
              <div className="flex items-center space-x-3">
                <item.icon className="w-4 h-4" />
                <span>{item.name}</span>
              </div>
              {isActive && <ChevronRight className="w-4 h-4 opacity-50" />}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-border">
        <div className="flex items-center space-x-3 px-3 py-2 bg-secondary rounded-md">
          <div className="w-8 h-8 rounded-full bg-slate-300" />
          <div>
            <p className="text-xs font-bold leading-none">Admin Station</p>
            <p className="text-[10px] text-muted-foreground mt-1">v.2.0.4 - Premium</p>
          </div>
        </div>
      </div>
    </div>
  );
}

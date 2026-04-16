"use client";

import { StatusBadge } from "@/components/ui/status-badge";
import { Search, Bell, Calendar } from "lucide-react";

export function Header() {
  const today = new Date().toLocaleDateString('en-US', { 
    weekday: 'long', 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric' 
  });

  return (
    <header className="h-20 border-b border-border bg-white flex items-center justify-between px-8">
      <div className="flex items-center space-x-4">
        <StatusBadge status="online" />
        <div className="h-4 w-px bg-border mx-2" />
        <div className="flex items-center space-x-2 text-muted-foreground">
          <Calendar className="w-4 h-4" />
          <span className="text-xs font-medium">{today}</span>
        </div>
      </div>

      <div className="flex items-center space-x-6">
        <div className="relative">
          <Search className="w-4 h-4 text-muted-foreground absolute left-3 top-1/2 -translate-y-1/2" />
          <input 
            type="text" 
            placeholder="Search metrics..." 
            className="pl-10 pr-4 py-2 bg-secondary border-none rounded-md text-xs w-64 focus:ring-1 focus:ring-primary transition-all"
          />
        </div>
        
        <button className="relative p-2 hover:bg-secondary rounded-full transition-colors">
          <Bell className="w-4 h-4 text-muted-foreground" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-rose-500 rounded-full border-2 border-white" />
        </button>
        
        <div className="flex items-center space-x-3 border-l border-border pl-6">
          <div className="text-right">
            <p className="text-sm font-bold leading-none">Ayush Chauhan</p>
            <p className="text-[10px] text-muted-foreground mt-1 uppercase tracking-tighter">Site Manager</p>
          </div>
          <div className="w-9 h-9 rounded-lg bg-primary flex items-center justify-center text-primary-foreground font-bold text-xs">
            AC
          </div>
        </div>
      </div>
    </header>
  );
}

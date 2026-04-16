"use client";

import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { useOccupancyStats } from "@/lib/hooks/use-occupancy-stats";
import { Maximize2, Minimize2, Settings, Shield, Target } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

export default function MonitorPage() {
  const { stats, isOnline } = useOccupancyStats();
  const [isFullscreen, setIsFullscreen] = useState(false);
  const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

  return (
    <div className="flex h-screen bg-background text-foreground">
      {!isFullscreen && <Sidebar />}
      <div className="flex-1 flex flex-col overflow-hidden">
        {!isFullscreen && <Header />}
        
        <main className={cn("flex-1 bg-slate-950 flex flex-col relative", isFullscreen ? "p-0" : "p-8")}>
          {/* Header Controls */}
          <div className="absolute top-12 left-12 z-20 flex flex-col space-y-1">
            <h2 className="text-white text-2xl font-bold tracking-tight drop-shadow-lg">
              Live Security Feed
            </h2>
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-1.5 px-2 py-0.5 bg-emerald-500/20 border border-emerald-500/30 rounded text-emerald-400 text-[10px] font-bold uppercase tracking-wider">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                <span>Live Stream</span>
              </div>
              <span className="text-white/40 text-[10px] font-bold uppercase tracking-widest">
                Cam: Internal_04_A
              </span>
            </div>
          </div>

          <div className="absolute top-12 right-12 z-20 flex items-center space-x-3">
            <button 
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="p-3 bg-white/10 hover:bg-white/20 backdrop-blur-md rounded-full text-white transition-all border border-white/10"
            >
              {isFullscreen ? <Minimize2 className="w-5 h-5" /> : <Maximize2 className="w-5 h-5" />}
            </button>
            <button className="p-3 bg-white/10 hover:bg-white/20 backdrop-blur-md rounded-full text-white transition-all border border-white/10">
              <Settings className="w-5 h-5" />
            </button>
          </div>

          {/* Main Feed */}
          <div className="flex-1 relative rounded-2xl overflow-hidden shadow-2xl border border-white/5 bg-slate-900 group">
            <img 
              src={`${BACKEND_URL}/video_feed`} 
              alt="Live Feed" 
              className="w-full h-full object-contain"
            />

            {/* AI HUD Overlay */}
            <div className="absolute inset-0 pointer-events-none p-12 flex flex-col justify-end">
              <div className="grid grid-cols-3 gap-12 w-full max-w-4xl mx-auto mb-8 opacity-0 group-hover:opacity-100 transition-opacity duration-700">
                <div className="flex flex-col space-y-1 p-4 bg-black/40 backdrop-blur-xl border border-white/10 rounded-xl">
                  <span className="text-[10px] font-bold text-white/40 uppercase tracking-[.2em]">Occupancy</span>
                  <div className="flex items-end space-x-2">
                    <span className="text-3xl font-bold text-white leading-none">{stats?.occupied_count || 0}</span>
                    <span className="text-sm font-bold text-white/40 pb-0.5">/ {stats?.total_seats || 0} SEATS</span>
                  </div>
                </div>
                
                <div className="flex flex-col space-y-1 p-4 bg-black/40 backdrop-blur-xl border border-white/10 rounded-xl">
                  <span className="text-[10px] font-bold text-white/40 uppercase tracking-[.2em]">Detection</span>
                  <div className="flex items-end space-x-2">
                    <span className="text-3xl font-bold text-white leading-none">{stats?.persons_detected || 0}</span>
                    <span className="text-sm font-bold text-white/40 pb-0.5 whitespace-nowrap">PERSONS FOUND</span>
                  </div>
                </div>

                <div className="flex flex-col space-y-1 p-4 bg-black/40 backdrop-blur-xl border border-white/10 rounded-xl">
                  <span className="text-[10px] font-bold text-white/40 uppercase tracking-[.2em]">Efficiency</span>
                  <div className="flex items-end space-x-2">
                    <span className="text-3xl font-bold text-white leading-none">{stats?.occupancy_rate.toFixed(0) || 0}</span>
                    <span className="text-sm font-bold text-white/40 pb-0.5">% LOAD</span>
                  </div>
                </div>
              </div>

              {/* HUD Decorations */}
              <div className="absolute top-0 left-0 w-32 h-32 border-l border-t border-white/20 rounded-tl-3xl m-12 pointer-events-none" />
              <div className="absolute top-0 right-0 w-32 h-32 border-r border-t border-white/20 rounded-tr-3xl m-12 pointer-events-none" />
              <div className="absolute bottom-0 left-0 w-32 h-32 border-l border-b border-white/20 rounded-bl-3xl m-12 pointer-events-none" />
              <div className="absolute bottom-0 right-0 w-32 h-32 border-r border-b border-white/20 rounded-br-3xl m-12 pointer-events-none" />
            </div>
            
            {/* System Info */}
            <div className="absolute bottom-12 right-12 z-20 flex items-center space-x-6">
              <div className="flex items-center space-x-2">
                <Shield className="w-4 h-4 text-emerald-400" />
                <span className="text-[10px] font-bold text-white/60 uppercase tracking-widest">Protocol Active</span>
              </div>
              <div className="flex items-center space-x-2">
                <Target className="w-4 h-4 text-sky-400" />
                <span className="text-[10px] font-bold text-white/60 uppercase tracking-widest">YOLOv5S Online</span>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

"use client";

import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { StatCard } from "@/components/ui/stat-card";
import { useOccupancyStats } from "@/lib/hooks/use-occupancy-stats";
import { Users, Armchair, Percent, Activity, Camera, Play, VideoOff } from "lucide-react";
import { cn } from "@/lib/utils";
import { useState, useEffect } from "react";

export default function Dashboard() {
  const { stats, isOnline, error } = useOccupancyStats();
  const [isRecording, setIsRecording] = useState(false);
  const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

  const toggleRecording = async () => {
    const endpoint = isRecording ? "/api/recording/stop" : "/api/recording/start";
    try {
      const response = await fetch(`${BACKEND_URL}${endpoint}`, { method: "POST" });
      const data = await response.json();
      if (data.success) {
        setIsRecording(!isRecording);
      } else {
        console.error("Recording action failed:", data.message);
      }
    } catch (err) {
      console.error("Failed to toggle recording:", err);
    }
  };

  const displayStats = stats || {
    occupied_count: 0,
    total_seats: 0,
    occupancy_rate: 0,
    persons_detected: 0,
    timestamp: new Date().toISOString()
  };

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        
        <main className="flex-1 overflow-y-auto p-8 space-y-8">
          {/* Metrics Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatCard 
              title="Occupied Seats" 
              value={displayStats.occupied_count}
              icon={Armchair}
              trend={{ value: "12%", isPositive: true }}
            />
            <StatCard 
              title="Available" 
              value={displayStats.total_seats - displayStats.occupied_count}
              icon={Users}
              className="border-slate-100"
            />
            <StatCard 
              title="Occupancy Rate" 
              value={`${displayStats.occupancy_rate.toFixed(1)}%`}
              icon={Percent}
            />
            <StatCard 
              title="Persons Detected" 
              value={displayStats.persons_detected}
              icon={Activity}
            />
          </div>

          {/* Main Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 h-[600px]">
            {/* Live Feed Container */}
            <div className="lg:col-span-8 flex flex-col space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Camera className="w-5 h-5 text-primary" />
                  <h2 className="text-lg font-bold tracking-tight">System Monitor 01</h2>
                  <span className="px-2 py-0.5 bg-emerald-100 text-emerald-700 text-[10px] font-bold rounded uppercase">Active</span>
                </div>
                <div className="flex items-center space-x-2">
                  <button 
                    onClick={toggleRecording}
                    className={cn(
                      "flex items-center space-x-2 px-4 py-2 rounded-md text-sm font-medium transition-all shadow-sm",
                      isRecording 
                        ? "bg-rose-50 text-rose-600 hover:bg-rose-100 border border-rose-200" 
                        : "bg-primary text-primary-foreground hover:bg-slate-800"
                    )}
                  >
                    {isRecording ? (
                      <>
                         <VideoOff className="w-4 h-4" />
                         <span>Stop Recording</span>
                      </>
                    ) : (
                      <>
                        <Play className="w-4 h-4 fill-current" />
                        <span>Start Recording</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
              
              <div className="relative flex-1 bg-black rounded-xl overflow-hidden shadow-lg border border-border group">
                {/* Video Feed Image */}
                <img 
                  src={`${BACKEND_URL}/video_feed`} 
                  alt="Live Room Feed" 
                  className="w-full h-full object-cover opacity-90"
                  onError={(e) => {
                    const target = e.target as HTMLImageElement;
                    target.style.display = 'none';
                    target.parentElement?.querySelector('.error-overlay')?.classList.remove('hidden');
                  }}
                />
                
                {/* Error Overlay */}
                <div className="error-overlay hidden absolute inset-0 flex flex-col items-center justify-center bg-slate-900/90 text-white p-6 text-center">
                  <VideoOff className="w-12 h-12 text-slate-500 mb-4" />
                  <h3 className="text-lg font-bold">Camera Feed Offline</h3>
                  <p className="text-sm text-slate-400 max-w-xs mt-2">
                    Unable to connect to the video stream at {BACKEND_URL}. Ensure the Flask backend is running.
                  </p>
                </div>

                {/* Overlays */}
                <div className="absolute top-4 right-4 bg-black/50 backdrop-blur-md px-3 py-1.5 rounded-full border border-white/20">
                  <p className="text-[10px] font-mono text-white tracking-widest uppercase">
                    REC: {new Date().toLocaleTimeString()}
                  </p>
                </div>
              </div>
            </div>

            {/* Seat Map Sidebar */}
            <div className="lg:col-span-4 flex flex-col space-y-4">
              <div className="flex items-center space-x-2">
                <LayoutDashboard className="w-5 h-5 text-primary" />
                <h2 className="text-lg font-bold tracking-tight">Seat Layout</h2>
              </div>
              
              <div className="flex-1 bg-card border border-border rounded-xl p-6 shadow-sm overflow-hidden flex flex-col">
                <div className="mb-6">
                  <div className="flex items-center justify-between text-xs font-bold text-muted-foreground uppercase tracking-wider mb-4">
                    <span>Floor Phase A</span>
                    <span className="text-primary">{displayStats.occupied_count}/{displayStats.total_seats} Seats</span>
                  </div>
                  <div className="w-full h-2 bg-secondary rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-primary transition-all duration-500" 
                      style={{ width: `${displayStats.occupancy_rate}%` }}
                    />
                  </div>
                </div>

                {/* Seat Visualization Grid */}
                <div className="grid grid-cols-4 gap-4 flex-1 content-start py-4">
                  {Array.from({ length: displayStats.total_seats || 12 }).map((_, i) => {
                    const seatName = `seat_${i + 1}`;
                    const isOccupied = stats?.occupied_seats.includes(seatName);
                    return (
                      <div 
                        key={seatName}
                        className={cn(
                          "aspect-square rounded-lg flex flex-col items-center justify-center transition-all border shadow-sm",
                          isOccupied 
                            ? "bg-primary text-primary-foreground border-primary" 
                            : "bg-white text-muted-foreground border-border hover:border-slate-300"
                        )}
                      >
                        <Armchair className={cn("w-6 h-6 mb-1", isOccupied ? "animate-pulse" : "opacity-40")} />
                        <span className="text-[10px] font-bold">S{i + 1}</span>
                      </div>
                    );
                  })}
                </div>

                <div className="mt-6 pt-6 border-t border-border flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 rounded-full bg-primary" />
                    <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Occupied</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 rounded-full bg-border border" />
                    <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Available</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

setInterval(() => {
    console.log("Checking for updates...");
}, 30); 


// Minimal missing component for the import
import { LayoutDashboard } from "lucide-react";

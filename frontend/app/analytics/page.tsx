"use client";

import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { useOccupancyStats } from "@/lib/hooks/use-occupancy-stats";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { BarChart3, TrendingUp, Users, Clock } from "lucide-react";
import { useEffect, useState } from "react";

// Mock history for visualization
const generateMockHistory = () => {
  return Array.from({ length: 24 }).map((_, i) => ({
    time: `${i}:00`,
    occupancy: Math.floor(Math.random() * 40) + 20,
    persons: Math.floor(Math.random() * 10) + 5
  }));
};

export default function AnalyticsPage() {
  const { stats } = useOccupancyStats();
  const [history, setHistory] = useState(generateMockHistory());

  // Update history with real data point if stats change
  useEffect(() => {
    if (stats) {
      const now = new Date();
      const timeStr = `${now.getHours()}:${now.getMinutes()}`;
      setHistory(prev => [...prev.slice(1), { 
        time: timeStr, 
        occupancy: stats.occupancy_rate,
        persons: stats.persons_detected
      }]);
    }
  }, [stats]);

  return (
    <div className="flex h-screen bg-background text-foreground">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        
        <main className="flex-1 overflow-y-auto p-8 space-y-8">
          <div className="flex flex-col space-y-2">
            <h2 className="text-3xl font-bold tracking-tight">Analytics Overview</h2>
            <p className="text-muted-foreground">Historical data and occupancy trend analysis.</p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 bg-card border border-border rounded-xl p-6 shadow-sm">
              <div className="flex items-center justify-between mb-8">
                <div className="flex items-center space-x-2">
                  <TrendingUp className="w-5 h-5 text-primary" />
                  <h3 className="text-sm font-bold uppercase tracking-widest text-muted-foreground">Occupancy Rate (%)</h3>
                </div>
                <div className="flex items-center space-x-2 text-xs font-medium text-emerald-600 bg-emerald-50 px-2 py-1 rounded">
                  <TrendingUp className="w-3 h-3" />
                  <span>+4.2% today</span>
                </div>
              </div>
              
              <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={history}>
                    <defs>
                      <linearGradient id="colorOcc" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#0f172a" stopOpacity={0.1}/>
                        <stop offset="95%" stopColor="#0f172a" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis dataKey="time" axisLine={false} tickLine={false} tick={{fontSize: 10, fill: '#64748b'}} />
                    <YAxis axisLine={false} tickLine={false} tick={{fontSize: 10, fill: '#64748b'}} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                      labelStyle={{ fontSize: '10px', fontWeight: 'bold', color: '#64748b' }}
                    />
                    <Area type="monotone" dataKey="occupancy" stroke="#0f172a" strokeWidth={2} fillOpacity={1} fill="url(#colorOcc)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="flex flex-col space-y-6">
              <div className="bg-primary text-primary-foreground rounded-xl p-6 shadow-lg">
                <div className="flex items-center space-x-2 mb-4">
                  <Clock className="w-5 h-5 opacity-70" />
                  <h3 className="text-xs font-bold uppercase tracking-widest opacity-70">Peak Occupancy</h3>
                </div>
                <p className="text-4xl font-bold tracking-tighter">14:45</p>
                <p className="text-xs mt-2 opacity-70 italic">Usually occurs on Tuesdays and Thursdays</p>
              </div>

              <div className="bg-card border border-border rounded-xl p-6 shadow-sm flex-1">
                <div className="flex items-center space-x-2 mb-6">
                  <Users className="w-5 h-5 text-primary" />
                  <h3 className="text-sm font-bold uppercase tracking-widest text-muted-foreground">Detection Velocity</h3>
                </div>
                <div className="h-[180px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={history.slice(-12)}>
                      <XAxis dataKey="time" hide />
                      <Bar dataKey="persons" fill="#0f172a" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <p className="text-xs text-center text-muted-foreground mt-4">Last 12 detection cycles (Person counts)</p>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

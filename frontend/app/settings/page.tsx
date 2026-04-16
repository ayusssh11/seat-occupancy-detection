"use client";

import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Settings, Shield, RefreshCw, Save, Camera, Database, Sliders } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

export default function SettingsPage() {
  const [isCalibrating, setIsCalibrating] = useState(false);
  const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

  const handleAutoCalibrate = async () => {
    setIsCalibrating(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/calibrate/auto`, { method: 'POST' });
      const data = await response.json();
      alert(data.message || "Manual Calibration Triggered");
    } catch (err) {
      console.error(err);
      alert("Failed to connect to backend");
    } finally {
      setIsCalibrating(false);
    }
  };

  return (
    <div className="flex h-screen bg-background text-foreground">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        
        <main className="flex-1 overflow-y-auto p-8 max-w-5xl mx-auto w-full space-y-8">
          <div className="flex flex-col space-y-2">
            <h2 className="text-3xl font-bold tracking-tight">System Settings</h2>
            <p className="text-muted-foreground">Manage your hardware configuration and detection protocols.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="md:col-span-1">
              <h3 className="text-lg font-bold mb-1">Calibration</h3>
              <p className="text-sm text-muted-foreground">Configure how seats are identified and mapped.</p>
            </div>
            
            <div className="md:col-span-2 space-y-4">
              <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-secondary rounded-lg">
                      <Camera className="w-5 h-5" />
                    </div>
                    <div>
                      <p className="text-sm font-bold">Auto-Calibration</p>
                      <p className="text-xs text-muted-foreground">Uses AI to detect empty chairs automatically.</p>
                    </div>
                  </div>
                  <button 
                    onClick={handleAutoCalibrate}
                    disabled={isCalibrating}
                    className={cn(
                      "px-4 py-2 rounded-md text-sm font-medium transition-all",
                      isCalibrating ? "bg-muted text-muted-foreground" : "bg-primary text-primary-foreground hover:bg-slate-800"
                    )}
                  >
                    {isCalibrating ? (
                      <RefreshCw className="w-4 h-4 animate-spin" />
                    ) : (
                      "Start Auto-Detection"
                    )}
                  </button>
                </div>
                
                <div className="h-px bg-border mb-6" />
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-secondary rounded-lg">
                      <Sliders className="w-5 h-5" />
                    </div>
                    <div>
                      <p className="text-sm font-bold">Manual Mapping</p>
                      <p className="text-xs text-muted-foreground">Draw seat boundaries for maximum precision.</p>
                    </div>
                  </div>
                  <button className="px-4 py-2 border border-border rounded-md text-sm font-medium hover:bg-secondary transition-all">
                    Open Editor
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 pt-8 border-t border-border">
            <div className="md:col-span-1">
              <h3 className="text-lg font-bold mb-1">System Health</h3>
              <p className="text-sm text-muted-foreground">Global parameters and storage management.</p>
            </div>
            
            <div className="md:col-span-2 space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-secondary/50 rounded-lg border border-border">
                  <div className="flex items-center space-x-3">
                    <Shield className="w-5 h-5 text-muted-foreground" />
                    <span className="text-sm font-medium">Auto-Restart on Error</span>
                  </div>
                  <div className="w-10 h-5 bg-emerald-500 rounded-full relative">
                    <div className="absolute top-1 right-1 w-3 h-3 bg-white rounded-full shadow-sm" />
                  </div>
                </div>

                <div className="flex items-center justify-between p-4 bg-secondary/50 rounded-lg border border-border">
                  <div className="flex items-center space-x-3">
                    <Database className="w-5 h-5 text-muted-foreground" />
                    <span className="text-sm font-medium">Log Retention (Days)</span>
                  </div>
                  <input type="number" defaultValue={30} className="w-16 bg-white border border-border rounded p-1 text-sm text-center" />
                </div>
              </div>

              <div className="flex justify-end pt-4">
                <button className="flex items-center space-x-2 px-6 py-2.5 bg-primary text-primary-foreground rounded-lg font-bold text-sm shadow-md hover:shadow-lg transition-all">
                  <Save className="w-4 h-4" />
                  <span>Save Configuration</span>
                </button>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

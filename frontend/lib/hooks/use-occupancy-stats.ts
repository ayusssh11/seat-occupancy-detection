"use client";

import { useState, useEffect } from "react";

export interface OccupancyStats {
  occupied_seats: string[];
  empty_seats: string[];
  total_seats: number;
  occupied_count: number;
  occupancy_rate: number;
  persons_detected: number;
  timestamp: string;
}

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

export function useOccupancyStats() {
  const [stats, setStats] = useState<OccupancyStats | null>(null);
  const [isOnline, setIsOnline] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let eventSource: EventSource | null = null;

    const connect = () => {
      eventSource = new EventSource(`${BACKEND_URL}/api/stream`);

      eventSource.onopen = () => {
        setIsOnline(true);
        setError(null);
      };

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setStats({
            ...data,
            timestamp: new Date().toISOString()
          });
        } catch (err) {
          console.error("Failed to parse SSE data", err);
        }
      };

      eventSource.onerror = (err) => {
        console.error("EventSource failed:", err);
        setIsOnline(false);
        setError("Connection lost. Retrying...");
        eventSource?.close();
        
        // Retry after 5 seconds
        setTimeout(connect, 5000);
      };
    };

    connect();

    return () => {
      eventSource?.close();
    };
  }, []);

  return { stats, isOnline, error };
}

"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { Activity, RotateCcw, Loader2, Target, Zap } from "lucide-react";

interface PostureStats {
    fps: number;
    connected: boolean;
    calibrating: boolean;
    calibration_progress: number;
    is_turning: boolean;
    active_skills: Record<string, boolean>;
    active_events: Record<string, boolean>;
    metrics: Record<string, number | string>;
    trigger_counts: Record<string, number>;
}

interface StatsDisplayProps {
    className?: string;
}

export function StatsDisplay({ className }: StatsDisplayProps) {
    const [stats, setStats] = useState<PostureStats>({
        fps: 0,
        connected: false,
        calibrating: false,
        calibration_progress: 0,
        is_turning: false,
        active_skills: {},
        active_events: {},
        metrics: {},
        trigger_counts: {},
    });

    const fetchStats = useCallback(async () => {
        try {
            const res = await fetch("http://localhost:5001/status", {
                signal: AbortSignal.timeout(2000),
            });
            if (res.ok) {
                const data = await res.json();
                setStats(data);
            }
        } catch {
            setStats((prev) => ({ ...prev, connected: false }));
        }
    }, []);

    useEffect(() => {
        fetchStats();
        const interval = setInterval(fetchStats, 200);
        return () => clearInterval(interval);
    }, [fetchStats]);

    if (stats.calibrating && stats.connected) {
        return (
            <div className={cn("space-y-4", className)}>
                <div className="flex flex-col items-center justify-center p-6 rounded-xl bg-violet-500/10 border border-violet-500/30">
                    <motion.div animate={{ rotate: 360 }} transition={{ duration: 2, repeat: Infinity, ease: "linear" }} className="mb-4">
                        <Loader2 className="w-10 h-10 text-violet-400" />
                    </motion.div>
                    <p className="text-violet-300 font-semibold mb-2">校準中...</p>
                    <p className="text-violet-400/70 text-sm text-center mb-4">請正視前方保持不動</p>
                    <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
                        <motion.div className="h-full bg-gradient-to-r from-violet-500 to-indigo-500" animate={{ width: `${stats.calibration_progress}%` }} transition={{ duration: 0.2 }} />
                    </div>
                    <p className="text-violet-400 text-sm mt-2">{stats.calibration_progress}%</p>
                </div>
            </div>
        );
    }

    return (
        <div className={cn("space-y-4", className)}>
            <AnimatePresence>
                {stats.is_turning && (
                    <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="flex items-center gap-3 p-3 rounded-xl bg-amber-500/10 border border-amber-500/30">
                        <RotateCcw className="w-4 h-4 text-amber-400" />
                        <p className="text-amber-400 text-sm">頭部轉動中 - 暫停偵測</p>
                    </motion.div>
                )}
            </AnimatePresence>

            <div className="grid grid-cols-2 gap-3">
                <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/50">
                    <div className="flex items-center gap-2 mb-2">
                        <Activity className="w-4 h-4 text-slate-400" />
                        <span className="text-xs text-slate-400 uppercase tracking-wide">FPS</span>
                    </div>
                    <p className="text-2xl font-bold text-cyan-400">{stats.fps}</p>
                </div>

                <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/50">
                    <div className="flex items-center gap-2 mb-2">
                        <span className="text-xs text-slate-400 uppercase tracking-wide">系統狀態</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <motion.div animate={{ backgroundColor: stats.connected ? "#22c55e" : "#ef4444", scale: stats.connected ? [1, 1.2, 1] : 1 }} transition={{ duration: 1, repeat: stats.connected ? Infinity : 0 }} className="w-2.5 h-2.5 rounded-full" />
                        <p className={cn("text-sm font-medium", stats.connected ? "text-emerald-400" : "text-red-400")}>
                            {stats.connected ? "連線中" : "未連線"}
                        </p>
                    </div>
                </div>

                {/* Dynamic Metrics */}
                {Object.entries(stats.metrics || {}).map(([key, val]) => (
                    <div key={key} className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/50">
                        <div className="flex items-center gap-2 mb-2">
                            <Target className="w-4 h-4 text-slate-400" />
                            <span className="text-xs text-slate-400 uppercase tracking-wide">{key}</span>
                        </div>
                        <p className="text-xl font-bold text-violet-400">
                            {typeof val === 'number' ? (val * 100).toFixed(1) + '%' : val}
                        </p>
                    </div>
                ))}

                {/* Dynamic Trigger Counts */}
                {Object.entries(stats.trigger_counts || {}).map(([key, count]) => (
                    <div key={`count-${key}`} className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/50">
                        <div className="flex items-center gap-2 mb-2">
                            <Zap className="w-4 h-4 text-slate-400" />
                            <span className="text-xs text-slate-400 uppercase tracking-wide">{key} 次數</span>
                        </div>
                        <p className="text-xl font-bold text-amber-400">{count}</p>
                    </div>
                ))}
            </div>

            {/* Active Events / Alerts */}
            {Object.entries(stats.active_events || {}).map(([key, isActive]) => isActive && (
                <motion.div key={`event-${key}`} initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="p-4 rounded-xl bg-red-500/20 border border-red-500/50 flex items-center justify-center">
                    <p className="text-red-400 font-bold tracking-widest uppercase">⚠️ {key} 觸發</p>
                </motion.div>
            ))}
        </div>
    );
}

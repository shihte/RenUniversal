"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import {
    Activity,
    AlertTriangle,
    TrendingUp,
    Gauge,
    RotateCcw,
    Loader2
} from "lucide-react";

interface PostureStats {
    ratio: number;
    nose_chin_ratio: number;
    is_bad_posture: boolean;
    down_count: number;
    fps: number;
    connected: boolean;
    calibrating: boolean;
    calibration_progress: number;
    is_turning: boolean;
    baseline_eye_dist: number;
}

interface StatsDisplayProps {
    className?: string;
}

export function StatsDisplay({ className }: StatsDisplayProps) {
    const [stats, setStats] = useState<PostureStats>({
        ratio: 0,
        nose_chin_ratio: 0,
        is_bad_posture: false,
        down_count: 0,
        fps: 0,
        connected: false,
        calibrating: true,
        calibration_progress: 0,
        is_turning: false,
        baseline_eye_dist: 0,
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

    const getRatioColor = (ratio: number, isBad: boolean) => {
        if (isBad) return "text-red-400";
        if (ratio < -8) return "text-amber-400";
        return "text-emerald-400";
    };

    const getRatioBarWidth = (ratio: number) => {
        // Map ratio (-20 to +10) to percentage (100 to 0)
        // Negative = head down, so we show it as more filled
        const normalized = Math.min(Math.max((-ratio + 10) / 30, 0), 1) * 100;
        return `${normalized}%`;
    };

    // Calibrating state
    if (stats.calibrating && stats.connected) {
        return (
            <div className={cn("space-y-4", className)}>
                <div className="flex flex-col items-center justify-center p-6 rounded-xl bg-violet-500/10 border border-violet-500/30">
                    <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                        className="mb-4"
                    >
                        <Loader2 className="w-10 h-10 text-violet-400" />
                    </motion.div>
                    <p className="text-violet-300 font-semibold mb-2">校準中...</p>
                    <p className="text-violet-400/70 text-sm text-center mb-4">請正視前方保持不動</p>

                    {/* Progress bar */}
                    <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
                        <motion.div
                            className="h-full bg-gradient-to-r from-violet-500 to-indigo-500"
                            animate={{ width: `${stats.calibration_progress}%` }}
                            transition={{ duration: 0.2 }}
                        />
                    </div>
                    <p className="text-violet-400 text-sm mt-2">{stats.calibration_progress}%</p>
                </div>
            </div>
        );
    }

    return (
        <div className={cn("space-y-4", className)}>
            {/* Turning Indicator */}
            <AnimatePresence>
                {stats.is_turning && (
                    <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        className="flex items-center gap-3 p-3 rounded-xl bg-amber-500/10 border border-amber-500/30"
                    >
                        <RotateCcw className="w-4 h-4 text-amber-400" />
                        <p className="text-amber-400 text-sm">頭部轉動中 - 暫停偵測</p>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 gap-3">
                {/* Ratio */}
                <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/50">
                    <div className="flex items-center gap-2 mb-2">
                        <Gauge className="w-4 h-4 text-slate-400" />
                        <span className="text-xs text-slate-400 uppercase tracking-wide">姿態變化</span>
                    </div>
                    <p className={cn("text-2xl font-bold", getRatioColor(stats.ratio, stats.is_bad_posture))}>
                        {stats.ratio > 0 ? "+" : ""}{stats.ratio.toFixed(1)}%
                    </p>
                    {/* Ratio Bar */}
                    <div className="mt-2 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                        <motion.div
                            className={cn(
                                "h-full rounded-full",
                                stats.is_bad_posture
                                    ? "bg-red-500"
                                    : stats.ratio < -8
                                        ? "bg-amber-500"
                                        : "bg-emerald-500"
                            )}
                            animate={{ width: getRatioBarWidth(stats.ratio) }}
                            transition={{ duration: 0.2 }}
                        />
                    </div>
                    <div className="flex justify-between mt-1 text-[10px] text-slate-500">
                        <span>抬頭</span>
                        <span>正常</span>
                        <span>低頭</span>
                    </div>
                </div>

                {/* Down Count */}
                <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/50">
                    <div className="flex items-center gap-2 mb-2">
                        <TrendingUp className="w-4 h-4 text-slate-400" />
                        <span className="text-xs text-slate-400 uppercase tracking-wide">低頭次數</span>
                    </div>
                    <p className="text-2xl font-bold text-white">
                        {stats.down_count}
                        <span className="text-sm text-slate-500 ml-1">次</span>
                    </p>
                </div>

                {/* FPS */}
                <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/50">
                    <div className="flex items-center gap-2 mb-2">
                        <Activity className="w-4 h-4 text-slate-400" />
                        <span className="text-xs text-slate-400 uppercase tracking-wide">FPS</span>
                    </div>
                    <p className="text-2xl font-bold text-cyan-400">
                        {stats.fps}
                    </p>
                </div>

                {/* Connection Status */}
                <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/50">
                    <div className="flex items-center gap-2 mb-2">
                        <span className="text-xs text-slate-400 uppercase tracking-wide">狀態</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <motion.div
                            animate={{
                                backgroundColor: stats.connected ? "#22c55e" : "#ef4444",
                                scale: stats.connected ? [1, 1.2, 1] : 1,
                            }}
                            transition={{ duration: 1, repeat: stats.connected ? Infinity : 0 }}
                            className="w-2.5 h-2.5 rounded-full"
                        />
                        <p className={cn("text-sm font-medium", stats.connected ? "text-emerald-400" : "text-red-400")}>
                            {stats.connected ? "偵測中" : "未連線"}
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}

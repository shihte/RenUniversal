"use client";

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { Sliders, RotateCcw, Save } from "lucide-react";
import { cn } from "@/lib/utils";

interface SettingsControlProps {
    className?: string;
}

export function SettingsControl({ className }: SettingsControlProps) {
    const [threshold, setThreshold] = useState(30);
    const [yawTolerance, setYawTolerance] = useState(20);
    const [isSaving, setIsSaving] = useState(false);
    const [isRecalibrating, setIsRecalibrating] = useState(false);
    const [message, setMessage] = useState<string | null>(null);

    // Fetch current settings on mount
    const fetchSettings = useCallback(async () => {
        try {
            const res = await fetch("http://localhost:5001/settings");
            if (res.ok) {
                const data = await res.json();
                setThreshold(data.threshold);
                setYawTolerance(data.yaw_tolerance);
            }
        } catch {
            // Ignore errors
        }
    }, []);

    useEffect(() => {
        fetchSettings();
    }, [fetchSettings]);

    const saveSettings = async () => {
        setIsSaving(true);
        setMessage(null);
        try {
            const res = await fetch("http://localhost:5001/settings", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ threshold, yaw_tolerance: yawTolerance }),
            });
            if (res.ok) {
                setMessage("設定已儲存");
                setTimeout(() => setMessage(null), 2000);
            }
        } catch {
            setMessage("儲存失敗");
        }
        setIsSaving(false);
    };

    const triggerRecalibrate = async () => {
        setIsRecalibrating(true);
        setMessage(null);
        try {
            const res = await fetch("http://localhost:5001/recalibrate", {
                method: "POST",
            });
            if (res.ok) {
                setMessage("重新校準中...");
                setTimeout(() => setMessage(null), 3000);
            }
        } catch {
            setMessage("校準失敗");
        }
        setIsRecalibrating(false);
    };

    return (
        <div className={cn("space-y-4", className)}>
            {/* Threshold Slider */}
            <div>
                <div className="flex justify-between items-center mb-2">
                    <label className="text-sm text-slate-400 flex items-center gap-2">
                        <Sliders className="w-4 h-4" />
                        低頭偵測靈敏度
                    </label>
                    <span className="text-sm font-mono text-white">{threshold}%</span>
                </div>
                <input
                    type="range"
                    min="10"
                    max="60"
                    value={threshold}
                    onChange={(e) => setThreshold(Number(e.target.value))}
                    className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-violet-500"
                />
                <div className="flex justify-between mt-1 text-[10px] text-slate-500">
                    <span>敏感</span>
                    <span>寬鬆</span>
                </div>
            </div>

            {/* Yaw Tolerance Slider */}
            <div>
                <div className="flex justify-between items-center mb-2">
                    <label className="text-sm text-slate-400">轉頭容忍度</label>
                    <span className="text-sm font-mono text-white">{yawTolerance}%</span>
                </div>
                <input
                    type="range"
                    min="10"
                    max="40"
                    value={yawTolerance}
                    onChange={(e) => setYawTolerance(Number(e.target.value))}
                    className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-cyan-500"
                />
                <div className="flex justify-between mt-1 text-[10px] text-slate-500">
                    <span>嚴格</span>
                    <span>寬鬆</span>
                </div>
            </div>

            {/* Buttons */}
            <div className="flex gap-2 pt-2">
                <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={saveSettings}
                    disabled={isSaving}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium transition-colors disabled:opacity-50"
                >
                    <Save className="w-4 h-4" />
                    {isSaving ? "儲存中..." : "套用設定"}
                </motion.button>

                <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={triggerRecalibrate}
                    disabled={isRecalibrating}
                    className="flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-200 text-sm font-medium transition-colors disabled:opacity-50"
                >
                    <RotateCcw className={cn("w-4 h-4", isRecalibrating && "animate-spin")} />
                    重新校準
                </motion.button>
            </div>

            {/* Message */}
            {message && (
                <motion.p
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-center text-sm text-emerald-400"
                >
                    {message}
                </motion.p>
            )}
        </div>
    );
}

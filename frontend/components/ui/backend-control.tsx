"use client";

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface BackendControlProps {
    onStatusChange?: (isRunning: boolean) => void;
    className?: string;
}

export function BackendControl({ onStatusChange, className }: BackendControlProps) {
    const [isRunning, setIsRunning] = useState(false);
    const [isLoading, setIsLoading] = useState(false);

    const checkStatus = useCallback(async () => {
        try {
            const res = await fetch("/api/backend");
            const data = await res.json();
            setIsRunning(data.running);
            onStatusChange?.(data.running);
        } catch {
            setIsRunning(false);
            onStatusChange?.(false);
        }
    }, [onStatusChange]);

    useEffect(() => {
        checkStatus();
        const interval = setInterval(checkStatus, 3000);
        return () => clearInterval(interval);
    }, [checkStatus]);

    const toggleBackend = async () => {
        setIsLoading(true);
        const action = isRunning ? "stop" : "start";

        try {
            await fetch("/api/backend", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action, cameraId: 0 }),
            });
            setTimeout(checkStatus, 1500);
        } catch (error) {
            console.error("Backend control error:", error);
        } finally {
            setTimeout(() => setIsLoading(false), 1500);
        }
    };

    return (
        <div className={cn("flex items-center justify-between", className)}>
            {/* Status Text */}
            <div className="flex items-center gap-2">
                <motion.div
                    animate={{
                        scale: isRunning ? [1, 1.2, 1] : 1,
                        backgroundColor: isRunning ? "#22c55e" : "#ef4444",
                    }}
                    transition={{ duration: 0.5, repeat: isRunning ? Infinity : 0, repeatDelay: 1 }}
                    className="w-3 h-3 rounded-full"
                />
                <span className="text-sm text-slate-300">
                    {isRunning ? "偵測運行中" : "偵測已停止"}
                </span>
            </div>

            {/* Toggle Switch */}
            <button
                onClick={toggleBackend}
                disabled={isLoading}
                className={cn(
                    "relative w-14 h-7 rounded-full transition-all duration-300",
                    isLoading && "opacity-50 cursor-wait",
                    isRunning
                        ? "bg-gradient-to-r from-emerald-500 to-green-500"
                        : "bg-slate-700"
                )}
            >
                <motion.div
                    animate={{ x: isRunning ? 28 : 4 }}
                    transition={{ type: "spring", stiffness: 500, damping: 30 }}
                    className={cn(
                        "absolute top-1 w-5 h-5 rounded-full shadow-md",
                        isRunning ? "bg-white" : "bg-slate-400"
                    )}
                />
            </button>
        </div>
    );
}

"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import {
    Play,
    Square,
    RefreshCw,
    Loader2,
    CheckCircle2,
    XCircle,
    Camera,
    ChevronDown
} from "lucide-react";
import { Button } from "./button";

interface BackendControlProps {
    onStatusChange?: (isRunning: boolean) => void;
    className?: string;
}

export function BackendControl({ onStatusChange, className }: BackendControlProps) {
    const [isRunning, setIsRunning] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [cameraId, setCameraId] = useState(0);
    const [showCameraSelect, setShowCameraSelect] = useState(false);
    const [message, setMessage] = useState<string | null>(null);

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
        const interval = setInterval(checkStatus, 5000);
        return () => clearInterval(interval);
    }, [checkStatus]);

    const performAction = async (action: "start" | "stop" | "restart") => {
        setIsLoading(true);
        setMessage(null);

        try {
            const res = await fetch("/api/backend", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action, cameraId }),
            });

            const data = await res.json();
            setMessage(data.message);

            // Wait a bit then check status
            setTimeout(checkStatus, 1000);
        } catch (error) {
            setMessage(`錯誤: ${error}`);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className={cn("space-y-4", className)}>
            {/* Status Indicator */}
            <div className="flex items-center justify-between">
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
                        {isRunning ? "後端運行中" : "後端已停止"}
                    </span>
                </div>

                {/* Camera Select */}
                <div className="relative">
                    <button
                        onClick={() => setShowCameraSelect(!showCameraSelect)}
                        className="flex items-center gap-2 px-3 py-1.5 text-xs rounded-lg bg-slate-800/80 text-slate-300 hover:bg-slate-700/80 transition-all border border-slate-700"
                    >
                        <Camera className="w-3 h-3" />
                        Camera {cameraId}
                        <ChevronDown className={cn("w-3 h-3 transition-transform", showCameraSelect && "rotate-180")} />
                    </button>

                    <AnimatePresence>
                        {showCameraSelect && (
                            <motion.div
                                initial={{ opacity: 0, y: -10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -10 }}
                                className="absolute right-0 mt-2 p-1 rounded-lg bg-slate-800 border border-slate-700 shadow-xl z-50"
                            >
                                {[0, 1, 2].map((id) => (
                                    <button
                                        key={id}
                                        onClick={() => {
                                            setCameraId(id);
                                            setShowCameraSelect(false);
                                        }}
                                        className={cn(
                                            "w-full px-4 py-2 text-left text-sm rounded-md transition-colors",
                                            cameraId === id
                                                ? "bg-violet-500/20 text-violet-400"
                                                : "text-slate-300 hover:bg-slate-700"
                                        )}
                                    >
                                        Camera {id}
                                    </button>
                                ))}
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>

            {/* Control Buttons */}
            <div className="flex gap-2">
                <Button
                    onClick={() => performAction("start")}
                    disabled={isLoading || isRunning}
                    variant="default"
                    size="sm"
                    className="flex-1"
                >
                    {isLoading ? (
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                        <Play className="w-4 h-4 mr-2" />
                    )}
                    啟動
                </Button>

                <Button
                    onClick={() => performAction("stop")}
                    disabled={isLoading || !isRunning}
                    variant="destructive"
                    size="sm"
                    className="flex-1"
                >
                    <Square className="w-4 h-4 mr-2" />
                    停止
                </Button>

                <Button
                    onClick={() => performAction("restart")}
                    disabled={isLoading}
                    variant="outline"
                    size="sm"
                    className="flex-1"
                >
                    <RefreshCw className={cn("w-4 h-4 mr-2", isLoading && "animate-spin")} />
                    重啟
                </Button>
            </div>

            {/* Message */}
            <AnimatePresence>
                {message && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        className={cn(
                            "text-xs p-2 rounded-lg flex items-center gap-2",
                            message.includes("錯誤")
                                ? "bg-red-500/10 text-red-400 border border-red-500/20"
                                : "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                        )}
                    >
                        {message.includes("錯誤") ? (
                            <XCircle className="w-3 h-3" />
                        ) : (
                            <CheckCircle2 className="w-3 h-3" />
                        )}
                        {message}
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

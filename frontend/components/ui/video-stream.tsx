"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { AlertCircle, CheckCircle2, Loader2, Video, VideoOff } from "lucide-react";

interface VideoStreamProps {
    streamUrl: string;
    className?: string;
}

export function VideoStream({ streamUrl, className }: VideoStreamProps) {
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isConnected, setIsConnected] = useState(false);
    const imgRef = useRef<HTMLImageElement>(null);
    const checkIntervalRef = useRef<NodeJS.Timeout | null>(null);

    // Check if the stream is available by checking backend status
    const checkStreamStatus = useCallback(async () => {
        try {
            const res = await fetch("http://localhost:5001/status", {
                method: "GET",
                signal: AbortSignal.timeout(2000),
            });

            if (res.ok) {
                const data = await res.json();
                if (data.connected) {
                    setIsLoading(false);
                    setIsConnected(true);
                    setError(null);
                    return true;
                }
            }
            return false;
        } catch {
            return false;
        }
    }, []);

    useEffect(() => {
        // Initial check
        checkStreamStatus();

        // Always keep checking every 2 seconds to detect disconnection
        checkIntervalRef.current = setInterval(async () => {
            const connected = await checkStreamStatus();
            if (!connected) {
                setIsConnected(false);
                setError("後端已停止運行");
            }
        }, 2000);

        return () => {
            if (checkIntervalRef.current) {
                clearInterval(checkIntervalRef.current);
            }
        };
    }, [streamUrl, checkStreamStatus]);

    const handleError = () => {
        setIsLoading(false);
        setError("無法連接至影像串流服務");
        setIsConnected(false);

        // Retry connection check
        if (!checkIntervalRef.current) {
            checkIntervalRef.current = setInterval(async () => {
                const isNowConnected = await checkStreamStatus();
                if (isNowConnected && checkIntervalRef.current) {
                    clearInterval(checkIntervalRef.current);
                }
            }, 3000);
        }
    };

    return (
        <div
            className={cn(
                "relative overflow-hidden rounded-2xl border border-white/10 bg-slate-900/60 backdrop-blur-xl",
                className
            )}
        >
            {/* Status Badge */}
            <div className="absolute top-4 left-4 z-10">
                <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className={cn(
                        "flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium backdrop-blur-md",
                        isConnected
                            ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                            : error
                                ? "bg-red-500/20 text-red-400 border border-red-500/30"
                                : "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                    )}
                >
                    {isLoading ? (
                        <>
                            <Loader2 className="w-3 h-3 animate-spin" />
                            連接中...
                        </>
                    ) : isConnected ? (
                        <>
                            <CheckCircle2 className="w-3 h-3" />
                            即時串流
                        </>
                    ) : (
                        <>
                            <AlertCircle className="w-3 h-3" />
                            連線中斷
                        </>
                    )}
                </motion.div>
            </div>

            {/* Loading State */}
            {isLoading && (
                <div className="absolute inset-0 flex items-center justify-center bg-slate-900/80 backdrop-blur-sm z-5">
                    <div className="flex flex-col items-center gap-4">
                        <motion.div
                            animate={{ scale: [1, 1.1, 1] }}
                            transition={{ duration: 1.5, repeat: Infinity }}
                            className="p-4 rounded-full bg-gradient-to-r from-violet-500/20 to-indigo-500/20 border border-violet-500/30"
                        >
                            <Video className="w-8 h-8 text-violet-400" />
                        </motion.div>
                        <p className="text-slate-400 text-sm">正在載入影像串流...</p>
                    </div>
                </div>
            )}

            {/* Error State */}
            {error && !isLoading && (
                <div className="absolute inset-0 flex items-center justify-center bg-slate-900/80 backdrop-blur-sm z-5">
                    <div className="flex flex-col items-center gap-4 p-6 text-center">
                        <div className="p-4 rounded-full bg-red-500/20 border border-red-500/30">
                            <VideoOff className="w-8 h-8 text-red-400" />
                        </div>
                        <div>
                            <p className="text-slate-200 font-medium mb-1">{error}</p>
                            <p className="text-slate-500 text-sm">請確認 Python 串流服務是否啟動</p>
                        </div>
                    </div>
                </div>
            )}

            {/* Video Stream - Always render the img element */}
            <img
                ref={imgRef}
                src={isConnected ? streamUrl : undefined}
                alt="Posture Monitor Stream"
                className={cn(
                    "w-full h-full object-cover aspect-video transition-opacity duration-300",
                    isConnected ? "opacity-100" : "opacity-0"
                )}
                onError={handleError}
            />

            {/* Scan line effect - gives it a tech feel */}
            {isConnected && (
                <div className="absolute inset-0 pointer-events-none">
                    <motion.div
                        className="absolute w-full h-px bg-gradient-to-r from-transparent via-cyan-400/50 to-transparent"
                        animate={{ y: [0, 400, 0] }}
                        transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
                    />
                </div>
            )}
        </div>
    );
}

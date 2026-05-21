"use client";

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { Sliders, RotateCcw, Save } from "lucide-react";
import { cn } from "@/lib/utils";

interface SettingsControlProps {
    className?: string;
}

export function SettingsControl({ className }: SettingsControlProps) {
    const [prefs, setPrefs] = useState<Record<string, number>>({});
    const [isSaving, setIsSaving] = useState(false);
    const [isRecalibrating, setIsRecalibrating] = useState(false);
    const [message, setMessage] = useState<string | null>(null);
    const [skills, setSkills] = useState<any[]>([]);

    const fetchSettings = useCallback(async () => {
        try {
            const res = await fetch("http://localhost:5001/status");
            const skillsRes = await fetch("http://localhost:5001/api/skills");
            if (res.ok) {
                const data = await res.json();
                setPrefs(data.prefs || {});
            }
            if (skillsRes.ok) {
                const s = await skillsRes.json();
                setSkills(s);
            }
        } catch {
        }
    }, []);

    useEffect(() => {
        fetchSettings();
    }, [fetchSettings]);

    const handlePrefChange = (key: string, val: number) => {
        setPrefs(p => ({ ...p, [key]: val }));
    };

    const saveSettings = async () => {
        setIsSaving(true);
        setMessage(null);
        try {
            const res = await fetch("http://localhost:5001/api/settings/update", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(prefs),
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
            {skills.map(skill => (
                <div key={skill.name} className="space-y-2 mb-4 p-3 bg-slate-800/30 rounded-lg border border-slate-700/50">
                    <h3 className="text-xs font-bold text-slate-300 uppercase">{skill.name} 靈敏度</h3>
                    {Object.keys(skill.default_preferences || {}).map(key => {
                        const val = prefs[key] !== undefined ? prefs[key] : skill.default_preferences[key];
                        const sliderVal = Math.round(val * 100);
                        const minRange = (skill.default_preferences[key] < 0) ? -100 : 0;
                        return (
                            <div key={key}>
                                <div className="flex justify-between items-center mb-1">
                                    <label className="text-xs text-slate-400">{key}</label>
                                    <span className="text-xs font-mono text-white">{sliderVal}%</span>
                                </div>
                                <input
                                    type="range"
                                    min={minRange}
                                    max="100"
                                    value={sliderVal}
                                    onChange={(e) => handlePrefChange(key, Number(e.target.value) / 100)}
                                    className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-violet-500"
                                />
                            </div>
                        );
                    })}
                </div>
            ))}

            <div className="flex gap-2 pt-2">
                <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} onClick={saveSettings} disabled={isSaving} className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium transition-colors disabled:opacity-50">
                    <Save className="w-4 h-4" />
                    {isSaving ? "儲存中..." : "套用設定"}
                </motion.button>
                <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} onClick={triggerRecalibrate} disabled={isRecalibrating} className="flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-200 text-sm font-medium transition-colors disabled:opacity-50">
                    <RotateCcw className={cn("w-4 h-4", isRecalibrating && "animate-spin")} />
                    重新校準
                </motion.button>
            </div>
            {message && (
                <motion.p initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} className="text-center text-sm text-emerald-400">
                    {message}
                </motion.p>
            )}
        </div>
    );
}

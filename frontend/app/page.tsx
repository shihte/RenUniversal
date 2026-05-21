"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Activity, Camera, Server, BarChart3, Settings, Brain, Zap } from "lucide-react";
import { VideoStream } from "@/components/ui/video-stream";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { BackendControl } from "@/components/ui/backend-control";
import { StatsDisplay } from "@/components/ui/stats-display";
import { SettingsControl } from "@/components/ui/settings-control";
import { BuilderControl } from "@/components/ui/builder-control";

export default function Home() {
  const PYTHON_STREAM_URL = "http://localhost:5001/video_feed";
  const [activeTab, setActiveTab] = useState<"dashboard" | "skills" | "events">("dashboard");

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-1/2 -left-1/2 w-full h-full bg-gradient-to-br from-violet-600/10 via-transparent to-transparent rounded-full blur-3xl" />
        <div className="absolute -bottom-1/2 -right-1/2 w-full h-full bg-gradient-to-tl from-cyan-600/10 via-transparent to-transparent rounded-full blur-3xl" />
      </div>

      <div
        className="fixed inset-0 pointer-events-none opacity-[0.015]"
        style={{
          backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
          backgroundSize: '50px 50px'
        }}
      />

      <div className="relative z-10 container mx-auto px-4 py-8">
        <motion.header initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-8">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-400 text-sm font-medium mb-6">
            <Activity className="w-4 h-4" />
            CTAR Framework
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
            通用姿態偵測與事件架構
          </h1>
          <p className="text-slate-400 text-lg max-w-2xl mx-auto">
            動態定義動作與複合事件，打造專屬的 AI 應用。
          </p>
        </motion.header>

        <div className="flex justify-center mb-8 border-b border-slate-800">
          <button onClick={() => setActiveTab("dashboard")} className={`px-6 py-3 text-sm font-bold flex items-center gap-2 transition-colors ${activeTab === 'dashboard' ? 'text-violet-400 border-b-2 border-violet-400' : 'text-slate-500 hover:text-slate-300'}`}>
            <BarChart3 className="w-4 h-4" /> 即時監控 (Dashboard)
          </button>
          <button onClick={() => setActiveTab("skills")} className={`px-6 py-3 text-sm font-bold flex items-center gap-2 transition-colors ${activeTab === 'skills' ? 'text-cyan-400 border-b-2 border-cyan-400' : 'text-slate-500 hover:text-slate-300'}`}>
            <Brain className="w-4 h-4" /> 動作技能 (Skills)
          </button>
          <button onClick={() => setActiveTab("events")} className={`px-6 py-3 text-sm font-bold flex items-center gap-2 transition-colors ${activeTab === 'events' ? 'text-amber-400 border-b-2 border-amber-400' : 'text-slate-500 hover:text-slate-300'}`}>
            <Zap className="w-4 h-4" /> 複合事件 (Events)
          </button>
        </div>

        <AnimatePresence mode="wait">
          {activeTab === "dashboard" && (
            <motion.div key="dashboard" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="grid lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Camera className="w-5 h-5 text-violet-400" />即時影像
                    </CardTitle>
                    <CardDescription>來自 Python 後端的即時串流</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <VideoStream streamUrl={PYTHON_STREAM_URL} className="w-full min-h-[400px]" />
                  </CardContent>
                </Card>
              </div>

              <div className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-lg">
                      <Server className="w-5 h-5 text-cyan-400" />後端控制
                    </CardTitle>
                    <CardDescription>控制串流服務</CardDescription>
                  </CardHeader>
                  <CardContent><BackendControl /></CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-lg">
                      <BarChart3 className="w-5 h-5 text-violet-400" />系統狀態
                    </CardTitle>
                  </CardHeader>
                  <CardContent><StatsDisplay /></CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-lg">
                      <Settings className="w-5 h-5 text-amber-400" />閾值調整
                    </CardTitle>
                  </CardHeader>
                  <CardContent><SettingsControl /></CardContent>
                </Card>
              </div>
            </motion.div>
          )}

          {activeTab === "skills" && (
            <motion.div key="skills" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}>
              <Card>
                <CardHeader>
                  <CardTitle className="text-xl text-cyan-400">動作技能建構器 (Skills Builder)</CardTitle>
                  <CardDescription>定義基礎動作。語法包含點位 ID：如 p11 (左肩)、f1 (鼻尖)。</CardDescription>
                </CardHeader>
                <CardContent>
                  <BuilderControl type="skill" />
                </CardContent>
              </Card>
            </motion.div>
          )}

          {activeTab === "events" && (
            <motion.div key="events" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}>
              <Card>
                <CardHeader>
                  <CardTitle className="text-xl text-amber-400">複合事件建構器 (Events Builder)</CardTitle>
                  <CardDescription>使用 AND / OR 組合多個技能。例如：slouch AND sway。</CardDescription>
                </CardHeader>
                <CardContent>
                  <BuilderControl type="event" />
                </CardContent>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>

        <motion.footer initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }} className="text-center mt-16 text-slate-500 text-sm">
          <p>CTAR Framework • Powered by Next.js 15 & MediaPipe</p>
        </motion.footer>
      </div>
    </main>
  );
}

"use client";

import { motion } from "framer-motion";
import { Activity, Camera, Server, BarChart3 } from "lucide-react";
import { VideoStream } from "@/components/ui/video-stream";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { BackendControl } from "@/components/ui/backend-control";
import { StatsDisplay } from "@/components/ui/stats-display";

export default function Home() {
  const PYTHON_STREAM_URL = "http://localhost:5001/video_feed";

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Ambient Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-1/2 -left-1/2 w-full h-full bg-gradient-to-br from-violet-600/10 via-transparent to-transparent rounded-full blur-3xl" />
        <div className="absolute -bottom-1/2 -right-1/2 w-full h-full bg-gradient-to-tl from-cyan-600/10 via-transparent to-transparent rounded-full blur-3xl" />
      </div>

      {/* Grid Pattern */}
      <div
        className="fixed inset-0 pointer-events-none opacity-[0.015]"
        style={{
          backgroundImage: `
            linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)
          `,
          backgroundSize: '50px 50px'
        }}
      />

      <div className="relative z-10 container mx-auto px-4 py-8">
        {/* Header */}
        <motion.header
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-400 text-sm font-medium mb-6">
            <Activity className="w-4 h-4" />
            CTAR Posture Monitor
          </div>
          <h1 className="text-4xl md:text-6xl font-bold mb-4 bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
            即時姿態監控系統
          </h1>
          <p className="text-slate-400 text-lg max-w-2xl mx-auto">
            使用 AI 驅動的 MediaPipe 臉部追蹤技術，即時偵測您的姿態並提供警告
          </p>
        </motion.header>

        {/* Main Content */}
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Video Stream - Main */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 }}
            className="lg:col-span-2"
          >
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Camera className="w-5 h-5 text-violet-400" />
                  即時影像
                </CardTitle>
                <CardDescription>
                  來自 Python 後端的 MJPEG 即時串流
                </CardDescription>
              </CardHeader>
              <CardContent>
                <VideoStream
                  streamUrl={PYTHON_STREAM_URL}
                  className="w-full min-h-[400px]"
                />
              </CardContent>
            </Card>
          </motion.div>

          {/* Sidebar - Stats & Info */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="space-y-6"
          >
            {/* Backend Control */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Server className="w-5 h-5 text-cyan-400" />
                  後端控制
                </CardTitle>
                <CardDescription>
                  啟動、停止或重啟 Python 串流服務
                </CardDescription>
              </CardHeader>
              <CardContent>
                <BackendControl />
              </CardContent>
            </Card>

            {/* Stats Display */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <BarChart3 className="w-5 h-5 text-violet-400" />
                  即時數據
                </CardTitle>
                <CardDescription>
                  姿態偵測即時統計
                </CardDescription>
              </CardHeader>
              <CardContent>
                <StatsDisplay />
              </CardContent>
            </Card>

            {/* Tech Stack */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">技術架構</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {["Next.js 15", "TypeScript", "Tailwind CSS", "Framer Motion", "Prisma", "MediaPipe"].map((tech) => (
                    <span
                      key={tech}
                      className="px-3 py-1 text-xs rounded-full bg-slate-800 text-slate-300 border border-slate-700"
                    >
                      {tech}
                    </span>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Footer */}
        <motion.footer
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="text-center mt-16 text-slate-500 text-sm"
        >
          <p>CTAR Posture Monitor • Powered by Next.js 15 & MediaPipe</p>
        </motion.footer>
      </div>
    </main>
  );
}

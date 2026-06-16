import { NextResponse } from "next/server";
import { exec, spawn } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

// Path to the Python environment and script
const PYTHON_PATH = "/Users/shihte.hsiao/Downloads/CTAR/venv/bin/python";
const SCRIPT_PATH = "/Users/shihte.hsiao/Downloads/CTAR/backend/stream_server.py";
const PORT = 5001;

export async function POST(request: Request) {
    try {
        const body = await request.json();
        const { action, cameraId = 0 } = body;

        switch (action) {
            case "start":
                // Kill any existing process on the port first
                try {
                    await execAsync(`lsof -ti:${PORT} | xargs kill -9 2>/dev/null || true`);
                    await new Promise((resolve) => setTimeout(resolve, 1000));
                } catch {
                    // Ignore errors if no process was running
                }

                // Start the stream server in background using spawn
                const child = spawn(
                    PYTHON_PATH,
                    [SCRIPT_PATH, "--port", String(PORT), "--camera", String(cameraId)],
                    {
                        detached: true,
                        stdio: "ignore",
                    }
                );
                child.unref();

                // Wait a bit for the server to start
                await new Promise((resolve) => setTimeout(resolve, 2000));

                return NextResponse.json({
                    success: true,
                    message: `Stream server started on port ${PORT} with camera ${cameraId}`,
                });

            case "stop":
                try {
                    await execAsync(`lsof -ti:${PORT} | xargs kill -9 2>/dev/null || true`);
                    return NextResponse.json({
                        success: true,
                        message: "Stream server stopped",
                    });
                } catch {
                    return NextResponse.json({
                        success: true,
                        message: "No server was running",
                    });
                }

            case "restart":
                // Stop first
                try {
                    await execAsync(`lsof -ti:${PORT} | xargs kill -9 2>/dev/null || true`);
                    await new Promise((resolve) => setTimeout(resolve, 1000));
                } catch {
                    // Ignore
                }

                // Start again using spawn
                const restartChild = spawn(
                    PYTHON_PATH,
                    [SCRIPT_PATH, "--port", String(PORT), "--camera", String(cameraId)],
                    {
                        detached: true,
                        stdio: "ignore",
                    }
                );
                restartChild.unref();

                await new Promise((resolve) => setTimeout(resolve, 2000));

                return NextResponse.json({
                    success: true,
                    message: `Stream server restarted on port ${PORT} with camera ${cameraId}`,
                });

            case "status":
                try {
                    const { stdout } = await execAsync(`lsof -ti:${PORT} 2>/dev/null || echo ""`);
                    const isRunning = stdout.trim().length > 0;
                    return NextResponse.json({
                        success: true,
                        running: isRunning,
                        port: PORT,
                    });
                } catch {
                    return NextResponse.json({
                        success: true,
                        running: false,
                        port: PORT,
                    });
                }

            default:
                return NextResponse.json(
                    { success: false, error: "Invalid action" },
                    { status: 400 }
                );
        }
    } catch (error) {
        console.error("Backend control error:", error);
        return NextResponse.json(
            { success: false, error: String(error) },
            { status: 500 }
        );
    }
}

export async function GET() {
    try {
        const { stdout } = await execAsync(`lsof -ti:${PORT} 2>/dev/null || echo ""`);
        const isRunning = stdout.trim().length > 0;
        return NextResponse.json({
            success: true,
            running: isRunning,
            port: PORT,
        });
    } catch {
        return NextResponse.json({
            success: true,
            running: false,
            port: PORT,
        });
    }
}

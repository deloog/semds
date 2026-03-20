"""
SEMDS Web Server - 真正的服务和交互

启动后:
1. Web界面: http://localhost:8000
2. API端点: http://localhost:8000/api/
3. 系统会持续运行，自主进化

启动: python semds_server.py
"""

import json
import os
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from semds_live import SEMDSLive

# 创建FastAPI应用
app = FastAPI(title="SEMDS - Self-Evolving System")

# 全局系统实例
semds_system = None
system_status = {
    "running": False,
    "tasks_completed": 0,
    "success_rate": 0.0,
    "last_evolution": None,
    "evolution_count": 0,
    "current_tasks": [],
}


# WebSocket连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass


manager = ConnectionManager()


# HTML界面
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>SEMDS - Self-Evolving System</title>
    <style>
        body { font-family: monospace; margin: 0; padding: 20px; background: #1a1a2e; color: #eee; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: #00ff88; border-bottom: 2px solid #00ff88; padding-bottom: 10px; }
        .status { background: #16213e; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .status-item { display: inline-block; margin-right: 30px; }
        .status-value { color: #00ff88; font-size: 24px; font-weight: bold; }
        .status-label { color: #888; font-size: 12px; }
        .task-input { width: 100%; padding: 15px; font-size: 16px; background: #0f3460; border: 1px solid #00ff88; color: #fff; border-radius: 5px; margin: 20px 0; }
        .task-input:focus { outline: none; box-shadow: 0 0 10px #00ff88; }
        button { padding: 15px 30px; font-size: 16px; background: #00ff88; color: #1a1a2e; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
        button:hover { background: #00cc6a; }
        .logs { background: #0f3460; padding: 15px; border-radius: 5px; height: 400px; overflow-y: auto; margin-top: 20px; }
        .log-entry { margin: 5px 0; padding: 5px; border-left: 3px solid #00ff88; padding-left: 10px; }
        .log-time { color: #888; font-size: 12px; }
        .log-success { border-color: #00ff88; }
        .log-error { border-color: #ff4444; }
        .log-evolve { border-color: #ffaa00; }
        .section { margin: 30px 0; }
        h2 { color: #00ff88; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧬 SEMDS - Self-Evolving Meta-Development System</h1>
        
        <div class="status">
            <div class="status-item">
                <div class="status-value" id="tasks-count">0</div>
                <div class="status-label">Tasks Completed</div>
            </div>
            <div class="status-item">
                <div class="status-value" id="success-rate">0%</div>
                <div class="status-label">Success Rate</div>
            </div>
            <div class="status-item">
                <div class="status-value" id="evolution-count">0</div>
                <div class="status-label">Evolutions</div>
            </div>
            <div class="status-item">
                <div class="status-value" id="system-status">🟢</div>
                <div class="status-label">Status</div>
            </div>
        </div>
        
        <div class="section">
            <h2>Assign Task</h2>
            <input type="text" class="task-input" id="task-input" 
                   placeholder="Describe a programming task (e.g., 'Create a calculator function')...">
            <div style="margin-top: 10px;">
                <button onclick="submitTask()">Execute Task</button>
                <button onclick="triggerEvolution()" style="margin-left: 10px; background: #ffaa00;">Trigger Evolution</button>
                <button onclick="clearLogs()" style="margin-left: 10px; background: #666;">Clear Logs</button>
            </div>
        </div>
        
        <div class="section">
            <h2>System Activity</h2>
            <div class="logs" id="logs"></div>
        </div>
    </div>
    
    <script>
        const ws = new WebSocket(`ws://${window.location.host}/ws`);
        const logsDiv = document.getElementById('logs');
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            
            if (data.type === 'status') {
                document.getElementById('tasks-count').textContent = data.tasks_completed;
                document.getElementById('success-rate').textContent = data.success_rate + '%';
                document.getElementById('evolution-count').textContent = data.evolution_count;
            }
            else if (data.type === 'log') {
                addLog(data.message, data.log_type);
            }
        };
        
        function addLog(message, type = 'info') {
            const entry = document.createElement('div');
            entry.className = 'log-entry log-' + type;
            const time = new Date().toLocaleTimeString();
            entry.innerHTML = `<span class="log-time">${time}</span> ${message}`;
            logsDiv.appendChild(entry);
            logsDiv.scrollTop = logsDiv.scrollHeight;
        }
        
        function submitTask() {
            const input = document.getElementById('task-input');
            const task = input.value.trim();
            if (!task) return;
            
            addLog(`Assigning task: ${task}`, 'info');
            
            fetch('/api/task', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({description: task})
            });
            
            input.value = '';
        }
        
        function triggerEvolution() {
            addLog('Triggering self-evolution...', 'evolve');
            fetch('/api/evolve', {method: 'POST'});
        }
        
        function clearLogs() {
            logsDiv.innerHTML = '';
        }
        
        // Enter key to submit
        document.getElementById('task-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') submitTask();
        });
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def root():
    """主页"""
    return HTML_PAGE


@app.post("/api/task")
async def execute_task(data: dict):
    """执行任务"""
    global semds_system, system_status

    description = data.get("description", "")
    if not description:
        return {"error": "No task description"}

    # 后台执行
    def run_task():
        try:
            result = semds_system.execute_task(description)

            # 广播结果
            message = {
                "type": "log",
                "log_type": "success" if result["success"] else "error",
                "message": f"Task '{description[:40]}...' -> {'SUCCESS' if result['success'] else 'FAILED'} (score: {result.get('score', 0):.2f})",
            }

            # 更新状态
            system_status["tasks_completed"] += 1
            if result["success"]:
                current_success = system_status["success_rate"] * (
                    system_status["tasks_completed"] - 1
                )
                system_status["success_rate"] = (current_success + 100) / system_status[
                    "tasks_completed"
                ]
            else:
                current_success = system_status["success_rate"] * (
                    system_status["tasks_completed"] - 1
                )
                system_status["success_rate"] = (
                    current_success / system_status["tasks_completed"]
                )

            # 异步广播
            import asyncio

            asyncio.run(manager.broadcast(message))
            asyncio.run(manager.broadcast({"type": "status", **system_status}))

        except Exception as e:
            message = {
                "type": "log",
                "log_type": "error",
                "message": f"Task failed: {str(e)}",
            }
            import asyncio

            asyncio.run(manager.broadcast(message))

    threading.Thread(target=run_task).start()

    return {"status": "Task queued"}


@app.post("/api/evolve")
async def evolve():
    """触发进化"""
    global semds_system, system_status

    def run_evolution():
        try:
            message = {
                "type": "log",
                "log_type": "evolve",
                "message": "Starting self-evolution...",
            }
            import asyncio

            asyncio.run(manager.broadcast(message))

            result = semds_system.evolve_self()

            system_status["evolution_count"] += 1
            system_status["last_evolution"] = datetime.now().isoformat()

            improvements = result.get("improvements_applied", 0)
            message = {
                "type": "log",
                "log_type": "success" if improvements > 0 else "info",
                "message": f"Evolution complete. Applied {improvements} improvements.",
            }
            asyncio.run(manager.broadcast(message))
            asyncio.run(manager.broadcast({"type": "status", **system_status}))

        except Exception as e:
            message = {
                "type": "log",
                "log_type": "error",
                "message": f"Evolution failed: {str(e)}",
            }
            import asyncio

            asyncio.run(manager.broadcast(message))

    threading.Thread(target=run_evolution).start()

    return {"status": "Evolution started"}


@app.get("/api/status")
async def get_status():
    """获取状态"""
    return system_status


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket连接"""
    await manager.connect(websocket)
    try:
        # 发送初始状态
        await websocket.send_json({"type": "status", **system_status})

        while True:
            # 保持连接
            data = await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(websocket)


def auto_evolution_loop():
    """自动进化循环（每10分钟检查一次）"""
    global semds_system, system_status

    while True:
        time.sleep(600)  # 10分钟

        if system_status["tasks_completed"] >= 5:
            try:
                message = {
                    "type": "log",
                    "log_type": "evolve",
                    "message": "[AUTO] Triggering scheduled evolution...",
                }
                import asyncio

                asyncio.run(manager.broadcast(message))

                result = semds_system.evolve_self()

                system_status["evolution_count"] += 1
                system_status["last_evolution"] = datetime.now().isoformat()

                improvements = result.get("improvements_applied", 0)
                message = {
                    "type": "log",
                    "log_type": "success" if improvements > 0 else "info",
                    "message": f"[AUTO] Evolution complete. Applied {improvements} improvements.",
                }
                asyncio.run(manager.broadcast(message))
                asyncio.run(manager.broadcast({"type": "status", **system_status}))

            except Exception as e:
                print(f"Auto-evolution error: {e}")


def main():
    """启动服务器"""
    global semds_system, system_status

    print("=" * 70)
    print("  SEMDS Web Server")
    print("=" * 70)
    print("\nInitializing...")

    # 初始化系统
    try:
        semds_system = SEMDSLive()
        system_status["running"] = True
    except SystemExit:
        print("\n[ERROR] API Key not configured!")
        print("  Create .env file with: DEEPSEEK_API_KEY=your-key")
        return

    # 启动自动进化线程
    evolution_thread = threading.Thread(target=auto_evolution_loop, daemon=True)
    evolution_thread.start()

    print("\n✓ System ready")
    print("✓ Auto-evolution enabled (every 10 minutes)")
    print("\nAccess SEMDS at:")
    print("  Web Interface: http://localhost:8000")
    print("  API: http://localhost:8000/api/")
    print("\nPress Ctrl+C to stop")
    print("=" * 70)

    # 启动服务器
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")


if __name__ == "__main__":
    main()

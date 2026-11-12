"""
TP-Link Router Discovery & Recovery Dashboard - Backend Entry Point
FastAPI application with REST endpoints, WebSocket streaming, and static SPA serving.
"""

import logging
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.services.websocket_service import ws_manager
from backend.api.network import router as network_router
from backend.api.wifi import router as wifi_router
from backend.api.discovery import router as discovery_router
from backend.api.devices import router as devices_router
from backend.api.recovery import router as recovery_router
from backend.api.auditor import router as auditor_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("backend")

app = FastAPI(
    title="TP-Link Router Discovery & Recovery Dashboard",
    description="Local web dashboard for LAN network discovery, diagnostics, and recovery guidance.",
    version="2.0.0"
)

# CORS Configuration - Local development & dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(network_router)
app.include_router(wifi_router)
app.include_router(discovery_router)
app.include_router(devices_router)
app.include_router(recovery_router)
app.include_router(auditor_router)


@app.get("/api/health")
def healthcheck():
    return {"status": "ok", "app": "router-recovery-dashboard", "version": "2.0.0"}


# Real-time WebSocket connection for scan progress
@app.websocket("/ws/scan")
async def websocket_scan_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep-alive receive ping / messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.debug(f"WebSocket connection closed: {e}")
        ws_manager.disconnect(websocket)


# Static assets & SPA fallback (when frontend is built)
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))


if __name__ == "__main__":
    import uvicorn
    # Security requirement: Bind to localhost by default
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    logger.info(f"Starting server on http://{host}:{port}")
    uvicorn.run("backend.main:app", host=host, port=port, reload=True)

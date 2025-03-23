from fastapi import APIRouter
from app.api.endpoints import audio, zoom, reports
from app.services.zoom_service import ZoomService

api_router = APIRouter()

# Include sub-routers
api_router.include_router(zoom.router, prefix="/zoom", tags=["Zoom"])
api_router.include_router(audio.router, prefix="/audio", tags=["Audio"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])

# Direct sessions endpoint to match original Flask route
@api_router.post("/sessions", tags=["Sessions"])
async def create_session():
    """Create a new ZoomBot session"""
    session_id = ZoomService.create_session()
    
    return {
        "session_id": session_id,
        "status": "created"
    }

@api_router.get("/status", tags=["System"])
async def status():
    """API status endpoint"""
    return {"status": "online", "version": "1.0.0"}
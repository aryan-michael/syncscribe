from fastapi import Header, HTTPException, Depends
from typing import Optional
from app.core.config import settings
from app.services.zoom_service import active_bots


async def verify_session_id(session_id: Optional[str] = Header(None, description="Session ID")):
    """
    Dependency to verify that a session ID exists and is valid
    """
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID is required")
    
    if session_id not in active_bots:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session_id


async def get_zoom_api_key_header(x_zoom_api_key: str = Header(..., description="Zoom API Key")):
    """
    Dependency to validate Zoom API key header
    """
    if x_zoom_api_key != settings.ZOOM_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_zoom_api_key


def get_optional_session_id(session_id: Optional[str] = Header(None, description="Session ID")):
    """
    Dependency for an optional session ID that will be created if not provided
    """
    return session_id
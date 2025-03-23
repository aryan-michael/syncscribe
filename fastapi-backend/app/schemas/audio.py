from typing import Optional, List
from pydantic import BaseModel, Field


class AudioProcessingResponse(BaseModel):
    """Response schema for audio processing results"""
    success: bool
    transcript: Optional[str] = None
    summary: Optional[str] = None
    insights: Optional[List[str]] = None
    error: Optional[str] = None


class StatusResponse(BaseModel):
    """Response schema for API status"""
    status: str
    version: str
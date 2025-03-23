from typing import Dict, Optional, List
from datetime import datetime
from pydantic import BaseModel

# This is just a placeholder class to maintain compatibility with the router and endpoints.
# The actual implementation is imported directly from zoombot.py at the service level.
class ZoomBot:
    """
    Placeholder for the ZoomBot class.
    The actual implementation is imported in the service layer.
    """
    pass

class MeetingStatus(BaseModel):
    """Model for tracking meeting status"""
    meeting_id: str
    session_id: str
    status: str = "created"  # created, joined, recording, ended
    recording: bool = False
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
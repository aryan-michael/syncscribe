from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CreateMeetingRequest(BaseModel):
    """Request schema for creating a meeting"""
    topic: str = Field(..., description="Topic or title of the meeting")
    duration: int = Field(60, description="Duration of the meeting in minutes")
    schedule_for: Optional[str] = Field(None, description="Email of the user to schedule for")
    user_id: str = Field("me", description="User ID to create the meeting under")
    session_id: Optional[str] = Field(None, description="Existing session ID")


class MeetingResponse(BaseModel):
    """Response schema for meeting info"""
    success: bool
    meeting_info: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    error: Optional[str] = None


class JoinMeetingRequest(BaseModel):
    """Request schema for joining a meeting"""
    meeting_id: str = Field(..., description="ID of the meeting to join")
    passcode: Optional[str] = Field(None, description="Meeting passcode if required")
    session_id: Optional[str] = Field(None, description="Existing session ID")


class ZoomSignatureRequest(BaseModel):
    """Request schema for Zoom signature generation"""
    meetingNumber: str = Field(..., description="Meeting number")
    role: int = Field(0, description="Role (0 for attendee, 1 for host)")


class ZoomSignatureResponse(BaseModel):
    """Response schema for Zoom signature generation"""
    signature: str
    sdkKey: str
    meetingNumber: str
    role: int
    success: bool
    expiration: int
    timestamp: int


class SessionRequest(BaseModel):
    """Request schema with session ID"""
    session_id: str = Field(..., description="Session ID")
    meeting_id: Optional[str] = Field(None, description="Meeting ID")


class MeetingStatusResponse(BaseModel):
    """Response schema for meeting status"""
    status: str
    recording: bool
    session_id: Optional[str] = None


class MeetingListResponse(BaseModel):
    """Response schema for meeting list"""
    success: bool
    meetings: List[Dict[str, Any]]
    session_id: str


class ReportInfo(BaseModel):
    """Schema for report file info"""
    filename: str
    path: str
    type: str


class ReportsResponse(BaseModel):
    """Response schema for reports list"""
    success: bool
    reports: List[ReportInfo] = []
    error: Optional[str] = None


class ReportContentResponse(BaseModel):
    """Response schema for report content"""
    success: bool
    content: Optional[str] = None
    filename: Optional[str] = None
    error: Optional[str] = None
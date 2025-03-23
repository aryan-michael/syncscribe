from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import uuid
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from zoombot import ZoomBot

from app.schemas.zoom import (
    CreateMeetingRequest, MeetingResponse, JoinMeetingRequest,
    ZoomSignatureRequest, ZoomSignatureResponse, SessionRequest,
    MeetingStatusResponse, MeetingListResponse
)
from app.services.zoom_service import ZoomService

router = APIRouter()

# @router.post("/sessions")
# async def create_session():
#     """Create a new ZoomBot session"""
#     session_id = str(uuid.uuid4())
#     active_bots[session_id] = ZoomBot()
    
#     return {
#         "session_id": session_id,
#         "status": "created"
#     }

@router.post("/signature", response_model=ZoomSignatureResponse)
async def generate_zoom_signature(request: ZoomSignatureRequest):
    """
    Generate a signature for Zoom Meeting SDK
    """
    success, signature_obj, error = ZoomService.generate_signature(
        request.meetingNumber,
        request.role
    )
    
    if not success:
        raise HTTPException(status_code=500, detail=error)
    
    return signature_obj

@router.post("/sessions")
async def create_session():
    """
    Create a new ZoomBot session
    """
    session_id = ZoomService.create_session()
    
    return {
        "session_id": session_id,
        "status": "created"
    }

@router.post("/meetings/create", response_model=MeetingResponse)
async def create_meeting(request: CreateMeetingRequest):
    """
    Create a new Zoom meeting
    """
    success, meeting_info, session_id, error = ZoomService.create_meeting(
        request.topic,
        request.duration,
        request.schedule_for,
        request.user_id,
        request.session_id
    )
    
    if not success:
        return {
            "success": False,
            "error": error,
            "session_id": session_id
        }
    
    return {
        "success": True,
        "meeting_info": meeting_info,
        "session_id": session_id
    }

@router.post("/meetings/join")
async def join_meeting(request_data: dict):
    """
    Join an existing Zoom meeting - debug version
    """
    print(f"Received raw request: {request_data}")
    
    # Extract fields manually
    meeting_id = request_data.get("meeting_id")
    passcode = request_data.get("passcode")
    session_id = request_data.get("session_id")
    
    if not meeting_id:
        return {
            "success": False,
            "error": "Meeting ID is required",
            "session_id": session_id
        }
    
    # Call your service
    success, session_id, meeting_id, error = ZoomService.join_meeting(
        meeting_id,
        passcode,
        session_id
    )
    
    if not success:
        return {
            "success": False,
            "error": error,
            "session_id": session_id
        }
    
    return {
        "success": True,
        "meeting_info": {"id": meeting_id},
        "session_id": session_id
    }


@router.post("/meetings/start-recording")
async def start_recording(request_data: dict):
    """
    Start recording a meeting
    """
    print(f"Received raw request: {request_data}")
    
    # Extract fields manually
    session_id = request_data.get("session_id")
    meeting_id = request_data.get("meeting_id")
    
    if not session_id:
        return {
            "success": False,
            "error": "Session ID is required"
        }
    
    # Call your service
    success, error = ZoomService.start_recording(session_id, meeting_id)
    
    if not success:
        return {
            "success": False,
            "error": error
        }
    
    return {"success": True, "message": "Recording started"}

@router.post("/meetings/stop-recording")
async def stop_recording(request_data: dict):
    """
    Stop recording a meeting
    """
    print(f"Received raw request: {request_data}")
    
    # Extract fields manually
    session_id = request_data.get("session_id")
    
    if not session_id:
        return {
            "success": False,
            "error": "Session ID is required"
        }
    
    # Call your service
    success, error = ZoomService.stop_recording(session_id)
    
    if not success:
        return {
            "success": False,
            "error": error
        }
    
    return {"success": True, "message": "Recording stopped"}

@router.post("/meetings/end")
async def end_meeting(request_data: dict):
    """
    End a Zoom meeting
    """
    print(f"Received raw request: {request_data}")
    
    # Extract fields manually
    meeting_id = request_data.get("meeting_id")
    session_id = request_data.get("session_id")
    
    if not meeting_id:
        return {
            "success": False,
            "error": "Meeting ID is required"
        }
    
    # Call your service
    success, error = ZoomService.end_meeting(meeting_id, session_id)
    
    if not success:
        return {
            "success": False,
            "error": error
        }
    
    return {"success": True, "message": "Meeting ended successfully"}

    
@router.get("/meetings/list", response_model=MeetingListResponse)
async def list_meetings(
    meeting_type: str = Query("scheduled", description="Meeting type (scheduled, live, upcoming)"),
    user_id: str = Query("me", description="User ID to list meetings for"),
    session_id: Optional[str] = Query(None, description="Session ID")
):
    """
    List Zoom meetings
    """
    success, meetings, session_id, error = ZoomService.list_meetings(
        user_id,
        meeting_type,
        session_id
    )
    
    if not success:
        return {
            "success": False,
            "meetings": [],
            "session_id": session_id,
            "error": error
        }
    
    return {
        "success": True,
        "meetings": meetings,
        "session_id": session_id
    }

@router.get("/meetings/status/{meeting_id}", response_model=MeetingStatusResponse)
async def meeting_status(
    meeting_id: str,
    session_id: Optional[str] = Query(None, description="Session ID")
):
    """
    Get status of a meeting
    """
    status = ZoomService.get_meeting_status(meeting_id, session_id)
    return status
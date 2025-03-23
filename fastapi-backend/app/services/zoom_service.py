import uuid
import time
import hmac
import hashlib
import base64
import sys
import os
from typing import Dict, List, Optional, Any, Tuple
from dotenv import load_dotenv

load_dotenv()

# Add the project root to Python path to import the ZoomBot from root directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from zoombot import ZoomBot

from app.core.config import settings

# Store active bots by session ID
active_bots: Dict[str, ZoomBot] = {}
# Track meeting statuses for frontend
meeting_statuses: Dict[str, Dict[str, Any]] = {}


class ZoomService:
    """Service for Zoom API interactions"""
    
    @staticmethod
    def create_session() -> str:
        """Create a new ZoomBot session"""
        session_id = str(uuid.uuid4())
        active_bots[session_id] = ZoomBot()
        return session_id
    
    @staticmethod
    def get_or_create_bot(session_id: Optional[str] = None) -> Tuple[ZoomBot, str]:
        """Get an existing bot or create a new one"""
        if not session_id or session_id not in active_bots:
            session_id = ZoomService.create_session()
        
        return active_bots[session_id], session_id
    
    @staticmethod
    def clean_meeting_info(meeting_info: Dict[str, Any]) -> Dict[str, Any]:
        """Clean meeting info to ensure it's JSON serializable"""
        if not meeting_info:
            return {}
            
        # Convert to dict if it's not already
        if not isinstance(meeting_info, dict):
            meeting_info = dict(meeting_info)
            
        # Remove any non-serializable objects
        clean_info = {}
        for key, value in meeting_info.items():
            # Skip non-serializable types
            if isinstance(value, (str, int, float, bool, list, dict)) or value is None:
                clean_info[key] = value
        
        return clean_info
    
    @staticmethod
    def create_meeting(
        topic: str,
        duration: int,
        schedule_for: Optional[str] = None,
        user_id: str = 'me',
        session_id: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any], str, Optional[str]]:
        """Create a new Zoom meeting"""
        bot, session_id = ZoomService.get_or_create_bot(session_id)
        
        try:
            # Create the meeting
            meeting_info = bot.create_meeting(topic, duration, schedule_for, user_id)
            
            if meeting_info:
                # Update meeting status
                meeting_id = str(meeting_info.get('id'))
                meeting_statuses[meeting_id] = {
                    "status": "created",
                    "recording": False,
                    "session_id": session_id
                }
                
                # Clean meeting info to ensure it's JSON serializable
                clean_info = ZoomService.clean_meeting_info(meeting_info)
                
                return True, clean_info, session_id, None
            else:
                return False, {}, session_id, "Failed to create meeting"
        except Exception as e:
            return False, {}, session_id, str(e)
    
    @staticmethod
    def join_meeting(
        meeting_id: str,
        passcode: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Tuple[bool, str, str, Optional[str]]:
        """Join an existing Zoom meeting"""
        bot, session_id = ZoomService.get_or_create_bot(session_id)
        
        try:
            # Join the meeting
            success = bot.join_meeting(meeting_id, passcode)
            
            if success:
                # Update meeting status
                meeting_statuses[meeting_id] = {
                    "status": "joined",
                    "recording": False,
                    "session_id": session_id
                }
                
                return True, session_id, meeting_id, None
            else:
                return False, session_id, meeting_id, "Failed to join meeting"
        except Exception as e:
            return False, session_id, meeting_id, str(e)
    
    @staticmethod
    def start_recording(session_id: str, meeting_id: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """Start recording a meeting"""
        if not session_id or session_id not in active_bots:
            return False, "Invalid session ID"
        
        bot = active_bots[session_id]
        
        try:
            # Verify we're in the right meeting if ID provided
            if meeting_id and hasattr(bot, 'meeting_id') and bot.meeting_id != meeting_id:
                return False, "Session is not connected to the specified meeting"
            
            # Start recording
            bot.start_recording()
            
            # Update status
            if hasattr(bot, 'meeting_id'):
                meeting_statuses[bot.meeting_id] = {
                    "status": "recording",
                    "recording": True,
                    "session_id": session_id
                }
            
            return True, None
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def stop_recording(session_id: str) -> Tuple[bool, Optional[str]]:
        """Stop recording a meeting"""
        if not session_id or session_id not in active_bots:
            return False, "Invalid session ID"
        
        bot = active_bots[session_id]
        
        try:
            # Keep meeting ID for status update
            meeting_id = bot.meeting_id if hasattr(bot, 'meeting_id') else None
            
            # Stop recording
            bot.stop_recording()
            
            # Update status
            if meeting_id:
                meeting_statuses[meeting_id] = {
                    "status": "joined",
                    "recording": False,
                    "session_id": session_id
                }
            
            return True, None
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def end_meeting(meeting_id: str, session_id: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """End a Zoom meeting"""
        if not meeting_id:
            return False, "Meeting ID is required"
        
        # Find session ID if not provided
        if not session_id or session_id not in active_bots:
            # Try to find a session with this meeting
            for sid, status in meeting_statuses.items():
                if status.get('meeting_id') == meeting_id:
                    session_id = status.get('session_id')
                    break
            
            if not session_id or session_id not in active_bots:
                return False, "Invalid session ID and no session found for this meeting"
        
        bot = active_bots[session_id]
        
        try:
            # Stop recording if it's running
            if hasattr(bot, 'recording') and bot.recording:
                bot.stop_recording()
            
            # End the meeting
            success = bot.end_meeting(meeting_id)
            
            if success:
                # Update status
                meeting_statuses[meeting_id] = {
                    "status": "ended",
                    "recording": False,
                    "session_id": session_id
                }
                
                return True, None
            else:
                return False, "Failed to end meeting"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def list_meetings(
        user_id: str = 'me',
        meeting_type: str = 'scheduled',
        session_id: Optional[str] = None
    ) -> Tuple[bool, List[Dict[str, Any]], str, Optional[str]]:
        """List Zoom meetings"""
        bot, session_id = ZoomService.get_or_create_bot(session_id)
        
        try:
            # List meetings
            meetings = bot.list_meetings(user_id, meeting_type)
            
            clean_meetings = []
            if meetings and 'meetings' in meetings:
                # Clean meetings info
                for meeting in meetings['meetings']:
                    clean_meetings.append(ZoomService.clean_meeting_info(meeting))
            
            return True, clean_meetings, session_id, None
        except Exception as e:
            return False, [], session_id, str(e)
    
    @staticmethod
    def get_meeting_status(meeting_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get status of a meeting"""
        if meeting_id in meeting_statuses:
            return meeting_statuses[meeting_id]
        
        # Try to check status via API
        if session_id and session_id in active_bots:
            bot = active_bots[session_id]
            
            try:
                # Get token first
                if not bot.token:
                    bot.get_zoom_token()
                
                # Check meeting
                is_active = bot._is_meeting_active(meeting_id)
                
                status = "active" if is_active else "ended"
                
                return {
                    "status": status,
                    "recording": False,
                    "session_id": session_id
                }
            except:
                pass
        
        return {
            "status": "unknown",
            "recording": False
        }
    
    @staticmethod
    def generate_signature(meeting_number: str, role: int = 0) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """Generate a signature for Zoom Meeting SDK"""
        try:
            # Get SDK key and secret from environment variables
            sdk_key = settings.ZOOM_SDK_KEY
            sdk_secret = settings.ZOOM_SDK_SECRET
            
            if not sdk_key or not sdk_secret:
                return False, {}, "Zoom SDK credentials not configured"
            
            # Generate timestamp (expires in 24 hours)
            timestamp = int(time.time() * 1000) - 30000
            expiration = timestamp + 86400 * 1000  # 24 hours
            
            # Create the signature data
            msg = f"{sdk_key}{meeting_number}{timestamp}{role}{expiration}"
            msg_bytes = msg.encode('utf-8')
            secret_bytes = sdk_secret.encode('utf-8')
            
            # Generate the signature
            hmac_obj = hmac.new(secret_bytes, msg_bytes, hashlib.sha256)
            hmac_digest = hmac_obj.digest()
            
            # Encode as base64
            signature = base64.b64encode(hmac_digest).decode('utf-8')
            
            # Create signature object
            signature_obj = {
                "signature": signature,
                "sdkKey": sdk_key,
                "meetingNumber": meeting_number,
                "role": role,
                "success": True,
                "expiration": expiration,
                "timestamp": timestamp
            }
            
            return True, signature_obj, None
        
        except Exception as e:
            return False, {}, str(e)
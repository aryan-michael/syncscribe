import hmac
import hashlib
import base64
import time
from typing import Dict, Any
from app.core.config import settings


def generate_zoom_signature(meeting_number: str, role: int = 0) -> Dict[str, Any]:
    """
    Generate a signature for Zoom Meeting SDK
    
    Args:
        meeting_number: The meeting number
        role: 0 for attendee, 1 for host
        
    Returns:
        Dict containing signature and related info
    """
    sdk_key = settings.ZOOM_SDK_KEY
    sdk_secret = settings.ZOOM_SDK_SECRET
    
    if not sdk_key or not sdk_secret:
        raise ValueError("Zoom SDK credentials not configured")
    
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
    
    return signature_obj
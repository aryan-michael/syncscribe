import os
from dotenv import load_dotenv
import speech_recognition as sr
import cohere
from google.cloud import aiplatform
from google.oauth2 import service_account
from vertexai.generative_models import GenerativeModel
import requests
import json
import time
import threading

load_dotenv()

# Direct Zoom authentication function that we know works
def get_zoom_token():
    client_id = os.getenv("ZOOM_CLIENT_ID")
    client_secret = os.getenv("ZOOM_CLIENT_SECRET")
    account_id = os.getenv("ZOOM_ACCOUNT_ID")
    
    url = "https://zoom.us/oauth/token"
    data = {
        "grant_type": "account_credentials",
        "account_id": account_id,
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    response = requests.post(url, data=data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Failed to get Zoom token: {response.text}")
        return None

def join_meeting(meeting_id, passcode=None):
    # Get token using the method we know works
    token = get_zoom_token()
    if not token:
        print("Failed to authenticate with Zoom")
        return False
    
    # Get meeting details
    meeting_url = f"https://api.zoom.us/v2/meetings/{meeting_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(meeting_url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to get meeting details: {response.text}")
        return False
    
    meeting_data = response.json()
    print(f"Successfully connected to meeting: {meeting_data['topic']}")
    print("Ready to record and transcribe...")
    
    return True

# Test joining a meeting
if __name__ == "__main__":
    meeting_id = input("Enter Zoom Meeting ID: ")
    passcode = input("Enter meeting passcode (leave blank if none): ") or None
    
    if join_meeting(meeting_id, passcode):
        print("Successfully connected to meeting!")
        # Here you would start your recording code
    else:
        print("Failed to connect to meeting.")
import os
from dotenv import load_dotenv
import speech_recognition as sr
from google.cloud import speech_v1p1beta1 as speech
import cohere
from google.cloud import aiplatform
from google.oauth2 import service_account
from vertexai.generative_models import GenerativeModel
import requests
import time
import threading
import io
import pyaudio
import wave
import queue
import sys
import json
import uuid
import datetime

load_dotenv()

class ZoomBot:
    def __init__(self):
        # Initialize recording variables
        self.recording = False
        self.transcript_buffer = []
        self.full_transcript = ""
        self.summary_counter = 0
        
        # Audio recording settings
        self.rate = 16000  # Matches Google's preferred rate
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1  # Mono
        
        # Initialize Google Cloud Speech client
        self.speech_client = speech.SpeechClient.from_service_account_json(
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS", 
                    "/Users/siraryanmichael/syncscribe/syncscribe-454510-6b6e3db310f5.json")
        )
        
        # Initialize AI services
        self.cohere_api_key = os.getenv("COHERE_API_KEY")
        self.co = cohere.Client(self.cohere_api_key)
        
        # Initialize Vertex AI
        credentials = service_account.Credentials.from_service_account_file(
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS", 
                      "/Users/siraryanmichael/syncscribe/syncscribe-454510-6b6e3db310f5.json")
        )
        aiplatform.init(
            project=os.getenv("GOOGLE_CLOUD_PROJECT", "syncscribe-454510"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
            credentials=credentials
        )
        
        # Create output directory if it doesn't exist
        os.makedirs("meeting_outputs", exist_ok=True)
        
        # For meeting status checking
        self.token = None
        self.meeting_check_thread = None
        self.last_audio_time = None
        self.silence_threshold = 60  # seconds of silence to assume meeting is over
        
        # For meeting creation
        self.created_meeting_id = None
        self.created_meeting_password = None
        self.created_meeting_join_url = None
        self.created_meeting_start_url = None
    
    def get_zoom_token(self):
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
            self.token = response.json()["access_token"]
            return self.token
        else:
            print(f"Failed to get Zoom token: {response.text}")
            return None
    
    def create_meeting(self, topic, duration=60, schedule_for=None, user_id="me"):
        """
        Create a new Zoom meeting and return meeting details
        
        Parameters:
        - topic: Meeting topic/title
        - duration: Meeting duration in minutes (default: 60)
        - schedule_for: Schedule meeting for this timestamp (ISO format)
        - user_id: Zoom user ID to create meeting for (default: "me" for your own account)
        
        Returns:
        - Dictionary with meeting details or None if failed
        """
        token = self.get_zoom_token()
        if not token:
            print("Failed to authenticate with Zoom")
            return None
        
        # Use current time as default if no schedule time provided
        if not schedule_for:
            # Format as ISO-8601 string
            schedule_for = datetime.datetime.now().isoformat()
        
        # Generate random password if enabled
        password = str(uuid.uuid4())[:8]  # Use first 8 chars of UUID as password
        
        # Prepare meeting data
        meeting_data = {
            "topic": topic,
            "type": 2,  # Scheduled meeting
            "duration": duration,
            "timezone": "UTC",
            "start_time": schedule_for,
            "password": password,
            "settings": {
                "host_video": True,
                "participant_video": True,
                "join_before_host": True,
                "mute_upon_entry": False,
                "auto_recording": "cloud",  # Options: none, local, cloud
                "waiting_room": False
            }
        }
        
        # Create meeting API endpoint
        api_url = f"https://api.zoom.us/v2/users/{user_id}/meetings"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(api_url, headers=headers, json=meeting_data)
            
            if response.status_code == 201:  # 201 Created
                meeting_info = response.json()
                
                # Store created meeting details
                self.created_meeting_id = meeting_info['id']
                self.created_meeting_password = meeting_info['password']
                self.created_meeting_join_url = meeting_info['join_url']
                self.created_meeting_start_url = meeting_info['start_url']
                
                # Print success message with meeting details
                print(f"Meeting created successfully!")
                print(f"Meeting ID: {self.created_meeting_id}")
                print(f"Password: {self.created_meeting_password}")
                print(f"Join URL: {self.created_meeting_join_url}")
                
                return meeting_info
            else:
                print(f"Failed to create meeting: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error creating meeting: {e}")
            return None
    
    def list_meetings(self, user_id="me", meeting_type="scheduled"):
        """
        List Zoom meetings for a user
        
        Parameters:
        - user_id: Zoom user ID (default: "me" for your own account)
        - meeting_type: Type of meetings to list (scheduled, live, upcoming)
        
        Returns:
        - List of meetings or None if failed
        """
        token = self.get_zoom_token()
        if not token:
            print("Failed to authenticate with Zoom")
            return None
            
        # Map meeting type to Zoom API parameter
        type_map = {
            "scheduled": "scheduled",
            "live": "live",
            "upcoming": "upcoming"
        }
        
        meeting_type_param = type_map.get(meeting_type, "scheduled")
        
        # List meetings API endpoint
        api_url = f"https://api.zoom.us/v2/users/{user_id}/meetings"
        params = {
            "type": meeting_type_param,
            "page_size": 30  # Number of meetings to return
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(api_url, headers=headers, params=params)
            
            if response.status_code == 200:
                meetings = response.json()
                
                # Print meeting list in a readable format
                if meetings.get("meetings"):
                    print(f"\nFound {len(meetings['meetings'])} {meeting_type} meetings:")
                    for i, meeting in enumerate(meetings["meetings"], 1):
                        print(f"{i}. {meeting['topic']} (ID: {meeting['id']})")
                        print(f"   Start Time: {meeting.get('start_time', 'N/A')}")
                        print(f"   Join URL: {meeting.get('join_url', 'N/A')}")
                        print(f"   Password: {meeting.get('password', 'N/A')}\n")
                else:
                    print(f"No {meeting_type} meetings found.")
                
                return meetings
            else:
                print(f"Failed to list meetings: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error listing meetings: {e}")
            return None
    
    def join_meeting(self, meeting_id=None, passcode=None):
        """Join a Zoom meeting using Server-to-Server OAuth app"""
        # Use created meeting ID and password if none provided
        if meeting_id is None and self.created_meeting_id:
            meeting_id = self.created_meeting_id
            print(f"Using created meeting ID: {meeting_id}")
            
        if passcode is None and self.created_meeting_password:
            passcode = self.created_meeting_password
            print(f"Using created meeting password: {passcode}")
            
        if meeting_id is None:
            print("No meeting ID provided or created. Cannot join meeting.")
            return False
            
        token = self.get_zoom_token()
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
        
        self.meeting_id = meeting_id
        self.meeting_topic = meeting_data['topic']
        
        # Start multiple threads for checking meeting status
        self._start_meeting_monitoring()
        
        return True
    
    def end_meeting(self, meeting_id=None):
        """
        End a running Zoom meeting
        
        Parameters:
        - meeting_id: Meeting ID to end (default: uses the current/last created meeting)
        
        Returns:
        - True if meeting ended successfully, False otherwise
        """
        # Use current/created meeting ID if none provided
        if meeting_id is None:
            if hasattr(self, 'meeting_id') and self.meeting_id:
                meeting_id = self.meeting_id
            elif self.created_meeting_id:
                meeting_id = self.created_meeting_id
            else:
                print("No meeting ID provided or available. Cannot end meeting.")
                return False
        
        token = self.get_zoom_token()
        if not token:
            print("Failed to authenticate with Zoom")
            return False
        
        # End meeting API endpoint
        api_url = f"https://api.zoom.us/v2/meetings/{meeting_id}/status"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Prepare end meeting request
        end_data = {
            "action": "end"
        }
        
        try:
            response = requests.put(api_url, headers=headers, json=end_data)
            
            if response.status_code in [204, 200]:  # Success codes
                print(f"Meeting {meeting_id} ended successfully.")
                
                # Stop recording if it's running
                if self.recording:
                    self.stop_recording()
                
                return True
            else:
                print(f"Failed to end meeting: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Error ending meeting: {e}")
            return False
    
    def setup_webhooks(self, endpoint_url=None):
        """
        Set up webhooks to listen for meeting events (for advanced users)
        Note: You'll need to implement a web server to receive these events
        
        Parameters:
        - endpoint_url: The URL where Zoom will send webhook events
        
        Returns:
        - True if webhook configured successfully, False otherwise
        """
        if not endpoint_url:
            print("No endpoint URL provided for webhooks.")
            return False
            
        token = self.get_zoom_token()
        if not token:
            print("Failed to authenticate with Zoom")
            return False
            
        # Create webhook subscription
        api_url = "https://api.zoom.us/v2/webhooks"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Define events to listen for
        webhook_data = {
            "url": endpoint_url,
            "event_types": [
                "meeting.started",
                "meeting.ended",
                "meeting.participant_joined",
                "meeting.participant_left"
            ]
        }
        
        try:
            response = requests.post(api_url, headers=headers, json=webhook_data)
            
            if response.status_code == 201:  # Created
                webhook_info = response.json()
                print(f"Webhook configured successfully. Webhook ID: {webhook_info.get('id')}")
                return True
            else:
                print(f"Failed to configure webhook: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Error configuring webhook: {e}")
            return False
    
    def _start_meeting_monitoring(self):
        """Start all threads for monitoring the meeting status"""
        # Thread 1: API-based status check
        self.meeting_check_thread = threading.Thread(target=self._check_meeting_status_api)
        self.meeting_check_thread.daemon = True
        self.meeting_check_thread.start()
        
        # Thread 2: Silence detection (backup method)
        self.silence_check_thread = threading.Thread(target=self._check_silence)
        self.silence_check_thread.daemon = True
        self.silence_check_thread.start()
        
        # Thread 3: Connection status check
        self.connection_check_thread = threading.Thread(target=self._check_connection_status)
        self.connection_check_thread.daemon = True
        self.connection_check_thread.start()
        
        # Thread 4: Meeting ended event check
        self.ended_event_thread = threading.Thread(target=self._check_meeting_ended_event)
        self.ended_event_thread.daemon = True
        self.ended_event_thread.start()
    
    def _check_meeting_status_api(self):
        """Periodically check if the meeting is still active via API"""
        while self.recording:
            try:
                # Check meeting status every 5 seconds instead of 15
                time.sleep(5)
                
                # Check if meeting is still active via Zoom API
                if not self._is_meeting_active():
                    print("\nAPI: Detected that the meeting has ended. Stopping recording...")
                    self.stop_recording()
                    break
            except Exception as e:
                print(f"Error checking meeting status via API: {e}")
    
    def _check_meeting_ended_event(self):
        """Specifically check for meeting ended event"""
        while self.recording:
            try:
                # Check every 7 seconds (staggered from other checks)
                time.sleep(7)
                
                if not self.token:
                    self.get_zoom_token()
                    
                # Use the most direct endpoint for meeting status
                end_check_url = f"https://api.zoom.us/v2/meetings/{self.meeting_id}/status"
                headers = {
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json"
                }
                
                response = requests.get(end_check_url, headers=headers)
                
                # If we get a success response, check the status
                if response.status_code == 200:
                    data = response.json()
                    if 'status' in data and data['status'] in ['ended', 'inactive']:
                        print("\nAPI: Meeting status endpoint reports meeting has ended.")
                        self.stop_recording()
                        break
                elif response.status_code in [404, 400, 401]:
                    # These status codes often indicate the meeting is over
                    print("\nAPI: Meeting status endpoint suggests meeting is over.")
                    self.stop_recording()
                    break
            except Exception as e:
                print(f"Error in meeting ended event check: {e}")
    
    def _check_silence(self):
        """Check for extended periods of silence as a backup method"""
        self.last_audio_time = time.time()
        
        while self.recording:
            try:
                time.sleep(10)  # Check every 10 seconds
                
                current_time = time.time()
                if self.last_audio_time and (current_time - self.last_audio_time) > self.silence_threshold:
                    print(f"\nSilence: No audio detected for {self.silence_threshold} seconds. Meeting appears to be over.")
                    self.stop_recording()
                    break
            except Exception as e:
                print(f"Error in silence detection: {e}")
    
    def _check_connection_status(self):
        """Check if we're still connected to the meeting"""
        while self.recording:
            try:
                # Check connection every 20 seconds
                time.sleep(20)
                
                # Send a ping request to Zoom API to verify connectivity
                if not self._ping_meeting():
                    print("\nConnection: Lost connection to Zoom meeting. Stopping recording...")
                    self.stop_recording()
                    break
            except Exception as e:
                print(f"Error checking connection status: {e}")
    
    def _ping_meeting(self):
        """Simple ping to see if we still have API access to the meeting"""
        try:
            if not self.token:
                self.get_zoom_token()
                
            check_url = f"https://api.zoom.us/v2/metrics/meetings/{self.meeting_id}"
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(check_url, headers=headers)
            return response.status_code in [200, 201, 202, 204]
        except:
            return False
    
    def _is_meeting_active(self):
        """Check if the meeting is still active using Zoom API"""
        try:
            # Refresh token if needed
            if not self.token:
                self.get_zoom_token()
            
            # Use a more reliable endpoint to check meeting status
            status_url = f"https://api.zoom.us/v2/metrics/meetings/{self.meeting_id}"
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(status_url, headers=headers)
            
            if response.status_code == 200:
                status_data = response.json()
                
                # If meeting data shows status as "ended"
                if 'status' in status_data and status_data['status'] in ['ended', 'finished']:
                    print("API detected meeting status as ended")
                    return False
                    
                # Check participants - if zero, meeting is likely over
                if 'participants_count' in status_data and status_data['participants_count'] == 0:
                    print("API detected zero participants")
                    return False
                    
                # Try to get meeting details using another endpoint as backup verification
                meeting_url = f"https://api.zoom.us/v2/meetings/{self.meeting_id}"
                meeting_response = requests.get(meeting_url, headers=headers)
                
                # If we get a 404, meeting has been ended and removed
                if meeting_response.status_code == 404:
                    print("API: Meeting no longer exists (404)")
                    return False
                
                return True
            elif response.status_code == 404:
                # 404 typically means the meeting is no longer active
                print("API: Meeting metrics not found (404)")
                return False
            else:
                print(f"Failed to get meeting status: {response.status_code} - {response.text}")
                # Add a more aggressive check if we get unexpected status codes
                try:
                    # Directly check if meeting exists
                    direct_url = f"https://api.zoom.us/v2/meetings/{self.meeting_id}"
                    direct_response = requests.get(direct_url, headers=headers)
                    if direct_response.status_code != 200:
                        print("API: Meeting likely ended (direct check failed)")
                        return False
                except:
                    pass
                return True  # Default to assuming meeting is still active
        except Exception as e:
            print(f"Error checking meeting status: {e}")
            return True  # Assume meeting is still active if we can't check
    
    def start_recording(self):
        """Start recording and transcribing the meeting audio using streaming recognition"""
        self.recording = True
        self.transcript_buffer = []
        self.full_transcript = ""
        self.summary_counter = 0
        self.meeting_start_time = time.strftime("%Y-%m-%d_%H-%M-%S")
        
        # Start streaming transcription in a separate thread
        self.transcription_thread = threading.Thread(target=self._stream_transcribe_audio)
        self.transcription_thread.daemon = True
        self.transcription_thread.start()
        
        print("Recording started...")
        print("Meeting in progress. Press Ctrl+C to manually end recording or wait for meeting to end automatically.")
    
    def _stream_transcribe_audio(self):
        """Stream audio to Google Cloud Speech API with speaker diarization"""
        # Set up audio stream
        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk
        )
        
        # Configuration for streaming with speaker diarization
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=self.rate,
            language_code="en-US",
            enable_speaker_diarization=True,
            diarization_speaker_count=2,  # Can be adjusted based on expected number of speakers
            enable_automatic_punctuation=True,
            use_enhanced=True,
        )
        streaming_config = speech.StreamingRecognitionConfig(
            config=config,
            interim_results=True
        )
        
        # Generator for streaming audio chunks
        def audio_generator():
            while self.recording:
                try:
                    data = stream.read(self.chunk, exception_on_overflow=False)
                    # Update last audio time whenever we get audio data
                    self.last_audio_time = time.time()
                    yield data
                except Exception as e:
                    print(f"Error reading audio: {e}")
                    time.sleep(0.1)  # Prevent tight loop on error
        
        try:
            print("Starting transcription stream...")
            # Create streaming recognize requests
            requests = (speech.StreamingRecognizeRequest(audio_content=content) 
                        for content in audio_generator())
            
            # Get streaming responses
            responses = self.speech_client.streaming_recognize(streaming_config, requests)
            
            # Process responses
            self._process_responses(responses)
            
        except Exception as e:
            print(f"Error in streaming transcription: {e}")
        finally:
            # Clean up
            stream.stop_stream()
            stream.close()
            audio.terminate()
            print("Audio stream closed.")
    
    def _process_responses(self, responses):
        """Process streaming responses with speaker diarization"""
        for response in responses:
            if not response.results or not self.recording:
                continue
                
            result = response.results[0]
            if not result.alternatives:
                continue
                
            alternative = result.alternatives[0]
            transcript = alternative.transcript
            
            # Extract speaker tag if available
            speaker_tag = None
            if hasattr(alternative, 'words') and alternative.words:
                for word in alternative.words:
                    if hasattr(word, 'speaker_tag') and word.speaker_tag:
                        speaker_tag = word.speaker_tag
                        break
            
            if result.is_final:
                # Format with speaker information
                speaker_label = f"Speaker {speaker_tag}" if speaker_tag is not None else "Unknown"
                final_text = f"{speaker_label}: {transcript}"
                
                # Display and save final transcription
                timestamp = time.strftime("%H:%M:%S")
                print(f"[{timestamp}] {final_text}")
                
                # Save to buffer and file
                self.transcript_buffer.append(final_text)
                self.full_transcript += f"{final_text} "
                self._save_interim_transcript(timestamp, final_text)
                
                # Generate periodic summaries
                self.summary_counter += 1
                if self.summary_counter >= 5:  # Summarize every 5 final results
                    summary = self._generate_live_summary(self.full_transcript)
                    print("\nLive Summary:")
                    print(summary)
                    print("\nContinuing transcription...\n")
                    
                    # Save the live summary
                    self._save_live_summary(summary)
                    
                    self.summary_counter = 0  # Reset counter
            else:
                # Display interim results
                speaker_label = f"Speaker {speaker_tag}" if speaker_tag is not None else "Unknown"
                sys.stdout.write(f"\rLive: {speaker_label}: {transcript}")
                sys.stdout.flush()
    
    def _generate_live_summary(self, text):
        """Generate a live summary using Cohere"""
        try:
            response = self.co.generate(
                prompt=f"Summarize this part of the meeting transcript: {text}",
                max_tokens=100,
                temperature=0.7
            )
            return response.generations[0].text.strip()
        except Exception as e:
            print(f"Error generating live summary: {e}")
            return "Live summary generation failed."
    
    def _save_live_summary(self, summary):
        """Save the live summary to a file"""
        try:
            with open(f"meeting_outputs/live_summaries_{self.meeting_start_time}.txt", "a") as f:
                timestamp = time.strftime("%H:%M:%S")
                f.write(f"[{timestamp}] LIVE SUMMARY:\n{summary}\n\n")
        except Exception as e:
            print(f"Error saving live summary: {e}")
    
    def _save_interim_transcript(self, timestamp, text):
        """Save interim transcript without processing or summarizing"""
        try:
            with open(f"meeting_outputs/interim_transcript_{self.meeting_start_time}.txt", "a") as f:
                f.write(f"[{timestamp}] {text}\n")
        except Exception as e:
            print(f"Error saving interim transcript: {e}")
    
    def stop_recording(self):
        """Stop recording and generate final report"""
        if not self.recording:
            return  # Already stopped
            
        self.recording = False
        print("\nStopping recording...")
        
        # Wait for transcription thread to finish
        if hasattr(self, 'transcription_thread') and self.transcription_thread.is_alive():
            self.transcription_thread.join(timeout=3)
        
        # Process complete transcript
        if self.transcript_buffer:
            print("Generating summary and insights...")
            
            # Save raw transcript first
            raw_transcript_file = f"meeting_outputs/raw_transcript_{self.meeting_start_time}.txt"
            with open(raw_transcript_file, "w") as f:
                full_transcript = " ".join(self.transcript_buffer)
                f.write(full_transcript)
            print(f"Raw transcript saved to {raw_transcript_file}")
            
            print("Generating summary with Cohere...")
            summary = self._generate_summary(full_transcript)
            
            print("Generating insights with Vertex AI Gemini...")
            insights = self._generate_insights(summary)
            
            # Save final report
            self._save_report(full_transcript, summary, insights)
            
            print("Final report generated successfully.")
        else:
            print("No transcript recorded.")
    
    def _generate_summary(self, text):
        """Generate summary using Cohere"""
        try:
            response = self.co.generate(
                prompt=f"Summarize this meeting transcript concisely: {text}",
                max_tokens=250,
                temperature=0.7
            )
            return response.generations[0].text.strip()
        except Exception as e:
            print(f"Error generating summary: {e}")
            return "Summary generation failed."
    
    def _generate_insights(self, summary):
        """Generate insights using Vertex AI's Gemini model"""
        try:
            model = GenerativeModel("gemini-pro")
            response = model.generate_content(
                f"Analyze this meeting summary and provide key insights, action items, and decisions made: {summary}"
            )
            return response.text
        except Exception as e:
            print(f"Error generating insights: {e}")
            return "Insight generation failed."
    
    def _save_report(self, transcript, summary, insights):
        """Save the complete meeting report to a file"""
        filename = f"meeting_outputs/meeting_report_{self.meeting_start_time}.txt"
        
        with open(filename, "w") as f:
            f.write(f"# MEETING REPORT: {self.meeting_topic}\n\n")
            f.write(f"Date: {time.strftime('%Y-%m-%d')}\n")
            f.write(f"Time: {time.strftime('%H:%M:%S')}\n")
            f.write(f"Meeting ID: {self.meeting_id}\n\n")
            
            f.write("## SUMMARY\n\n")
            f.write(f"{summary}\n\n")
            
            f.write("## INSIGHTS AND ACTION ITEMS\n\n")
            f.write(f"{insights}\n\n")
            
            f.write("## FULL TRANSCRIPT\n\n")
            f.write(f"{transcript}")
        
        print(f"Meeting report saved to {filename}")
        return filename


# Updated usage example with new meeting creation capabilities
if __name__ == "__main__":
    bot = ZoomBot()
    
    while True:
        # Display menu of options
        print("\n=== SyncScribe Zoom Bot ===")
        print("1. Create a new meeting")
        print("2. List scheduled meetings")
        print("3. Join an existing meeting")
        print("4. Create meeting, join immediately and start recording")
        print("5. Exit")
        
        choice = input("\nSelect an option (1-5): ")
        
        if choice == "1":
            # Create a new meeting
            topic = input("Enter meeting topic: ")
            duration = int(input("Enter meeting duration in minutes (default: 60): ") or "60")
            
            meeting_info = bot.create_meeting(topic, duration)
            if meeting_info:
                print("\nMeeting created successfully!")
                print(f"Meeting ID: {meeting_info['id']}")
                print(f"Password: {meeting_info['password']}")
                print(f"Join URL: {meeting_info['join_url']}")
                
                # Ask if user wants to join now
                join_now = input("\nDo you want to join this meeting now? (y/n): ").lower()
                if join_now == 'y':
                    if bot.join_meeting(meeting_info['id'], meeting_info['password']):
                        bot.start_recording()
                        
                        try:
                            # Keep the main thread running
                            while bot.recording:
                                time.sleep(1)
                        except KeyboardInterrupt:
                            print("\nManually ending recording...")
                            bot.stop_recording()
            
        elif choice == "2":
            # List meetings
            meeting_type = input("Enter meeting type (scheduled, live, upcoming) [default: scheduled]: ") or "scheduled"
            bot.list_meetings(meeting_type=meeting_type)
            
        elif choice == "3":
            # Join existing meeting
            meeting_id = input("Enter Zoom Meeting ID: ")
            passcode = input("Enter meeting passcode (leave blank if none): ") or None
            
            if bot.join_meeting(meeting_id, passcode):
                bot.start_recording()
                
                try:
                    # Keep the main thread running
                    while bot.recording:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\nManually ending recording...")
                    bot.stop_recording()
        
        elif choice == "4":
            # Create and join immediately
            topic = input("Enter meeting topic: ")
            duration = int(input("Enter meeting duration in minutes (default: 60): ") or "60")
            
            meeting_info = bot.create_meeting(topic, duration)
            if meeting_info:
                print("\nMeeting created, joining now...")
                if bot.join_meeting(meeting_info['id'], meeting_info['password']):
                    print("Starting recording...")
                    bot.start_recording()
                    
                    try:
                        # Keep the main thread running
                        while bot.recording:
                            time.sleep(1)
                    except KeyboardInterrupt:
                        print("\nManually ending recording...")
                        bot.stop_recording()
        
        elif choice == "5":
            print("Exiting SyncScribe Zoom Bot. Goodbye!")
            break
            
        else:
            print("Invalid option. Please try again.")
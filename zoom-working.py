import os
from dotenv import load_dotenv
import speech_recognition as sr
import cohere
from google.cloud import aiplatform
from google.oauth2 import service_account
from vertexai.generative_models import GenerativeModel
import requests
import time
import threading

load_dotenv()

class ZoomBot:
    def __init__(self):
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        self.recording = False
        self.transcript_buffer = []
        
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
            return response.json()["access_token"]
        else:
            print(f"Failed to get Zoom token: {response.text}")
            return None
    
    def join_meeting(self, meeting_id, passcode=None):
        """Join a Zoom meeting using Server-to-Server OAuth app"""
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
        return True
    
    def start_recording(self):
        """Start recording and transcribing the meeting audio"""
        self.recording = True
        self.transcript_buffer = []
        self.meeting_start_time = time.strftime("%Y-%m-%d_%H-%M-%S")
        
        # Start the recording in a separate thread
        self.recording_thread = threading.Thread(target=self._record_audio)
        self.recording_thread.daemon = True
        self.recording_thread.start()
        
        print("Recording started...")
    
    def stop_recording(self):
        """Stop recording and generate final report"""
        self.recording = False
        
        if hasattr(self, 'recording_thread') and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=2)
        
        # Process complete transcript
        if self.transcript_buffer:
            full_transcript = " ".join(self.transcript_buffer)
            summary = self._generate_summary(full_transcript)
            insights = self._generate_insights(summary)
            
            # Save final report
            self._save_report(full_transcript, summary, insights)
            
            print("Recording stopped. Final report generated.")
        else:
            print("No transcript recorded.")
    
    def _record_audio(self):
        """Record audio from microphone and transcribe in real-time"""
        with sr.Microphone() as source:
            print("Adjusting for background noise...")
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
            print("Listening to meeting...")
            
            while self.recording:
                try:
                    audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=30)
                    text = self.recognizer.recognize_google(audio)
                    
                    if text:
                        timestamp = time.strftime("%H:%M:%S")
                        print(f"[{timestamp}] Transcribed: {text[:50]}..." if len(text) > 50 else f"[{timestamp}] Transcribed: {text}")
                        self.transcript_buffer.append(text)
                        
                        # Process in chunks if buffer gets large
                        if len(self.transcript_buffer) >= 5:
                            chunk_text = " ".join(self.transcript_buffer[-5:])
                            threading.Thread(target=self._process_text_chunk, 
                                            args=(chunk_text,)).start()
                    
                except sr.UnknownValueError:
                    print("Could not understand audio")
                except sr.RequestError as e:
                    print(f"Google API error: {e}")
                except Exception as e:
                    print(f"Error in recording: {e}")
    
    def _process_text_chunk(self, text):
        """Process a chunk of transcribed text"""
        try:
            # Generate interim summary for large chunks
            summary = self._generate_summary(text)
            print(f"Interim Summary: {summary}")
            
            # Save interim data
            timestamp = time.strftime("%H:%M:%S")
            with open(f"meeting_outputs/interim_{self.meeting_start_time}.txt", "a") as f:
                f.write(f"\n\n--- {timestamp} ---\n")
                f.write(f"Transcription:\n{text}\n\n")
                f.write(f"Summary:\n{summary}\n")
        except Exception as e:
            print(f"Error processing text chunk: {e}")
    
    def _generate_summary(self, text):
        """Generate summary using Cohere"""
        try:
            response = self.co.generate(
                prompt=f"Summarize this meeting transcript concisely: {text}",
                max_tokens=150,
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

# Usage example
if __name__ == "__main__":
    bot = ZoomBot()
    
    meeting_id = input("Enter Zoom Meeting ID: ")
    passcode = input("Enter meeting passcode (leave blank if none): ") or None
    
    if bot.join_meeting(meeting_id, passcode):
        bot.start_recording()
        
        print("Recording meeting. Press Ctrl+C to stop...")
        try:
            # Keep the main thread running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Stopping recording...")
            bot.stop_recording()
import os
import tempfile
from typing import List, Tuple, Optional
import speech_recognition as sr
from pydub import AudioSegment
import cohere
from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel
from app.core.config import settings

# Initialize external services
co = cohere.Client(settings.COHERE_API_KEY)

credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", settings.GOOGLE_APPLICATION_CREDENTIALS)
project_id = os.getenv("GOOGLE_CLOUD_PROJECT", settings.GOOGLE_CLOUD_PROJECT)
location = os.getenv("GOOGLE_CLOUD_LOCATION", settings.GOOGLE_CLOUD_LOCATION)

if settings.GOOGLE_APPLICATION_CREDENTIALS:
    aiplatform.init(
        project=settings.GOOGLE_CLOUD_PROJECT,
        location=settings.GOOGLE_CLOUD_LOCATION,
    )


class AudioService:
    """Service for processing audio files"""
    
    @staticmethod
    async def process_audio(file) -> Tuple[bool, str, Optional[str], Optional[List[str]], Optional[str]]:
        """Process audio file and return transcript, summary, and insights"""
        try:
            # Check file extension
            filename = file.filename
            if not filename.lower().endswith(('.wav', '.mp3', '.m4a', '.ogg')):
                return False, None, None, None, "Unsupported file format. Please upload WAV, MP3, M4A, or OGG files."
            
            # Create a temporary file to store the uploaded audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
                temp_path = temp_audio.name
            
            # Convert non-WAV formats to WAV if needed
            try:
                if filename.lower().endswith('.wav'):
                    # Save directly if already WAV
                    with open(temp_path, "wb") as f:
                        f.write(file.file.read())
                else:
                    # For non-WAV formats, convert using pydub
                    temp_original = temp_path + "_original"
                    with open(temp_original, "wb") as f:
                        f.write(file.file.read())
                    
                    sound = AudioSegment.from_file(temp_original)
                    sound.export(temp_path, format="wav")
                    # Clean up the original file
                    os.unlink(temp_original)
            except Exception as e:
                return False, None, None, None, f"Error processing audio file: {str(e)}"
            
            # Initialize speech recognition
            recognizer = sr.Recognizer()
            
            # Transcribe the audio
            transcript = ""
            with sr.AudioFile(temp_path) as source:
                audio_data = recognizer.record(source)
                transcript = recognizer.recognize_google(audio_data)
            
            # Generate summary with Cohere
            summary = ""
            try:
                summary_response = co.generate(
                    prompt=f"Summarize this transcript concisely: {transcript}",
                    max_tokens=150,
                    temperature=0.7
                )
                summary = summary_response.generations[0].text.strip()
            except Exception as e:
                # If summary fails, continue with just the transcript
                print(f"Error generating summary: {str(e)}")
                summary = "Summary generation failed: " + str(e)
                # pass
            
            # Generate insights with Vertex AI Gemini
            insights_list = []
            try:
                model = GenerativeModel("gemini-pro")
                insight_response = model.generate_content(
                    f"Analyze this meeting transcript and summary. Provide key insights, action items, and important decisions made:\n\nTranscript: {transcript}\n\nSummary: {summary}"
                )
                insights = insight_response.text.strip()
                
                # Format insights as a list by splitting on newlines or bullet points
                if insights:
                    # Try to split by common delimiters in the insights
                    lines = insights.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line:
                            # Remove bullet points or numbering
                            line = line.lstrip('•-*').strip()
                            line = line.lstrip('1234567890.)').strip()
                            insights_list.append(line)
            except Exception as e:
                # If insights fail, continue with transcript and summary
               print(f"Error generating insights: {str(e)}")
               insights_list = ["Insights generation failed: " + str(e)]
            
            # Clean up the temporary file
            os.unlink(temp_path)
            
            return True, transcript, summary, insights_list, None
            
        except sr.UnknownValueError:
            return False, None, None, None, "Could not understand audio. Please ensure clear speech and minimal background noise."
        except sr.RequestError as e:
            return False, None, None, None, f"Error with speech recognition service: {str(e)}"
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, None, None, None, f"Error processing audio: {str(e)}"
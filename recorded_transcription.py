# from google.cloud import speech_v1p1beta1 as speech
# import soundfile as sf
# import cohere
# import os
# from dotenv import load_dotenv

# # Load environment variables from .env file
# load_dotenv()

# # Initialize the speech client
# client = speech.SpeechClient()

# # Load an audio file and get its properties
# audio_file = "new_recording.wav"
# with sf.SoundFile(audio_file) as f:
#     sample_rate = f.samplerate
#     channels = f.channels
#     print(f"Detected sample rate: {sample_rate} Hz, Channels: {channels}")

# with open(audio_file, "rb") as audio:
#     content = audio.read()

# # Configure the audio settings dynamically
# audio = speech.RecognitionAudio(content=content)
# config = speech.RecognitionConfig(
#     encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
#     sample_rate_hertz=sample_rate,
#     language_code="en-US",
#     audio_channel_count=channels,
# )

# # Send the audio to Google and get the transcription
# response = client.recognize(config=config, audio=audio)

# # Save the full transcript in a variable
# full_transcript = ""
# for result in response.results:
#     alternative = result.alternatives[0]
#     speaker_tag = alternative.words[0].speaker_tag if alternative.words else "Unknown"
#     print(f"Speaker {speaker_tag}: {alternative.transcript}")
#     full_transcript += alternative.transcript + " "
# full_transcript = full_transcript.strip()

# print("\nFull Transcript:")
# print(full_transcript)

# # Initialize Cohere client and generate summary
# COHERE_API_KEY = os.getenv("COHERE_API_KEY")
# if not COHERE_API_KEY:
#     raise ValueError("COHERE_API_KEY not found in .env file")
# co = cohere.Client(COHERE_API_KEY)
# response1 = co.generate(
#     prompt=f"Summarize this: {full_transcript}",
#     max_tokens=50,
#     temperature=0.7
# )
# summary = response1.generations[0].text.strip()

# # Print the summary
# print("\nSummary:")
# print(summary)


from google.cloud import speech_v1p1beta1 as speech
import soundfile as sf
import cohere
import os
from dotenv import load_dotenv
from google.cloud import aiplatform

# Load environment variables
load_dotenv()

# Initialize Speech-to-Text client
speech_client = speech.SpeechClient()

# Load audio file and get properties
audio_file = "new_recording.wav"
with sf.SoundFile(audio_file) as f:
    sample_rate = f.samplerate
    channels = f.channels
    print(f"Detected sample rate: {sample_rate} Hz, Channels: {channels}")

with open(audio_file, "rb") as audio:
    content = audio.read()

# Configure audio settings
audio = speech.RecognitionAudio(content=content)
config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=sample_rate,
    language_code="en-US",
    audio_channel_count=channels,
)

# Get transcription
response = speech_client.recognize(config=config, audio=audio)

# Save full transcript
full_transcript = ""
for result in response.results:
    alternative = result.alternatives[0]
    speaker_tag = alternative.words[0].speaker_tag if alternative.words else "Unknown"
    # print(f"Speaker {speaker_tag}: {alternative.transcript}")
    full_transcript += alternative.transcript + " "
full_transcript = full_transcript.strip()

print("\nFull Transcript:")
print(full_transcript)

# Cohere summary
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
if not COHERE_API_KEY:
    raise ValueError("COHERE_API_KEY not found in .env file")
co = cohere.Client(COHERE_API_KEY)
response1 = co.generate(
    prompt=f"Summarize this: {full_transcript}",
    max_tokens=50,
    temperature=0.7
)
summary = response1.generations[0].text.strip()
print("\nSummary:")
print(summary)

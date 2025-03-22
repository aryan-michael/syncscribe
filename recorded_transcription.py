from google.cloud import speech

# Initialize the client
client = speech.SpeechClient()

# Load an audio file
audio_file = "harvard.wav"  # Updated to your file
with open(audio_file, "rb") as audio:
    content = audio.read()

# Configure the audio settings
audio = speech.RecognitionAudio(content=content)
config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=44100,  # Matches your file’s 44.1 kHz
    language_code="en-US",
    audio_channel_count=2,    # Specify stereo (2 channels)
)

# Send the audio to Google and get the transcription
response = client.recognize(config=config, audio=audio)

# Print the results
for result in response.results:
    print("Transcription:", result.alternatives[0].transcript)
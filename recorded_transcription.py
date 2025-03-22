from google.cloud import speech_v1p1beta1 as speech  # Use v1p1beta1 for diarization support
import soundfile as sf

# Initialize the client
client = speech.SpeechClient()

# Load an audio file and get its properties
audio_file = "new_recording.wav"
with sf.SoundFile(audio_file) as f:
    sample_rate = f.samplerate  # Get the sample rate (e.g., 48000)
    channels = f.channels       # Get the number of channels (e.g., 2 for stereo)
    print(f"Detected sample rate: {sample_rate} Hz, Channels: {channels}")

with open(audio_file, "rb") as audio:
    content = audio.read()

# Configure the audio settings dynamically
audio = speech.RecognitionAudio(content=content)
config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=sample_rate,    # Use detected sample rate
    language_code="en-US",
    audio_channel_count=channels,     # Use detected channel count
    enable_speaker_diarization=True,  # Enable diarization (uncommented)
    diarization_speaker_count=2,      # Expect 2 speakers
)

# Send the audio to Google and get the transcription
response = client.recognize(config=config, audio=audio)

# Print the results with speaker tags
for result in response.results:
    alternative = result.alternatives[0]
    speaker_tag = alternative.words[0].speaker_tag if alternative.words else "Unknown"
    print(f"Speaker {speaker_tag}: {alternative.transcript}")


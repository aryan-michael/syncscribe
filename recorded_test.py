from google.cloud import speech_v1p1beta1 as speech
import soundfile as sf

# Initialize the client
client = speech.SpeechClient()

# Load an audio file and get its properties
audio_file = "new_recording.wav"
with sf.SoundFile(audio_file) as f:
    sample_rate = f.samplerate
    channels = f.channels
    print(f"Detected sample rate: {sample_rate} Hz, Channels: {channels}")

with open(audio_file, "rb") as audio:
    content = audio.read()

# Configure the audio settings (no diarization)
audio = speech.RecognitionAudio(content=content)
config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=sample_rate,
    language_code="en-US",
    audio_channel_count=channels,
)

# Send the audio to Google and get the transcription
response = client.recognize(config=config, audio=audio)

# Segment speakers based on time gaps
speaker_transcripts = {}  # Dictionary to store transcripts by speaker ID
current_speaker = 1       # Start with Speaker 1
last_end_time = 0         # Track the end of the last segment
silence_threshold = 2.0   # 2-second gap to switch speakers

for result in response.results:
    alternative = result.alternatives[0]
    transcript = alternative.transcript
    
    # Get timing from the first and last word
    if alternative.words:
        start_time = alternative.words[0].start_time.total_seconds()
        end_time = alternative.words[-1].end_time.total_seconds()
        
        # Switch to a new speaker if there's a significant gap
        if start_time - last_end_time > silence_threshold:
            current_speaker += 1  # Increment to next speaker
        
        last_end_time = end_time
    else:
        # Handle rare cases with no word timing
        end_time = last_end_time
    
    # Store the transcript for the current speaker
    if current_speaker not in speaker_transcripts:
        speaker_transcripts[current_speaker] = []
    speaker_transcripts[current_speaker].append(transcript)
    print(f"Speaker {current_speaker}: {transcript}")

# Print final speaker transcripts
print("\nFinal Speaker Breakdown:")
for speaker, lines in speaker_transcripts.items():
    full_text = " ".join(lines)
    print(f"Speaker {speaker}: {full_text}")
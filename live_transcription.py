import pyaudio
from google.cloud import speech
import queue
import sys
from google.cloud import speech_v1p1beta1 as speech

# Audio recording settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1  # Mono
RATE = 16000  # Matches Google's preferred rate

# Set up audio stream
p = pyaudio.PyAudio()
stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
audio_queue = queue.Queue()

# Initialize Google Speech client
client = speech.SpeechClient()

# Configuration for streaming with speaker diarization
config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=RATE,
    language_code="en-US",
    enable_speaker_diarization=True,  # Enable diarization
    diarization_speaker_count=2,     # Expect 2 speakers
)
streaming_config = speech.StreamingRecognitionConfig(config=config, interim_results=True)

# Generator to stream audio chunks
def audio_generator():
    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        audio_queue.put(data)
        yield data

# Handle streaming responses with speaker tags
def process_responses(responses):
    for response in responses:
        if not response.results:
            continue
        result = response.results[0]
        if not result.alternatives:
            continue
        alternative = result.alternatives[0]
        transcript = alternative.transcript
        speaker_tag = alternative.words[0].speaker_tag if alternative.words else None  # Get speaker tag from first word
        
        if result.is_final:
            speaker_label = f"Speaker {speaker_tag}" if speaker_tag is not None else "Unknown"
            print(f"Final Transcript ({speaker_label}): {transcript}")
            # Add Cohere summarization here later
        else:
            speaker_label = f"Speaker {speaker_tag}" if speaker_tag is not None else "Unknown"
            sys.stdout.write(f"Live Transcript ({speaker_label}): {transcript}\r")
            sys.stdout.flush()

# Main function to run the streaming
def main():
    print("Listening... Press Ctrl+C to stop.")
    try:
        requests = (speech.StreamingRecognizeRequest(audio_content=content) for content in audio_generator())
        responses = client.streaming_recognize(streaming_config, requests)
        process_responses(responses)
    except KeyboardInterrupt:
        print("\nStopping...")
        stream.stop_stream()
        stream.close()
        p.terminate()
        print("Stopped cleanly.")
    except Exception as e:
        print(f"An error occurred: {e}")
        stream.stop_stream()
        stream.close()
        p.terminate()

if __name__ == "__main__":
    main()
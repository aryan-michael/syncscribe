import pyaudio
from google.cloud import speech
import queue
import sys

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

# Configuration for streaming
config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=RATE,
    language_code="en-US",
)
streaming_config = speech.StreamingRecognitionConfig(config=config, interim_results=True)

# Generator to stream audio chunks
def audio_generator():
    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        audio_queue.put(data)
        yield data

# Handle streaming responses
def process_responses(responses):
    for response in responses:
        if not response.results:
            continue
        result = response.results[0]
        if not result.alternatives:
            continue
        transcript = result.alternatives[0].transcript
        if result.is_final:
            print("Final Transcript:", transcript)
            # Add Cohere summarization here later
        else:
            sys.stdout.write(f"Live Transcript: {transcript}\r")
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
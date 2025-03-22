import pyaudio
from google.cloud import speech_v1p1beta1 as speech
import queue
import sys
import cohere
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Audio recording settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1  # Mono
RATE = 16000  # Matches Google's preferred rate

# Set up audio stream
p = pyaudio.PyAudio()
stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
audio_queue = queue.Queue()

# Initialize clients
speech_client = speech.SpeechClient()
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
if not COHERE_API_KEY:
    raise ValueError("COHERE_API_KEY not found in .env file")
cohere_client = cohere.Client(COHERE_API_KEY)

# Configuration for streaming with speaker diarization
config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=RATE,
    language_code="en-US",
    enable_speaker_diarization=True,
    diarization_speaker_count=2,
)
streaming_config = speech.StreamingRecognitionConfig(config=config, interim_results=True)

# Generator to stream audio chunks
def audio_generator():
    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        audio_queue.put(data)
        yield data

# Handle streaming responses with speaker tags and summarization
full_transcript = ""  # Store the full transcript
summary_counter = 0  # Track final results for periodic summaries

def process_responses(responses):
    global full_transcript, summary_counter
    for response in responses:
        if not response.results:
            continue
        result = response.results[0]
        if not result.alternatives:
            continue
        alternative = result.alternatives[0]
        transcript = alternative.transcript
        speaker_tag = alternative.words[0].speaker_tag if alternative.words else None
        
        if result.is_final:
            speaker_label = f"Speaker {speaker_tag}" if speaker_tag is not None else "Unknown"
            print(f"Final Transcript ({speaker_label}): {transcript}")
            full_transcript += f"{speaker_label}: {transcript} "  # Append to full transcript
            summary_counter += 1
            
            # Summarize every 3 final results (adjust as needed)
            if summary_counter >= 3:
                summary = cohere_client.generate(
                    prompt=f"Summarize this meeting transcript: {full_transcript}",
                    max_tokens=50,
                    temperature=0.7
                ).generations[0].text.strip()
                print("\nLive Summary:")
                print(summary)
                summary_counter = 0  # Reset counter
        else:
            speaker_label = f"Speaker {speaker_tag}" if speaker_tag is not None else "Unknown"
            sys.stdout.write(f"Live Transcript ({speaker_label}): {transcript}\r")
            sys.stdout.flush()

# Main function to run the streaming
def main():
    print("Listening... Press Ctrl+C to stop.")
    try:
        requests = (speech.StreamingRecognizeRequest(audio_content=content) for content in audio_generator())
        responses = speech_client.streaming_recognize(streaming_config, requests)
        process_responses(responses)
    except KeyboardInterrupt:
        print("\nStopping...")
        # Final summary on exit
        if full_transcript:
            final_summary = cohere_client.generate(
                prompt=f"Summarize this meeting transcript: {full_transcript}",
                max_tokens=50,
                temperature=0.7
            ).generations[0].text.strip()
            print("\nFinal Summary:")
            print(final_summary)
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
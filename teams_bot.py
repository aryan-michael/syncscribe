from botbuilder.core import BotFrameworkAdapterSettings, BotFrameworkAdapter, TurnContext  # Added TurnContext
from botbuilder.schema import Activity
from aiohttp import web
import asyncio
from google.cloud import speech_v1p1beta1 as speech
import cohere
from dotenv import load_dotenv
import os
import queue
import threading

# Load environment variables
load_dotenv()

# Teams Bot settings
APP_ID = "123e4567-e89b-12d3-a456-426614174000"  # Replace with your Client ID
APP_PASSWORD = "abc123~xyz789"  # Replace with your Client Secret
SETTINGS = BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)
ADAPTER = BotFrameworkAdapter(SETTINGS)

# Audio queue
audio_queue = queue.Queue()

# Clients
speech_client = speech.SpeechClient()
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
if not COHERE_API_KEY:
    raise ValueError("COHERE_API_KEY not found in .env file")
cohere_client = cohere.Client(COHERE_API_KEY)

# Streaming config
RATE = 16000
config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=RATE,
    language_code="en-US",
    enable_speaker_diarization=True,
    diarization_speaker_count=2,
)
streaming_config = speech.StreamingRecognitionConfig(config=config, interim_results=True)

# Bot class
class TeamsAudioBot:
    async def on_turn(self, turn_context: TurnContext):
        if turn_context.activity.type == "event" and turn_context.activity.name == "application/vnd.microsoft.meetingStart":
            await turn_context.send_activity("Bot joined the meeting!")
            threading.Thread(target=self.process_audio, daemon=True).start()
        elif turn_context.activity.type == "message":
            text = turn_context.activity.text
            audio_queue.put(text.encode())  # Simulate audio with chat for now
            await turn_context.send_activity(f"Echo: {text}")

    def process_audio(self):
        requests = (speech.StreamingRecognizeRequest(audio_content=content) for content in self.audio_generator())
        responses = speech_client.streaming_recognize(streaming_config, requests)
        self.process_responses(responses)

    def audio_generator(self):
        while True:
            data = audio_queue.get()
            if data is None:
                break
            yield data

    def process_responses(self, responses):
        global full_transcript, summary_counter
        full_transcript = ""
        summary_counter = 0
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
                full_transcript += f"{speaker_label}: {transcript} "
                summary_counter += 1
                
                if summary_counter >= 3:
                    summary = cohere_client.generate(
                        prompt=f"Summarize this meeting transcript: {full_transcript}",
                        max_tokens=50,
                        temperature=0.7
                    ).generations[0].text.strip()
                    print("\nLive Summary:")
                    print(summary)
                    summary_counter = 0
            else:
                speaker_label = f"Speaker {speaker_tag}" if speaker_tag is not None else "Unknown"
                print(f"Live Transcript ({speaker_label}): {transcript}\r", end="")

# HTTP server
async def messages(req):
    body = await req.json()
    activity = Activity().deserialize(body)
    auth_header = req.headers.get("Authorization", "")
    await ADAPTER.process_activity(activity, auth_header, bot.on_turn)
    return web.Response(status=200)

app = web.Application()
app.router.add_post("/api/messages", messages)
bot = TeamsAudioBot()

async def run_server():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "localhost", 3978)
    await site.start()
    print("Bot running on http://localhost:3978/api/messages - Use Localtunnel: lt --port 3978 --subdomain mihir-meeting-bot")

if __name__ == "__main__":
    asyncio.run(run_server())
from gtts import gTTS
from pydub import AudioSegment
import os

# Define dialogue with characters
dialogue = [
    ("Alex", "Hey Jordan, did you hear about the latest AI advancements? It’s insane how fast things are moving."),
    ("Jordan", "Yeah, I did. But honestly, it kind of worries me. AI is automating everything. What happens to people’s jobs?"),
    ("Alex", "That’s a valid concern, but AI also creates new opportunities. Look at software development. AI tools like Copilot help programmers, but they don’t replace them."),
    ("Jordan", "True, but what about industries like customer service? AI chatbots are everywhere now."),
    ("Alex", "Sure, but have you ever had a great experience with a chatbot? Most of the time, you still need a human to step in. AI assists; it doesn’t replace."),
    ("Jordan", "Maybe for now, but as AI gets better, won’t companies prefer machines over humans?"),
    ("Alex", "Not necessarily. AI lacks creativity, empathy, and critical thinking—things humans excel at. Even with automation, we’ll need people to manage, train, and improve AI systems."),
    ("Jordan", "I get that, but what if AI reaches a point where it doesn’t need human supervision?"),
    ("Alex", "Even then, new roles will emerge. Think about the industrial revolution—machines replaced some jobs but created entirely new ones. The key is adapting."),
    ("Jordan", "So you think AI will create more jobs than it destroys?"),
    ("Alex", "Not necessarily more, but different jobs. AI is a tool, not a replacement for human ingenuity."),
    ("Jordan", "I hope you’re right. Guess I should start learning more about AI instead of fearing it."),
    ("Alex", "Exactly! Understanding AI is the best way to stay ahead."),
]

# Generate audio files with different voices
alex_audio = []
jordan_audio = []

for speaker, text in dialogue:
    tts = gTTS(text=text, lang="en", slow=False)
    filename = f"{speaker}.mp3"
    tts.save(filename)

    # Load and adjust the pitch/speed for variation
    audio = AudioSegment.from_mp3(filename)

    if speaker == "Alex":
        audio = audio.speedup(playback_speed=1.1)  # Slightly faster for Alex
    else:
        audio = audio - 5  # Lower volume for Jordan

    if speaker == "Alex":
        alex_audio.append(audio)
    else:
        jordan_audio.append(audio)

    os.remove(filename)  # Cleanup temporary file

# Combine the conversation
full_conversation = AudioSegment.silent(duration=500)  # Start with a short silence
for idx, (speaker, _) in enumerate(dialogue):
    if speaker == "Alex":
        full_conversation += alex_audio.pop(0)
    else:
        full_conversation += jordan_audio.pop(0)

# Export final WAV file
output_wav = "conversation.wav"
full_conversation.export(output_wav, format="wav")

print(f"Conversation saved as {output_wav}")

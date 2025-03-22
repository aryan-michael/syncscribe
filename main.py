import speech_recognition as sr

recognizer = sr.Recognizer()
with sr.AudioFile("harvard.wav") as source:
    audio = recognizer.record(source)
    text = recognizer.recognize_google(audio)  # Free Google API for testing
    print("Transcription:", text)

with sr.Microphone() as source:
    print("Listening...")
    audio = recognizer.listen(source, timeout=10)
    text = recognizer.recognize_google(audio)
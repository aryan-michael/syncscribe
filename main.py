import speech_recognition as sr

recognizer = sr.Recognizer()
with sr.AudioFile("meeting_audio.wav") as source:
    audio = recognizer.record(source)
    text = recognizer.recognize_google(audio)  # Free Google API for testing
    print("Transcription:", text)
from http.client import HTTPException

from app.ai_services import stt_client
import google.cloud.speech as speech

speech.

def speech_to_text(audio_content):
    audio = speech.RecognitionAudio(content=audio_content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
    )
    response = stt_client.recognize(config=config, audio=audio)

    # Check if the response contains results and alternatives
    if not response.results or not response.results[0].alternatives:
        raise HTTPException()
    return response.results[0].alternatives[0].transcript

with open("temp.mp3", "rb") as audio_file:
    content = audio_file.read()
    print(type(content))
    text = speech_to_text(content)

    print(text)

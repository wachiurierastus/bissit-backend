from http.client import HTTPException

import openai
from google.cloud import texttospeech, speech
from google.oauth2 import service_account
from config.config import config

openai.api_key = config.OPENAI_API_KEY

credentials = service_account.Credentials.from_service_account_file(config.GOOGLE_APPLICATION_CREDENTIALS)
tts_client = texttospeech.TextToSpeechClient(credentials=credentials)
stt_client = speech.SpeechClient(credentials=credentials)


def process_with_ai(prompt, model="gpt-3.5-turbo"):
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def text_to_speech(text: str) -> bytes:
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = tts_client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    return response.audio_content


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
        raise HTTPException(status_code=400, detail="No speech detected in audio file.")

    return response.results[0].alternatives[0].transcript
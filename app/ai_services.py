import os
from google.cloud import vision
import openai
from google.cloud import texttospeech, speech
from google.oauth2 import service_account
from config.config import config
from openai import OpenAI
import logging
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech
import requests

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
LANGUAGE_CODE = "en-US"
DEFAULT_MODEL = "latest_long"

openai.api_key = config.OPENAI_API_KEY

credentials = service_account.Credentials.from_service_account_file(config.GOOGLE_APPLICATION_CREDENTIALS)
tts_client = texttospeech.TextToSpeechClient(credentials=credentials)
stt_client = speech.SpeechClient(credentials=credentials)


def process_with_ai(prompt, model="gpt-3.5-turbo"):
    try:
        # Initialize the OpenAI client with the API key
        client = OpenAI(
            # This is the default and can be omitted
            api_key=config.OPENAI_API_KEY,
        )

        # Create a chat completion
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "user", "content": prompt}
            ],
            model=model,
        )

        # Return the content of the response
        return chat_completion.choices[0].message.content

    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def detect_text_in_images(path):
    """Detects text in the file."""

    client = vision.ImageAnnotatorClient()

    with open(path, "rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations

    text = []
    for item in texts:
        text.append(item.description)

    if response.error.message:
        raise Exception(
            "{}\nFor more info on error messages, check: "
            "https://cloud.google.com/apis/design/errors".format(response.error.message)
        )

    return text

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


def read_audio_file(audio_file: str) -> bytes:
    """Read the audio file and return its content as bytes."""
    try:
        with open(audio_file, "rb") as f:
            content = f.read()
        logger.info("Successfully read audio file.")
        return content
    except FileNotFoundError:
        logger.error(f"Audio file {audio_file} not found.")
        raise
    except IOError as e:
        logger.error(f"Error reading audio file {audio_file}: {e}")
        raise


def create_recognition_config(model: str) -> cloud_speech.RecognitionConfig:
    """Create and return the recognition configuration."""
    config = cloud_speech.RecognitionConfig(
        auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
        language_codes=[LANGUAGE_CODE],
        model=model,
    )
    logger.info("Recognition config created successfully.")
    return config


def transcribe_audio(
        project_id: str,
        model: str,
        audio_file: str
) -> cloud_speech.RecognizeResponse:
    """Transcribe an audio file using the specified model."""
    # Instantiates a client
    client = SpeechClient()

    # Read audio file content
    audio_content = read_audio_file(audio_file)

    # Create recognition config
    config = create_recognition_config(model)

    # Build the request
    request = cloud_speech.RecognizeRequest(
        recognizer=f"projects/{project_id}/locations/global/recognizers/_",
        config=config,
        content=audio_content,
    )

    try:
        # Transcribe the audio into text
        response = client.recognize(request=request)
        logger.info("Transcription completed successfully.")

        # Process the response
        for result in response.results:
            logger.info(f"Transcript: {result.alternatives[0].transcript}")

        return response
    except Exception as e:
        logger.error(f"Error during transcription: {e}")
        raise


# Example usage
if __name__ == "__main__":
    project_id = "your-project-id"
    model = DEFAULT_MODEL
    audio_file = "path/to/your/audio/file.wav"

    try:
        response = transcribe_audio(project_id, model, audio_file)
    except Exception as e:
        logger.error(f"Transcription failed: {e}")

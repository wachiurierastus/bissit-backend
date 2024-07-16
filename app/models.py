from pydantic import BaseModel

class TextInput(BaseModel):
    text: str

class AudioInput(BaseModel):
    audio_url: str
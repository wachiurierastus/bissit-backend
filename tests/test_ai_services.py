from app.ai_services import process_with_ai, text_to_speech, speech_to_text

def test_process_with_ai():
    response = process_with_ai("What is 2+2?")
    assert response is not None
    assert "4" in response.lower()

def test_text_to_speech():
    audio_content = text_to_speech("Hello, world!")
    assert audio_content is not None
    assert len(audio_content) > 0

def test_speech_to_text():
    # This test requires a sample audio file
    with open('sample_audio.wav', 'rb') as audio_file:
        audio_content = audio_file.read()

    text = speech_to_text(audio_content)
    assert text is not None
    assert len(text) > 0
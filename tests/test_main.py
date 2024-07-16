from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_upload_document():
    with open('test_document.txt', 'w') as f:
        f.write('This is a test document.')

    with open('test_document.txt', 'rb') as f:
        response = client.post("/doc", files={"file": ("test_document.txt", f, "text/plain")})

    assert response.status_code == 200
    assert "file_id" in response.json()
    assert "ai_analysis" in response.json()

def test_tts_endpoint():
    response = client.post("/sing", json={"text": "Hello, world!"})
    assert response.status_code == 200
    assert "audio_url" in response.json()

def test_stt_endpoint():
    # This test assumes you have a test audio file in S3
    response = client.post("/listen", json={"audio_url": "https://your-bucket.s3.amazonaws.com/test_audio.wav"})
    assert response.status_code == 200
    assert "text" in response.json()

def test_chat_endpoint():
    response = client.post("/chat", json={"text": "What is the capital of France?"})
    assert response.status_code == 200
    assert "response" in response.json()
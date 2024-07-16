import uuid

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from .models import TextInput, AudioInput
from .rag import RAG
from .database import Database
from .ai_services import process_with_ai, text_to_speech, speech_to_text
from .storage import upload_to_s3, download_from_s3
from config.config import config
import os

app = FastAPI()
db = Database()
rag = RAG()


@app.post("/doc")
async def upload_document(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        file_id = db.save_document(file.filename, contents)

        document_text = contents.decode('utf-8')
        ai_response = process_with_ai(f"Analyze this document: {document_text}")

        rag.add_document(document_text)

        return JSONResponse(content={
            "message": "Document uploaded and processed successfully",
            "file_id": str(file_id),
            "ai_analysis": ai_response
        }, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#TODO Update this to read from env and S3
@app.post("/sing")
async def tts_endpoint(text_input: TextInput):
    try:
        audio_content = text_to_speech(text_input.text)
        filename = f"{uuid.uuid4()}.mp3"
        with open(filename, "wb") as out:
            out.write(audio_content)

        s3_url = upload_to_s3(filename, 'your-s3-bucket-name')

        os.remove(filename)

        return JSONResponse(content={
            "message": "Audio generated successfully",
            "audio_url": s3_url
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/listen")
async def stt_endpoint(audio_input: AudioInput):
    try:
        local_filename = 'temp_audio.wav'
        download_from_s3(audio_input.audio_url, local_filename)

        with open(local_filename, "rb") as audio_file:
            content = audio_file.read()

        text = speech_to_text(content)

        os.remove(local_filename)

        return JSONResponse(content={"text": text})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
async def chat(text_input: TextInput):
    rag_response = rag.ask(text_input.text)
    ai_response = process_with_ai(f"Given this context: {rag_response}, respond to: {text_input.text}")
    return JSONResponse(content={"response": ai_response})

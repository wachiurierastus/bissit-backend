import uuid

import aiohttp
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from .models import TextInput, AudioInput
from .rag import RAG
from .database import Database
from .ai_services import process_with_ai, text_to_speech, speech_to_text
from .storage import upload_to_s3, download_from_s3
from config.config import config
import os
import chardet

app = FastAPI()
db = Database()
rag = RAG()


@app.get("/")
async def root():
    return {"Hello": "World"}

#Check this code out first before running the tests
@app.post("/img")
async def upload_image(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        file_id = db.save_document(file.filename, contents)

        return JSONResponse(content={
            "message": "Image uploaded successfully",
            "file_id": str(file_id)
        }, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/doc")
async def upload_document(file: UploadFile = File(...)):
    try:
        contents = await file.read()

        # Detect the encoding of the file
        detected_encoding = chardet.detect(contents)['encoding']
        if not detected_encoding:
            raise ValueError("Could not detect file encoding.")

        # Convert to UTF-8 if necessary
        if detected_encoding.lower() != 'utf-8':
            contents = contents.decode(detected_encoding).encode('utf-8')

        # Save the document in the database
        file_id = db.save_document(file.filename, contents)

        # Decode contents to UTF-8 string for further processing
        document_text = contents.decode('utf-8')
        ai_response = process_with_ai(f"Analyze this document: {document_text}")

        rag.add_document(document_text)

        return JSONResponse(content={
            "message": "Document uploaded and processed successfully",
            "file_id": str(file_id),
            "ai_analysis": ai_response
        }, status_code=200)

    except UnicodeDecodeError as e:
        raise HTTPException(status_code=400, detail=f"File encoding error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# TODO Update this to read from env and S3
@app.post("/sing")
async def tts_endpoint(text_input: TextInput):
    print(text_input)
    try:
        audio_content = text_to_speech(text_input.text)
        filename = f"{uuid.uuid4()}.mp3"
        with open(filename, "wb") as out:
            out.write(audio_content)

        s3_url = upload_to_s3(filename, filename)

        os.remove(filename)

        return JSONResponse(content={
            "message": "Audio generated successfully",
            "audio_url": s3_url
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/listen")
async def stt_endpoint(audio_input: AudioInput):
    local_filename = 'temp_audio.mp3'
    try:
        await download_from_s3(audio_input.audio_url, local_filename)

        if not os.path.exists(local_filename):
            raise HTTPException(status_code=400, detail="Audio file not found after download.")

        with open(local_filename, "rb") as audio_file:
            content = audio_file.read()

        if not content:
            raise HTTPException(status_code=400, detail="Downloaded audio file is empty.")

        text = speech_to_text(content)

        return JSONResponse(content={"text": text})
    except aiohttp.ClientError as e:
        raise HTTPException(status_code=400, detail=f"Error downloading audio file: {e}")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
    finally:
        if os.path.exists(local_filename):
            os.remove(local_filename)

@app.post("/chat")
async def chat(text_input: TextInput):
    rag_response = rag.ask(text_input.text)
    ai_response = process_with_ai(f"Given this context: {rag_response}, respond to: {text_input.text}")
    return JSONResponse(content={"response": ai_response})

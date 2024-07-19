import uuid
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from .models import TextInput, AudioInput
from .rag import RAG
from .database import Database
from .ai_services import text_to_speech, detect_text_in_images, process_with_ai
from .storage import upload_to_s3, download_from_s3
from config.config import config
import os
import logging
import aiofiles
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
rag = RAG()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
def extract_text_block(text_list):
    # Initialize a list to hold blocks of text (lines with more than one word)
    text_blocks = []

    # Iterate over the lines in the text_list
    for line in text_list:
        # Replace newline characters with spaces in each line
        cleaned_line = line.replace('\n', ' ')

        # Split the line into words
        words = cleaned_line.split()

        # Only keep lines with more than one word
        if len(words) > 1:
            # Join the words back into a single string and add it to the text_blocks
            text_blocks.append(' '.join(words))

    # Return the combined block of text as a single string
    return ' '.join(text_blocks)

@app.get("/")
async def root():
    return {"Hello": "World"}


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),  # Log to a file
        logging.StreamHandler()  # Also log to console
    ]
)
import re


@app.post("/upload-and-ocr")
async def upload_and_ocr(file: UploadFile = File(...)):
    """
    Endpoint to upload a file and perform OCR on it immediately.

    Args:
        file (UploadFile): The file to be uploaded and processed.

    Returns:
        JSONResponse: The OCR results from the uploaded file.
    """
    try:
        if file is None or file.filename == "":
            logging.error("No file uploaded")
            raise HTTPException(500)

        # Create the upload directory if it doesn't exist
        os.makedirs(config.UPLOAD_DIR, exist_ok=True)

        # Define the path to save the file
        file_path = os.path.join(config.UPLOAD_DIR, file.filename)

        # Read and save the uploaded file
        async with aiofiles.open(file_path, 'wb') as out_file:
            contents = await file.read()
            if contents is None:
                logging.error(f"Failed to read the file '{file.filename}'")
                raise HTTPException(500)
            await out_file.write(contents)

        logging.info(f"File '{file.filename}' uploaded successfully and saved to '{file_path}'")

        # Perform OCR using the process_with_ai function
        ocr_response = detect_text_in_images(file_path)
        return JSONResponse(content={
            "message": "OCR processing completed successfully",
            "ocr_text": extract_text_block(ocr_response)
        }, status_code=200)

    except Exception as e:
        logging.error(f"An error occurred for file '{file.filename}': {str(e)}")
        raise HTTPException(500)





@app.post("/doc")
async def upload_document(file: UploadFile = File(...)):
    try:
        if file is None or file.filename == "":
            logging.error("No file uploaded")
            raise HTTPException(status_code=400, detail="No file uploaded")

        # Create the upload directory if it doesn't exist
        os.makedirs(config.UPLOAD_DIR, exist_ok=True)

        # Define the path to save the file
        file_path = os.path.join(config.UPLOAD_DIR, file.filename)

        # Read the uploaded file contents
        contents = await file.read()
        if contents is None:
            logging.error(f"Failed to read the file '{file.filename}'")
            raise HTTPException(status_code=400, detail="Failed to read the uploaded file")

        # Save the uploaded file
        async with aiofiles.open(file_path, 'wb') as out_file:
            await out_file.write(contents)

        logging.info(f"File '{file.filename}' uploaded successfully and saved to '{file_path}'")

        return JSONResponse(content={
            "message": "Document uploaded successfully",
            "file_path": file_path
        }, status_code=200)

    except Exception as e:
        logging.error(f"An error occurred for file '{file.filename}': {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


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
    try:
        local_filename = 'temp_audio.mp3'
        download_from_s3(audio_input.audio_url, local_filename)

        with open(local_filename, "rb") as audio_file:
            content = audio_file.read()

        #text = speech_to_text(content)

        os.remove(local_filename)

        #return JSONResponse(content={"text": text})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
async def chat(text_input: TextInput):
    rag_response = rag.ask(text_input.text)
    ai_response = process_with_ai(f"Given this context: {rag_response}, respond to: {text_input.text}")
    return JSONResponse(content={"response": ai_response})


@app.post("/summary")
async def summary(text_input: TextInput):
    try:
        rag_response = rag.summary(text_input.text)
        ai_response = process_with_ai(f"Given this context: {rag_response}, respond to: {text_input.text}")
        return JSONResponse(content={"response": ai_response})
    except Exception as e:
        raise HTTPException(500)

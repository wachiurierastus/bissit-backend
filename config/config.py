import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    MONGODB_URI = os.getenv('MONGODB_URI')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_DEFAULT_REGION = os.getenv('AWS_DEFAULT_REGION')
    S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
    DOCS_DIR = os.getenv('DOCS_DIR')
    MILVUS_HOST = os.getenv('MILVUS_HOST')
    MILVUS_PORT = int(os.getenv('MILVUS_PORT'))
    UPLOAD_DIR = os.getenv('UPLOAD_DIR')
    RAPIDAPI_HOST = os.getenv('RAPIDAPI_HOST')
    RAPIDAPI_URL = os.getenv('RAPIDAPI_URL')
    RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY')



config = Config()

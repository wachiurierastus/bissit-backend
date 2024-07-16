from pymongo import MongoClient
from gridfs import GridFS
from config.config import config

class Database:
    def __init__(self):
        self.client = MongoClient(config.MONGODB_URI)
        self.db = self.client['document_db']
        self.fs = GridFS(self.db)

    def save_document(self, filename, content):
        return self.fs.put(content, filename=filename)

    def get_document(self, file_id):
        return self.fs.get(file_id)
import pytest
from app import Database, RAG
from config.config import config

@pytest.fixture
def test_database():
    return Database()

@pytest.fixture
def test_rag():
    return RAG(docs_dir=config.DOCS_DIR)

# You could also define shared test data or mock objects here
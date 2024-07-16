from app.database import Database

def test_database_connection():
    db = Database()
    assert db.client is not None
    assert db.db is not None
    assert db.fs is not None

def test_save_and_get_document():
    db = Database()
    content = b"Test document content"
    file_id = db.save_document("test.txt", content)
    assert file_id is not None

    retrieved_content = db.get_document(file_id).read()
    assert retrieved_content == content
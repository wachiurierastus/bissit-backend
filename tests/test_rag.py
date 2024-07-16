from app.rag import RAG

def test_rag_initialization():
    rag = RAG(docs_dir="test_docs")
    assert rag is not None

def test_rag_ask():
    rag = RAG(docs_dir="test_docs")
    response = rag.ask("What is the capital of France?")
    assert isinstance(response, str)
    assert len(response) > 0
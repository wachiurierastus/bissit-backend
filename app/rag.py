import requests
from io import BytesIO
from typing import List, Union
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.chains.query_constructor.base import AttributeInfo
from langchain.memory import ConversationTokenBufferMemory
from milvus import default_server as milvus_server

from .database import Database
from .ai_services import process_with_ai
from config.config import config
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredHTMLLoader, \
    UnstructuredWordDocumentLoader
from langchain_community.vectorstores import Milvus
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings


class RAG:
    def __init__(self, n_retrievals: int = 4, chat_max_tokens: int = 3097):
        self.db = Database()
        self.n_retrievals = n_retrievals
        self.chat_max_tokens = chat_max_tokens

        self.model = self.__set_llm_model()
        self.embeddings = OpenAIEmbeddings()
        self.vector_store = self.__set_vector_store()
        self.retriever = self.__set_retriever()
        self.chat_history = self.__set_chat_history()

    @staticmethod
    def __set_llm_model():
        return ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.7)

    def __set_vector_store(self):
        milvus_server.start()
        return Milvus(
            embedding_function=self.embeddings,
            connection_args={"host": config.MILVUS_HOST, "port": config.MILVUS_PORT},
            collection_name="personal_documents",
        )

    def __set_retriever(self):
        metadata_field_info = [
            AttributeInfo(
                name="source",
                description="The source or URL of the document",
                type="string",
            ),
            AttributeInfo(
                name="filetype",
                description="The file type of the document",
                type="string",
            ),
        ]

        document_content_description = "Personal and web documents"

        return SelfQueryRetriever.from_llm(
            self.model,
            self.vector_store,
            document_content_description,
            metadata_field_info,
            search_kwargs={"k": self.n_retrievals}
        )

    def __set_chat_history(self):
        return ConversationTokenBufferMemory(llm=self.model, max_token_limit=self.chat_max_tokens, return_messages=True)

    def add_document(self, document_url: str):
        # Download the document
        response = requests.get(document_url)
        if response.status_code != 200:
            raise Exception(f"Failed to download document from {document_url}")

        # Determine file type and load document
        content_type = response.headers.get('Content-Type', '')
        if 'pdf' in content_type:
            loader = PyPDFLoader(BytesIO(response.content))
            filetype = 'pdf'
        elif 'word' in content_type:
            loader = UnstructuredWordDocumentLoader(BytesIO(response.content))
            filetype = 'docx'
        elif 'html' in content_type:
            loader = UnstructuredHTMLLoader(BytesIO(response.content))
            filetype = 'html'
        else:
            loader = TextLoader(BytesIO(response.content))
            filetype = 'txt'

        documents = loader.load()

        # Split the documents
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(documents)

        # Add metadata
        for split in splits:
            split.metadata['source'] = document_url
            split.metadata['filetype'] = filetype

        # Add to vector store
        self.vector_store.add_documents(splits)

        # Save to database
        doc_id = self.db.save_document(document_url, response.content)

        return doc_id

    def ask(self, question: str) -> str:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an assistant responsible for answering questions about documents. "
                       "Answer the user's question with a reasonable level of detail based on the "
                       "following context document(s):\n\n{context}"),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
        ])

        output_parser = StrOutputParser()
        chain = prompt | self.model | output_parser

        context_docs = self.retriever.get_relevant_documents(question)
        context = "\n\n".join([doc.page_content for doc in context_docs])

        answer = chain.invoke({
            "input": question,
            "chat_history": self.chat_history.load_memory_variables({})['history'],
            "context": context
        })

        self.chat_history.save_context({"input": question}, {"output": answer})

        refined_answer = process_with_ai(
            f"Given this context and question: {context}\n\nQuestion: {question}\n\nInitial answer: {answer}\n\nPlease provide a more refined and detailed answer:")

        return refined_answer

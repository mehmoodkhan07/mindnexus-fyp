from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

def process_pdf(file_path, persist_dir):
    loader = PyPDFLoader(file_path)
    pages = loader.load()

    # Splitting logic
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150
    )
    chunks = splitter.split_documents(pages)

    # Embedding and Vector Storage
    Chroma.from_documents(
        documents=chunks,
        embedding=OllamaEmbeddings(model="nomic-embed-text"),
        persist_directory=persist_dir
    )
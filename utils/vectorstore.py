import os
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
## langchain loader - To load PDF,Word documents
from langchain_community.document_loaders import PyMuPDFLoader, Docx2txtLoader,DirectoryLoader,TextLoader
## Split long text into smaller chunks
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import settings

VECTORSTORE_PATH = settings.vector_path

def get_embeddings():
    return OllamaEmbeddings(model=settings.embedding_model)

def load_all_docs():
    docs = []

    loaders = [
        ("*.md",TextLoader),
        ("*.pdf",PyMuPDFLoader),
        ("*.docx",Docx2txtLoader)
    ]

    print("=" * 50)
    print("DOCS PATH:", os.path.abspath(settings.docs_path))
    print("=" * 50)

    for glob,loader_cls in loaders:
        loader = DirectoryLoader(settings.docs_path,glob=glob,loader_cls=loader_cls)

        loaded_docs = loader.load()
        print(f"\n{glob} -> {len(loaded_docs)} files")

        for doc in loaded_docs:
            print("   ", doc.metadata.get("source"))

        docs.extend(loaded_docs)

    print(f" Loaded {len(docs)} documents")
    return docs

def build_vectorstore():
    docs = load_all_docs()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size = settings.chunk_size,
        chunk_overlap = settings.chunk_overlap,
    )
    chunks = splitter.split_documents(docs)

    vs = FAISS.from_documents(chunks,get_embeddings())
    vs.save_local(settings.vector_path)
    print(f"Build FAISS with {len(chunks)} chunks")

def load_retriver():
    if not os.path.exists(settings.vector_path):
        build_vectorstore()
    vs = FAISS.load_local(
        settings.vector_path,
        get_embeddings(),
        allow_dangerous_deserialization=True,
    )

    return vs.as_retriever(search_type="mmr",
                           search_kwargs={"k":settings.retriver_k})

if __name__ == "__main__":
    build_vectorstore()
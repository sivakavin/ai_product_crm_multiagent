import os
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
## langchain loader - To load PDF,Word documents
from langchain_community.document_loaders import PyMuPDFLoader, Docx2txtLoader,DirectoryLoader,TextLoader
## Split long text into smaller chunks
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import settings
##Adding BM25 Retriver
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from utils.logger import get_logger

log = get_logger(__name__)

_chunks_cache = None
_retriever_cache = None

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

    log.info("Loading docs from %s", os.path.abspath(settings.docs_path))

    for glob,loader_cls in loaders:
        loader = DirectoryLoader(settings.docs_path,glob=glob,loader_cls=loader_cls)
        loaded_docs = loader.load()
        log.info("%s -> %d file(s)", glob, len(loaded_docs))
        for doc in loaded_docs:
            log.debug("   source: %s", doc.metadata.get("source"))
        docs.extend(loaded_docs)
    log.info("Loaded %d document(s)", len(docs))
    return docs

def get_chunks():
    global _chunks_cache
    if _chunks_cache is None:
        docs = load_all_docs()
        splitter = RecursiveCharacterTextSplitter(
            chunk_size = settings.chunk_size,
            chunk_overlap = settings.chunk_overlap,
        )
        _chunks_cache = splitter.split_documents(docs)
    return _chunks_cache

def build_vectorstore():
    # docs = load_all_docs()

    # splitter = RecursiveCharacterTextSplitter(
    #     chunk_size = settings.chunk_size,
    #     chunk_overlap = settings.chunk_overlap,
    # )
    chunks = get_chunks()
    vs = FAISS.from_documents(chunks,get_embeddings())
    vs.save_local(settings.vector_path)
    log.info("Built FAISS with %d chunks", len(chunks))

def load_retriver():
    global _retriever_cache

    if _retriever_cache is not None:
        return _retriever_cache
    
    chunks = get_chunks()

    # Sematic retriver (FAISS)
    if not os.path.exists(settings.vector_path):
        build_vectorstore()

    vs = FAISS.load_local(
        settings.vector_path,
        get_embeddings(),
        allow_dangerous_deserialization=True,
    )
    faiss_retriver = vs.as_retriever(search_type="mmr",search_kwargs={"k":settings.retriver_k})

    # Keyword retriver (BM25)
    bm25_retriver = BM25Retriever.from_documents(chunks)
    bm25_retriver.k = settings.retriver_k

    #Hybrid: 50% semantic + 50% keyword
    _retriever_cache = EnsembleRetriever(
        retrievers=[faiss_retriver,bm25_retriver],
        weights=[0.5,0.5]
    )
    return _retriever_cache

if __name__ == "__main__":
    build_vectorstore()
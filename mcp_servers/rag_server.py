import faiss  # eager main-thread load: faiss.dll must not be imported inside a
              # fastmcp worker thread on Windows (loader-lock deadlock)

from fastmcp import FastMCP
from utils.vectorstore import load_retriver
from utils.reranker import rerank

mcp = FastMCP("rag-server")

@mcp.tool()
def search_docs(question:str)->str:
    """ Search CRM policy,FAQ and support docs."""

    base_retriver = load_retriver()
    docs = base_retriver.invoke(question)
    docs = rerank(question,docs)
    return  "\n\n".join(doc.page_content for doc in docs)

if __name__ == "__main__":
    mcp.run(transport="stdio")
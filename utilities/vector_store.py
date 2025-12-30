from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings


def create_vector_store(chunks, persist_directory="db/chroma_db"):
    """Create and persist ChromaDB vector store"""
    print("-- CREATING EMBEDDINGS AND STORING IN CHROMADB... ---")

    embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")

    # Create ChromaDB vector store
    print("-- CREATING VECTOR STORE ---")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        persist_directory=persist_directory,
        collection_metadata={"hnsw:space": "cosine"}
    )
    print(f"-- VECTOR STORE CREATED AND SAVED TO {persist_directory} ---")

    return vectorstore
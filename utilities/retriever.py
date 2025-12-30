from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

persistent_directory="db/chroma_db"
embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")

db = Chroma(
    persist_directory=persistent_directory,
    embedding_function=embedding_model,
    collection_metadata={"hnsw:space": "cosine"}
)

retriever = db.as_retriever(search_kwargs={"k": 3})
# retriever = db.as_retriever(
#     search_type="similarity_score_threshold",
#     search_kwargs={
#         "k": 5, 
#         "score_threshold": 0.3 # Only return chunks with cosine similarity ≥ 0.3
#     }
# )

def retrieve_chunks(query: str):
    relevant_docs = retriever.invoke(query)

    return relevant_docs
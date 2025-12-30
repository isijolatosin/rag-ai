from langchain_text_splitters import CharacterTextSplitter


def split_documents(documents, chunk_size=800, chunk_overlap=0):
    """Split documents into smaller chunks with overlap"""
    print("-- SPLITTING DOCUMENTS INTO CHUNKS ---")

    text_splitter = CharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    chunks = text_splitter.split_documents(documents)
    # for i, chunk in enumerate(chunks[:5]):
    #     print(f"\n --- Chunk {i+1} ---")
    #     print(f"Source: {chunk.metadata['source']}")
    #     print(f"Length: {len(chunk.page_content)} characters")
    #     print(f"Content:")
    #     print(chunk.page_content)
    #     print("-" * 50)

    # if len(chunks) > 5:
    #     print((f"\n... and {len(chunks) - 5} more chunks"))

    return chunks
import os

from langchain_community.document_loaders import (DirectoryLoader,
                                                  Docx2txtLoader, PyPDFLoader,
                                                  TextLoader)


def load_documents(documents_path="documents"):
    """Load all text files from the docs directory"""
    print(f"-- LOADING DOCUMENTS FROM {documents_path} ---")

    # CHECK IF DOCUMENTS DIRECTORY EXISTS
    if not os.path.exists(documents_path):
        raise FileNotFoundError(f"-- The directory {documents_path} does not exist. Please create it and add your company files ---")

    # LOAD ALL FILES FROM THE DOCUMENTS DIRECTORY
    documents = []

    documents += DirectoryLoader(
        path=documents_path,
        glob="**/*.txt",
        loader_cls=TextLoader,
    ).load()

    documents += DirectoryLoader(
        path=documents_path,
        glob="**/*.pdf",
        loader_cls=PyPDFLoader,
    ).load()

    documents += DirectoryLoader(
        path=documents_path,
        glob="**/*.docx",
        loader_cls=Docx2txtLoader,
    ).load()

    if len(documents) == 0:
        raise FileNotFoundError(f"-- No .txt or .pdf or .docx files found in {documents_path}. Please add your company documents. ---")

    print(f"documents, {len(documents)}")
    return documents
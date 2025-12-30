## RAG PYTHON API (FastAPI + OpenAI Responses)

# This service:

1. Ingests documents (.txt, .pdf, .docx)
2. Builds vector embeddings
3. Retrieves relevant chunks for a query
4. Streams AI responses token-by-token to the client

## ARCHITECTURE OVERVIEW

Client (Browser / Postman)
│
│ SSE (text/event-stream)
▼
FastAPI (Python RAG API)
│
├── Document loaders (txt / pdf / docx)
├── Text splitters
├── Embeddings (OpenAI)
├── Vector store (Chroma)
├── Retriever
├── Cache (Redis)
└── OpenAI Responses API (streaming)

## PROJECT STRUCTURE

python_api/
├── app.py # FastAPI app
├── utilities/
│ ├── loaders.py # Document loaders
│ ├── splitters.py # Chunking logic
│ ├── vector_store.py # Chroma setup
│ ├── retriever.py # Similarity search
│ ├── cache.py # Redis cache helpers
│ └── tokens.py # Token accounting
├── RAG/
│ └── Documents/ # Uploaded documents
└── README.md

# PYTHON VERSION

python3.11 --version

# VIRTUAL ENVIRONMENT

- RUN python3.11 -m venv venv
- RUN source venv/bin/activate

# 🔐 ENVIRONMENT VARIABLES

OPENAI_API_KEY=sk-xxxx
REDIS_URL=redis://localhost:6379
DAILY_TOKEN_LIMIT=50000
MODEL_MAX_TOKENS=4096

# 📄 DOCUMENT INGESTION

- .TXT
- .PDF
- .DOCX

# 🚀 API ENDPOINT

- /process-file - File upload
- /process-query - chatting with api

# 🔹 API RESPONSE - PROCESS-FILE ENDPOINT

```{
  "message": "File processed and vector store updated",
  "file": {
    "filename": "example.pdf",
    "path": "RAG/Documents/example.pdf"
  }
}
```

# 🔹 API RESPONSE - PROCESS-QUERY ENDPOINT

```{
  "query": "What is Nvidia known for?",
  "user_id": "user_123"
}
```

### What happens internally

- Retrieve relevant chunks from Chroma
- Build RAG prompt
- Check Redis cache
- Stream response from OpenAI
- Track token usage
- Cache final output

### 🌊 Streaming (SSE)

#### The API uses Server-Sent Events (SSE).

- Content-Type: text/event-stream
- Cache-Control: no-cache
- Connection: keep-alive
- X-Accel-Buffering: no

#### Stream format

data: Hello
data: world
data: !
data: [DONE]

# 🧠 Caching Strategy (Redis)

- Key: cache:{query}
- TTL: 24 hours
- Cached responses are streamed instantly without calling OpenAI.

# 🔢 Token Management

- Per-user daily token tracking
- Input token estimation
- Output token enforcement
- Prevents over-usage

# 🔌 Node.js Integration

- Node can:
- Upload documents
- Proxy queries
- Forward SSE stream to frontend
  Node uploads files → Python processes → Python streams AI output → Node forwards to client.

#### TO INSTALL PACKAGES WITH ONE RUN

- pip install -r requirements.txt
- pip list - to verify

import asyncio
import os
import re
import shutil
import traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from openai import OpenAI
from pydantic import BaseModel

from utilities.cache import get_cached_response
from utilities.loader import load_documents
from utilities.retriever import retrieve_chunks
from utilities.set_cache import set_cached_response
from utilities.splitters import split_documents
from utilities.tokens import add_tokens, estimate_tokens, get_tokens_used_today
from utilities.vector_store import create_vector_store

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # use specific domains in production
    allow_credentials=True,
    allow_methods=["*"],  # includes OPTIONS
    allow_headers=["*"],
)
executor = ThreadPoolExecutor(max_workers=1)

# OpenAI setup
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
# Token & model limits
DAILY_TOKEN_LIMIT = int(os.environ.get("DAILY_TOKEN_LIMIT"))
MODEL_MAX_TOKENS = int(os.environ.get("MODEL_MAX_TOKENS"))
SAFE_FLUSH_RE = re.compile(r".*[\s\.\,\!\?\:\;\)\]\}\n]$")

openai_client = OpenAI(api_key=OPENAI_KEY)

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "RAG" / "Documents"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

class QueryPayload(BaseModel):
    query: str
    user_id: str
    source: str | None = "direct-api"

# Helper to generate system prompt
def get_rag_system_prompt(query: str, relevant_docs: list[str]) -> str:
    full_sentence = "\n\n".join(relevant_docs)
    return f"""
You are an intelligent, adaptive AI assistant that understands and takes the user's input and responds accurately, helpfully, and human-like.

Based on the following Documents, please answer this question: "{query}"

Documents: "{full_sentence}"
"""

@app.post("/process-file")
async def process_file(file: UploadFile = File(...)):
    try:
        # Save uploaded file
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Run RAG pipeline
        documents = load_documents(documents_path=str(UPLOAD_DIR.resolve()))
        chunks = split_documents(documents)
        create_vector_store(chunks)

        return JSONResponse(
            content={
                "message": "File processed and vector store updated",
                "file": {
                    "filename": file.filename,
                    "path": str(file_path),
                },
            }
        )
    except Exception as e:
        traceback.print_exc() 
        raise HTTPException(status_code=500, detail=str(e))

###### Streaming /process-query endpoint
@app.post("/process-query")
async def process_query(payload: QueryPayload, request: Request):
    query = payload.query.strip()
    
    if not query:
        raise HTTPException(status_code=400, detail="Query is empty")

    # Step 1: Retrieve RAG chunks
    relevant_docs = [d.page_content for d in retrieve_chunks(query)]

    # Step 2: Check cache
    cached = await get_cached_response(query)
    if cached:
        async def cached_gen():
            yield cached
        return StreamingResponse(cached_gen(), media_type="text/event-stream")
    
    # Step 3: Token management
    used_today = int(await get_tokens_used_today(payload.user_id))
    prompt = get_rag_system_prompt(query, relevant_docs)
    estimated_input_tokens = int(estimate_tokens(prompt))
    remaining_tokens = DAILY_TOKEN_LIMIT - used_today - estimated_input_tokens
    max_output_tokens = min(remaining_tokens, MODEL_MAX_TOKENS)

    if remaining_tokens <= 0 or max_output_tokens < 50:
        raise HTTPException(status_code=429, detail="Not enough tokens left for a response")

    # Step 4: Generate completion (streaming)
    async def event_stream():
        loop = asyncio.get_running_loop()
        stream_response = ""
        buffer = ""
        tokens_used_in_stream = 0
        token_limit_exceeded = False

        def openai_stream():
            return openai_client.responses.create(
                model="gpt-4o-mini",
                input=prompt,
                stream=True,
                max_output_tokens=max_output_tokens,
            )

        try:
            stream_manager = await loop.run_in_executor(executor, openai_stream)
            for event in stream_manager:
                if event.type != "response.output_text.delta":
                    continue

                delta = event.delta
                if not delta:
                    continue

                # Estimate tokens for this chunk
                estimated = estimate_tokens(delta)
                tokens_used_in_stream += estimated

                # 🚨 Enforce token limit DURING stream
                if used_today + tokens_used_in_stream > DAILY_TOKEN_LIMIT:
                    token_limit_exceeded = True
                    yield "data: [TOKEN_LIMIT_EXCEEDED]\n\n"
                    break

                buffer += delta
                stream_response += delta

                # Flush only when buffer ends cleanly
                if SAFE_FLUSH_RE.match(buffer):
                    yield f"data: {buffer}\n\n"
                    buffer = ""

                await asyncio.sleep(0)

            # Flush anything remaining
            if buffer and not token_limit_exceeded:
                yield f"data: {buffer}\n\n"

        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"
        finally:
            # Only charge tokens that were actually streamed
            if tokens_used_in_stream > 0:
                await add_tokens(payload.user_id, tokens_used_in_stream)
                
            # Cache partial response ONLY if not exceeded
            if stream_response and not token_limit_exceeded:
                await set_cached_response(query, stream_response)

            yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    })
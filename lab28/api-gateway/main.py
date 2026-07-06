# api-gateway/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from prometheus_fastapi_instrumentator import Instrumentator
import httpx, os, time

app = FastAPI(title="AI Platform API Gateway")
Instrumentator().instrument(app).expose(app)  # Integration 9: Prometheus

VLLM_URL = os.environ["VLLM_URL"]
QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")

class ChatRequest(BaseModel):
    query: str
    embedding: Optional[List[float]] = None

@app.post("/api/v1/chat")
async def chat(chat_req: ChatRequest):
    query = chat_req.query
    embedding = chat_req.embedding or [0.0] * 384
    start = time.time()

    # 1. Vector search
    try:
        async with httpx.AsyncClient() as client:
            search_resp = await client.post(f"{QDRANT_URL}/collections/documents/points/search", json={
                "vector": embedding,
                "limit": 3
            })
            search_resp.raise_for_status()
            context = search_resp.json().get("result", [])
    except Exception:
        context = []  # Graceful degradation nếu Qdrant sập

    # 2. LLM inference
    prompt = f"Context: {context}\n\nQuery: {query}"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            llm_resp = await client.post(f"{VLLM_URL}/v1/chat/completions", json={
                "model": "Qwen/Qwen2.5-7B-Instruct-GPTQ-Int4",
                "messages": [{"role": "user", "content": prompt}]
            })
            llm_resp.raise_for_status()
            result = llm_resp.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="LLM request timeout")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM gateway connection error: {e}")

    latency = (time.time() - start) * 1000

    return {
        "answer": result["choices"][0]["message"]["content"],
        "latency_ms": round(latency, 2),
        "model": result["model"]
    }

@app.get("/health")
def health():
    return {"status": "ok"}

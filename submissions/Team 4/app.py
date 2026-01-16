from fastapi import FastAPI
from pydantic import BaseModel
from rag_engine import answer_query_api

app = FastAPI(
    title="MetaKGP GraphMind",
    description="RAG + Graph of Thoughts based QA system for MetaKGP",
    version="1.0.0"
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------- Request / Response Models --------

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    sources: list[str]

# -------- API Endpoint --------

@app.post("/query", response_model=QueryResponse)
def query_rag(req: QueryRequest):
    result = answer_query_api(req.question)

    return {
        "answer": result.get("answer", "I don't know."),
        "sources": result.get("sources", [])
    }




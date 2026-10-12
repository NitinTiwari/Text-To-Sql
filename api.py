import json
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from config import DB_FILE, OLLAMA_BASE_URL, TEXT_TO_SQL_MODEL
from main import db_url, extract_schema, get_data_from_database

app = FastAPI(
    title="AI Data Analyst (Text-to-SQL) API",
    description="REST API for natural language text-to-SQL generation and database querying.",
    version="1.0.0",
)

# Enable CORS for external and frontend consumers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    prompt: str = Field(..., description="Natural language question about the database", example="Total revenue from all orders")
    model_name: Optional[str] = Field(default=TEXT_TO_SQL_MODEL, description="Ollama model to use")
    base_url: Optional[str] = Field(default=OLLAMA_BASE_URL, description="Ollama server base URL")


class QueryResponse(BaseModel):
    sql: str
    columns: List[str]
    data: List[Any]


@app.get("/")
def root():
    return {
        "message": "AI Data Analyst (Text-to-SQL) API is running.",
        "docs_url": "/docs",
        "health_url": "/health",
        "schema_url": "/schema"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "database": DB_FILE,
        "default_model": TEXT_TO_SQL_MODEL
    }


@app.get("/schema")
def get_schema():
    try:
        raw_schema = extract_schema(db_url)
        parsed_schema = json.loads(raw_schema)
        return {"schema": parsed_schema}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract schema: {str(e)}")


@app.post("/query", response_model=QueryResponse)
def run_query(request: QueryRequest):
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Query prompt cannot be empty.")

    try:
        result = get_data_from_database(
            prompt=request.prompt,
            model_name=request.model_name or TEXT_TO_SQL_MODEL,
            base_url=request.base_url or OLLAMA_BASE_URL,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query execution error: {str(e)}")


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)

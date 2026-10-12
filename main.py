#Step1: Extract Schema
from pathlib import Path
import os
import json
import re
import sqlite3
from sqlalchemy import create_engine, inspect
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM

from config import DB_FILE, OLLAMA_BASE_URL, TEXT_TO_SQL_MODEL

db_url = f"sqlite:///{DB_FILE}"
def extract_schema(db_url):
    engine = create_engine(db_url)
    inspector = inspect(engine)
    schema = {}

    for table_name in inspector.get_table_names():
        columns = inspector.get_columns(table_name)
        schema[table_name] = [col['name'] for col in columns]
    return json.dumps(schema)


def clean_sql_query(raw_response: str) -> str:
    """Removes thinking tags, markdown fences, and preambles from LLM response."""
    # Remove <think>...</think> reasoning blocks from DeepSeek-R1
    cleaned = re.sub(r"<think>.*?</think>", "", raw_response, flags=re.DOTALL)

    # Extract SQL inside markdown fences if present
    match = re.search(r"```(?:sql)?\s*(.*?)\s*```", cleaned, flags=re.DOTALL | re.IGNORECASE)
    if match:
        cleaned = match.group(1)
    else:
        cleaned = re.sub(r"^```(?:sql)?", "", cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.replace("```", "")

    # Remove any prefix like 'SQL Query:'
    cleaned = re.sub(r"^(?:SQL\s*Query\s*:?|SQLite\s*Query\s*:?)", "", cleaned.strip(), flags=re.IGNORECASE)
    return cleaned.strip()


def get_ollama_base_url() -> str:
    try:
        import streamlit as st
        if "OLLAMA_BASE_URL" in st.secrets:
            return str(st.secrets["OLLAMA_BASE_URL"])
    except Exception:
        pass
    return os.getenv("OLLAMA_BASE_URL", OLLAMA_BASE_URL)


#Step2: Text to SQL
def text_to_sql(schema, prompt, model_name=TEXT_TO_SQL_MODEL, base_url=None):
    SYSTEM_PROMPT = """You are an expert SQL generator for SQLite. Given a database schema and a user prompt, generate a valid SQL query that answers the prompt. 
Only use the tables and columns provided in the schema. ALWAYS ensure the SQL syntax is valid SQLite. 
Output ONLY the raw SQL query. No preamble, no explanation, no markdown backticks, and do not use <think> tags."""

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("user", "Schema:\n{schema}\n\nQuestion: {user_prompt}\n\nSQL Query:")
    ])

    resolved_base_url = base_url or get_ollama_base_url()
    model = OllamaLLM(model=model_name, temperature=0, base_url=resolved_base_url)
    chain = prompt_template | model

    raw_response = chain.invoke({"schema": schema, "user_prompt": prompt})
    return clean_sql_query(raw_response)


def get_data_from_database(prompt, model_name=TEXT_TO_SQL_MODEL, base_url=None):
    schema = extract_schema(db_url)
    sql_query = text_to_sql(schema, prompt, model_name=model_name, base_url=base_url)
    
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    cursor.execute(sql_query)
    columns = [desc[0] for desc in cursor.description] if cursor.description else []
    results = cursor.fetchall()
    conn.close()
    
    return {
        "sql": sql_query,
        "columns": columns,
        "data": results
    }



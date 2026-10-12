---
title: AI Data Analyst (Text-To-SQL)
emoji: 🤖
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 5.16.0
app_file: app.py
pinned: false
---

# AI Data Analyst (Text-to-SQL)

An interactive Gradio application that turns natural-language questions into SQL queries for a SQLite database using a local or remote Ollama model. The app inspects the database schema, uses an LLM to generate SQL, executes that query against the database, and displays the result set directly in the browser.

## Features

- Reads the SQLite database schema automatically
- Uses LangChain + Ollama to generate SQLite queries from natural language questions
- Runs the generated SQL against the local database
- Clean, reactive Gradio web interface with interactive tables and query syntax highlighting
- Optional FastAPI backend integration with direct fallback
- Includes a sample SQLite database (`amazon.db`) for immediate testing

## Tech stack

- Python 3.13+
- Gradio (Web frontend & Hugging Face Spaces SDK)
- FastAPI & Uvicorn (REST API backend)
- SQLAlchemy
- LangChain Core
- LangChain Ollama
- Pandas
- SQLite

## Prerequisites

Before running the app, make sure you have:

- Python installed
- Ollama installed locally or accessible via a remote URL / ngrok tunnel
- At least one model pulled into Ollama, for example:
  - `ollama pull llama3.1:latest`
  - `ollama pull mistral:latest`
  - `ollama pull deepseek-r1:8b`

## Setup

From the project root:

1. Create and activate a virtual environment
   - Windows PowerShell:
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```

2. Install dependencies
   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Create the sample database if it is missing
   ```powershell
   python create_database.py
   ```

4. Run the application:
   - **Option A: Run Gradio UI directly**
     ```powershell
     python app.py
     ```
     Access the web UI at `http://localhost:7860`.

   - **Option B: Run FastAPI backend + Gradio UI**
     - Terminal 1 (FastAPI with Swagger docs at `http://localhost:8000/docs`):
       ```powershell
       python -m uvicorn api:app --reload --port 8000
       ```
     - Terminal 2 (Gradio UI):
       ```powershell
       python app.py
       ```

## Project structure

- `.env` — environment variables (database path, model, Ollama URL, API URL)
- `config.py` — centralized configuration loader
- `main.py` — core text-to-SQL logic and schema extraction
- `api.py` — FastAPI REST server exposing `/query`, `/schema`, `/health`, and `/docs`
- `app.py` — Gradio web application (entry point for Hugging Face Spaces)
- `create_database.py` — creates the demo SQLite database
- `amazon.db` — sample database used by the app

## Example questions

- Total products sold in 2024
- List all customers and their cities
- Top 3 most expensive products
- Total revenue from all orders

## Notes

- The app connects to your Ollama server (default `http://localhost:11434`).
- When deployed on Hugging Face Spaces, your remote Space cannot reach your PC's `localhost` directly. You can expose your local Ollama instance via an **ngrok** tunnel (`ngrok http 11434`) and paste the public URL into the Ollama Base URL field.

# AI Data Analyst (Text-to-SQL)

A small Streamlit application that turns natural-language questions into SQL for a SQLite database using a local Ollama model. The app inspects the schema, asks the LLM to generate SQL, executes that query against the database, and displays the result set in the browser.

## Features

- Reads the SQLite database schema automatically
- Uses LangChain + Ollama to generate SQL from natural language
- Runs the generated SQL against the local database
- Shows the results in a simple Streamlit interface
- Includes a sample SQLite database for demo/testing

## Tech stack

- Python 3.13+
- Streamlit
- SQLAlchemy
- LangChain Core
- LangChain Ollama
- Pandas
- SQLite

## Prerequisites

Before running the app, make sure you have:

- Python installed
- Ollama installed locally
- At least one model pulled into Ollama, for example:

  - `ollama pull llama3.1:latest`
  - `ollama pull mistral:latest`
  - `ollama pull deepseek-r1:8b`

## Setup

From the project root:

1. Create and activate a virtual environment
   - Windows PowerShell:
     `python -m venv .venv`
     `.\.venv\Scripts\Activate.ps1`

2. Install dependencies
   `python -m pip install -r requirements.txt`

3. Create the sample database if it is missing
   `python create_database.py`

4. Start the app
   `streamlit run frontend.py`

## Project structure

- `.env` — environment variables (database path, model, Ollama URL)
- `config.py` — centralized configuration loader
- `main.py` — schema extraction and SQL generation logic
- `frontend.py` — Streamlit UI
- `create_database.py` — creates the demo SQLite database
- `amazon.db` — sample database used by the app

## Example questions

- Total products sold in 2024
- List all customers and their cities
- Top 3 most expensive products
- Total revenue from all orders

## Notes

- The app depends on a local Ollama server being available.
- The default model selection in the UI includes `llama3.1:latest`, `mistral:latest`, and `deepseek-r1:8b`.
- Some reasoning models such as DeepSeek R1 can take significantly longer to respond on CPU-only machines.

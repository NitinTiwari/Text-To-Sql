import os
import requests
import pandas as pd
import gradio as gr

from config import DB_FILE, OLLAMA_BASE_URL, TEXT_TO_SQL_MODEL, API_BASE_URL
from main import get_data_from_database

DEFAULT_MODELS = ["llama3.1:latest", "mistral:latest", "deepseek-r1:8b"]
if TEXT_TO_SQL_MODEL and TEXT_TO_SQL_MODEL not in DEFAULT_MODELS:
    DEFAULT_MODELS.insert(0, TEXT_TO_SQL_MODEL)


def run_text_to_sql(query: str, model_name: str, ollama_url: str, api_url: str):
    """Processes user query either through the FastAPI backend or directly via main.py."""
    if not query or not query.strip():
        return "", pd.DataFrame(), "⚠️ **Please enter a question to analyze.**"

    sql_query = ""
    columns = []
    data = []
    source = "Direct Execution"

    # Try calling FastAPI backend first if provided
    if api_url and api_url.strip():
        try:
            resp = requests.post(
                f"{api_url.strip().rstrip('/')}/query",
                json={"prompt": query, "model_name": model_name, "base_url": ollama_url},
                timeout=120,
            )
            if resp.status_code == 200:
                result = resp.json()
                sql_query = result.get("sql", "")
                columns = result.get("columns", [])
                data = result.get("data", [])
                source = "FastAPI Backend"
            else:
                detail = resp.json().get("detail", resp.text) if "application/json" in resp.headers.get("content-type", "") else resp.text
                return "", pd.DataFrame(), f"❌ **API Error ({resp.status_code}):** {detail}"
        except requests.exceptions.ConnectionError:
            # Fall back seamlessly to direct python execution
            source = "Direct Execution (FastAPI offline)"

    # If not served by API, run direct database & LLM pipeline
    if not sql_query:
        try:
            result = get_data_from_database(
                prompt=query,
                model_name=model_name,
                base_url=ollama_url
            )
            sql_query = result.get("sql", "")
            columns = result.get("columns", [])
            data = result.get("data", [])
        except Exception as e:
            err_msg = str(e)
            if any(term in err_msg for term in ["Connection refused", "ConnectError", "WinError 10061", "Failed to establish a new connection"]):
                help_text = (
                    f"❌ **Connection Error:** Cannot reach Ollama at `{ollama_url}`.\n\n"
                    "**How to connect when deployed remotely (e.g. Hugging Face Spaces):**\n"
                    "1. Remote servers cannot connect to your personal machine's `localhost` directly.\n"
                    "2. Expose your local Ollama port using an **ngrok** tunnel:\n"
                    "   ```bash\n   ngrok http 11434\n   ```\n"
                    "3. Paste the generated public URL (e.g., `https://xyz.ngrok-free.app`) into the **Ollama Base URL** field below."
                )
                return "", pd.DataFrame(), help_text
            return "", pd.DataFrame(), f"❌ **Error executing query:** {err_msg}"

    # Build DataFrame for Gradio output
    if data and columns:
        df = pd.DataFrame(data, columns=columns)
    elif data:
        df = pd.DataFrame(data)
    else:
        df = pd.DataFrame({"Result": ["Query executed successfully, but returned 0 rows."]})

    status_message = f"✅ **Analysis complete!** (Served via {source})"
    return sql_query, df, status_message


# Build Gradio UI
with gr.Blocks(title="AI Data Analyst (Text-to-SQL)") as demo:
    gr.Markdown(
        """
        # 🤖 AI Data Analyst (Text-to-SQL)
        Ask questions about your SQLite database in natural language. The LLM translates your question to SQL, runs it against the database, and visualizes the results.
        """
    )

    with gr.Row():
        with gr.Column(scale=1):
            with gr.Accordion("⚙️ Model & Server Settings", open=True):
                model_dropdown = gr.Dropdown(
                    choices=DEFAULT_MODELS,
                    value=TEXT_TO_SQL_MODEL,
                    label="LLM Model",
                    info="Ollama model for SQL synthesis"
                )
                ollama_url_input = gr.Textbox(
                    value=OLLAMA_BASE_URL,
                    label="Ollama Base URL",
                    info="Local URL (http://localhost:11434) or public tunnel (ngrok)"
                )
                api_url_input = gr.Textbox(
                    value=API_BASE_URL,
                    label="FastAPI Backend URL (Optional)",
                    info="If unreachable, automatically falls back to direct execution"
                )

            query_input = gr.Textbox(
                lines=3,
                label="💬 Enter your question:",
                placeholder="e.g., Total products sold in 2024",
                autofocus=True
            )

            with gr.Row():
                submit_btn = gr.Button("🚀 Analyze Query", variant="primary")
                clear_btn = gr.Button("🗑️ Clear")

            gr.Examples(
                examples=[
                    ["Total products sold in 2024"],
                    ["List all customers and their cities"],
                    ["Top 3 most expensive products"],
                    ["Total revenue from all orders"],
                ],
                inputs=query_input,
                label="💡 Sample Questions"
            )

        with gr.Column(scale=2):
            status_output = gr.Markdown()
            sql_output = gr.Code(
                language="sql",
                label="🔍 Generated SQLite Query",
                lines=5
            )
            table_output = gr.Dataframe(
                label="📊 Query Results",
                interactive=False
            )

    submit_btn.click(
        fn=run_text_to_sql,
        inputs=[query_input, model_dropdown, ollama_url_input, api_url_input],
        outputs=[sql_output, table_output, status_output]
    )
    query_input.submit(
        fn=run_text_to_sql,
        inputs=[query_input, model_dropdown, ollama_url_input, api_url_input],
        outputs=[sql_output, table_output, status_output]
    )
    clear_btn.click(
        fn=lambda: ("", "", pd.DataFrame(), ""),
        inputs=[],
        outputs=[query_input, sql_output, table_output, status_output]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)

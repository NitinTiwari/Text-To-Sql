#Step3: Build Streamlit frontend
import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import OLLAMA_BASE_URL, TEXT_TO_SQL_MODEL
from main import get_data_from_database

def get_secret_or_env(key: str, default: str = "") -> str:
    try:
        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return os.getenv(key, default)

DEFAULT_MODELS = ["llama3.1:latest", "mistral:latest", "deepseek-r1:8b"]
configured_model = get_secret_or_env("TEXT_TO_SQL_MODEL", TEXT_TO_SQL_MODEL)
configured_base_url = get_secret_or_env("OLLAMA_BASE_URL", OLLAMA_BASE_URL)

if configured_model and configured_model not in DEFAULT_MODELS:
    DEFAULT_MODELS.insert(0, configured_model)

st.set_page_config(
    page_title="AI Data Analyst (Text-to-SQL)",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 AI Data Analyst (Text-to-SQL)")
st.markdown("Ask questions about your data in natural language.")

# Sidebar for settings & model selection
with st.sidebar:
    st.header("⚙️ Settings")

    ollama_base_url = st.text_input(
        "Ollama Base URL:",
        value=configured_base_url,
        help="On Streamlit Cloud, localhost or host.docker.internal will not connect to your computer. Use a public tunnel URL like ngrok."
    )

    is_local_address = any(h in ollama_base_url for h in ["localhost", "127.0.0.1", "host.docker.internal"])
    if is_local_address:
        st.warning("⚠️ **Note for Streamlit Cloud**: Remote servers cannot connect to `localhost` or `host.docker.internal`. Use an [ngrok tunnel](https://ngrok.com) or a remote Ollama server.")

    default_model_index = 0
    if configured_model in DEFAULT_MODELS:
        default_model_index = DEFAULT_MODELS.index(configured_model)

    model_choice = st.selectbox(
        "Select LLM Model:",
        options=DEFAULT_MODELS,
        index=default_model_index,
        help="Set TEXT_TO_SQL_MODEL and OLLAMA_BASE_URL in Streamlit secrets or override them here."
    )
    if "deepseek" in model_choice:
        st.warning("⚠️ DeepSeek-R1 runs reasoning tokens (<think>) before responding. On CPU, this can take 5–10 minutes.")

    st.markdown("---")
    st.markdown("**Sample Questions:**")
    sample_queries = [
        "Total products sold in 2024",
        "List all customers and their cities",
        "Top 3 most expensive products",
        "Total revenue from all orders"
    ]
    for q in sample_queries:
        if st.button(q, key=f"sample_{q}"):
            st.session_state["query_input"] = q

default_query = st.session_state.get("query_input", "")
user_query = st.text_area("💬 Enter your question:", value=default_query, placeholder="e.g., Total products sold in 2024")

if st.button("🚀 Analyze", type="primary"):
    if user_query.strip() == "":
        st.warning("Please enter a question to analyze.")
    else:
        with st.spinner(f"Analyzing your query with {model_choice}..."):
            try:
                response = get_data_from_database(user_query, model_name=model_choice, base_url=ollama_base_url)
                sql_query = response.get("sql", "")
                columns = response.get("columns", [])
                data = response.get("data", [])

                st.success("Analysis complete!")
                
                # Display the generated SQL
                with st.expander("🔍 Generated SQL Query", expanded=True):
                    st.code(sql_query, language="sql")

                # Display the results
                st.subheader("📊 Query Results")
                if data and columns:
                    df = pd.DataFrame(data, columns=columns)
                    st.dataframe(df, use_container_width=True)
                elif data:
                    st.write(data)
                else:
                    st.info("Query executed successfully, but returned no rows.")

            except Exception as e:
                err_msg = str(e)
                if any(phrase in err_msg for phrase in ["Connection refused", "ConnectError", "Failed to establish a new connection", "111", "WinError 10061"]):
                    st.error(
                        f"❌ **Connection Error:** Cannot reach Ollama at `{ollama_base_url}`.\n\n"
                        "**Why this happens:**\n"
                        "- When deployed on **Streamlit Cloud**, the app runs on a remote server that cannot reach your computer's `localhost` or `host.docker.internal`.\n\n"
                        "**How to connect your local Ollama:**\n"
                        "1. Run an **ngrok** tunnel on your machine:\n"
                        "   ```bash\n   ngrok http 11434\n   ```\n"
                        "2. Copy the public URL (e.g., `https://xyz.ngrok-free.app`).\n"
                        "3. Paste it into the **Ollama Base URL** box in the sidebar (or in Streamlit Cloud Secrets under `OLLAMA_BASE_URL`).\n"
                        "4. Ensure Ollama allows cross-origin requests by running it with `OLLAMA_ORIGINS=\"*\"`."
                    )
                else:
                    st.error(f"❌ Error executing query: {err_msg}")

st.markdown("""
    <style>
    textarea {
        font-size: 16px !important;
    }
    </style>
""", unsafe_allow_html=True)

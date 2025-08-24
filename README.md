# Insight Agent – PDF-to-Insight using NLP & LLMs

## 🎯 Objective
Extract structured summaries and insights from long, unstructured business documents (PDFs, filings, reports) using NLP and LLMs.

## 🚀 Features
- Extracts sections from PDFs
- Summarizes each section with a local LLM (Ollama `phi3:mini`)
- Saves structured summaries into `data/summaries/<doc_name>/`


## 🚀 Quickstart
```bash
python -m venv .venv && source .venv/Scripts/activate
pip install -r requirements.txt

📁 Project Structure
Insight-agent/
├── data/
├── notebooks/
├── src/
├── app/
├── README.md
├── requirements.txt
├── pyproject.toml
└── .gitignore

---

### 📄 `.gitignore`

```gitignore
# data
/data/
*.pdf

# envs
.venv/
.env

# Jupyter artifacts
__pycache__/
.ipynb_checkpoints/

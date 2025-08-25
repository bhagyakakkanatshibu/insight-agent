
# Import your existing modules
import parser
from pathlib import Path

import streamlit as st

import agent
import segmenter

st.set_page_config(page_title="Insight Agent", layout="wide")
st.title("📄 Insight Agent - Smart Document Summarizer")

uploaded_file = st.file_uploader("Upload a PDF or TXT file", type=["pdf", "txt"])

if uploaded_file is not None:
    # Save uploaded file temporarily
    temp_path = Path("data/uploads") / uploaded_file.name
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success(f"Uploaded: {uploaded_file.name}")

    if st.button("Process Document"):
        with st.spinner("Parsing file..."):
            text = parser.parse_file(str(temp_path))  # Use your parser.py

        with st.spinner("Segmenting text..."):
            sections = segmenter.segment_text(text)  # Use your segmenter.py

        st.subheader("Summaries")
        for section_name, section_text in sections.items():
            with st.spinner(f"Summarizing {section_name}..."):
                summary = agent.summarize_text(section_text, section_name=section_name)  # Use agent.py
            st.markdown(f"### {section_name}")
            st.write(summary if summary else "_No summary generated._")

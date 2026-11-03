import streamlit as st
import json
from text_analyzer import summarize_text, extract_keywords
from pathlib import Path
import base64
import time

# Local imports
from document_processor import (
    validate_file,
    _save_to_temp,
    convert_document,
    cleanup_temp,
)

# Title and layout
st.set_page_config(page_title="Smart Document Intelligence", layout="wide")
st.title("Smart Document Intelligence")
st.caption("Convert documents into structured Markdown and explore their content.")

# Sidebar for upload and actions
with st.sidebar:
    st.header("Upload & Convert")
    uploaded = st.file_uploader(
        "Choose a document", type=["pdf", "docx", "pptx", "xlsx", "html", "htm", "txt", "csv"]
    )
    if uploaded:
        # Show file info
        st.write(f"**Filename:** {uploaded.name}")
        st.write(f"**Size:** {uploaded.size / 1024:.2f} KB")
        # Validate
        validation = validate_file(uploaded)
        if not validation["valid"]:
            st.error(validation["message"])
        else:
            if st.button("Convert Document"):
                st.session_state.convert_requested = True
                st.session_state.uploaded_file = uploaded
    if st.button("Clear Results"):
        for key in ["convert_requested", "uploaded_file", "result", "temp_path"]:
            if key in st.session_state:
                del st.session_state[key]
        st.experimental_rerun()

# Main area
if "convert_requested" in st.session_state and st.session_state.convert_requested:
    uploaded = st.session_state.uploaded_file
    # Save to temp
    temp_path = _save_to_temp(uploaded)
    st.session_state.temp_path = temp_path
    with st.spinner("Converting…"):
        try:
            result = convert_document(str(temp_path))
            st.session_state.result = result
        except Exception as e:
            st.error(f"Conversion failed: {e}")
            cleanup_temp(temp_path)
            st.session_state.convert_requested = False
            st.stop()
    cleanup_temp(temp_path)
    st.success("Conversion successful!")

if "result" in st.session_state:
    result = st.session_state.result
    meta = result["metadata"]
    stats = result["stats"]
    markdown = result["markdown"]

    # Metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Input size (KB)", f"{meta['input_size_bytes']/1024:.2f}")
    col2.metric("Output size (KB)", f"{meta['output_size_bytes']/1024:.2f}")
    col3.metric("Duration (s)", f"{meta['duration_seconds']}")
    col4.metric("Word count", stats['word_count'])
    col5.metric("Language", stats.get('language','unknown'))
    # Bar chart
    chart_data = {
        "Word count": stats['word_count'],
        "Char count": stats['char_count'],
        "Line count": stats['line_count'],
        "Heading count": stats['heading_count'],
    }
    st.bar_chart(chart_data)

    # ------- Analysis Section (Summary & Keywords) -------
    st.subheader("Smart Document Analysis")
    # Adjustable summary length
    summary_len = st.slider("Summary length (sentences)", min_value=1, max_value=10, value=3, step=1)
    summary = summarize_text(markdown, sentence_count=summary_len)
    st.markdown("### Document Summary")
    st.write(summary)
    # Adjustable keyword count
    kw_n = st.slider("Number of keywords to show", min_value=5, max_value=30, value=10, step=5)
    keywords = extract_keywords(markdown, top_n=kw_n)
    st.markdown("### Important Keywords")
    st.dataframe(keywords, use_container_width=True)
    # Prepare analysis report JSON
    report = {
        "summary": summary,
        "keywords": keywords,
        "metadata": meta,
        "stats": stats,
    }
    st.download_button(
        label="Download Analysis Report (JSON)",
        data=json.dumps(report, indent=2),
        file_name=uploaded.name.rsplit(".", 1)[0] + "_analysis.json",
        mime="application/json",
    )

    # Tabs for preview
    tabs = st.tabs(["Readable Preview", "Raw Markdown", "Statistics"])
    with tabs[0]:
        st.markdown(markdown)
    with tabs[1]:
        st.code(markdown, language="markdown")
    with tabs[2]:
        st.json({
            "original_filename": uploaded.name,
            **meta,
            **stats,
        })

    # Download buttons
    def _download_button(content: bytes, filename: str, mime: str):
        b64 = base64.b64encode(content).decode()
        href = f"data:{mime};base64,{b64}"
        st.download_button(label=f"Download {filename}", data=href, file_name=filename, mime=mime)

    md_bytes = markdown.encode("utf-8")
    json_bytes = json.dumps({
        "original_filename": uploaded.name,
        **meta,
        **stats,
    }, indent=2).encode("utf-8")
    st.download_button("Download Markdown", data=md_bytes, file_name=uploaded.name.rsplit(".",1)[0] + "_converted.md", mime="text/markdown")
    st.download_button("Download JSON Summary", data=json_bytes, file_name=uploaded.name.rsplit(".",1)[0] + "_summary.json", mime="application/json")

st.caption("Built with Python, Streamlit, and MarkItDown.")

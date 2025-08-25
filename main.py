import os
import tempfile
import zipfile
import io
import shutil
import streamlit as st
from utils.pdf_processing import (
    split_pdf_pages, merge_pdfs, extract_page_range, remove_first_last_pages,
    extract_text_from_pdf, keyword_highlight_pdf, extract_images, extract_tables,
    ocr_pdf, reorder_pages, rotate_pages, add_watermark, extract_metadata
)
from utils.pdf_analysis import rag_qa, summarize_text
from utils.pdf_export import export_to_word, export_to_text, export_text_to_markdown


st.set_page_config(page_title="PDF Toolbox", layout="wide")
st.title("🛠 PDF Toolbox")

with st.sidebar:
    st.header("Tools")
    # Define tool categories
    tool_categories = {
        "PDF Processing": [
            "Split PDF Pages",
            "Merge PDFs",
            "Extract Page Range",
            "Remove First/Last Pages",
        ],
        "Advanced Processing": [
            "Keyword Search & Highlight",
            "Extract Images",
            "Extract Tables",
            "OCR Scanned PDF",
            "Reorder Pages",
            "Rotate Pages",
            "Add Watermark",
            "Extract Metadata",
        ],
        "Analysis": [
            "Summarize PDF",
            "Ask Questions on PDF (RAG)",
        ],
        "Export": [
            "Export to Word (.docx)",
            "Export to Text (.txt)",
            "Export to Markdown (.md)",
        ],
    }

    # Step 1: User selects category
    selected_category = st.selectbox(
        "Choose a Category",
        list(tool_categories.keys())
    )

    # Step 2: Show tools under that category
    tool = st.selectbox(
        "Choose a Tool",
        tool_categories[selected_category]
    )
    # st.caption("Note: For OCR, ensure Tesseract is installed on system path.")


# ------------- Helpers for downloads -------------
def download_bytes(label: str, data: bytes, file_name: str, mime: str):
    st.download_button(label, data, file_name=file_name, mime=mime)


def zip_folder_to_bytes(folder_path: str) -> bytes:
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(folder_path):
            for f in files:
                full = os.path.join(root, f)
                arc = os.path.relpath(full, start=folder_path)
                zf.write(full, arcname=arc)
    mem.seek(0)
    return mem.read()


OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)
def out_file(name: str) -> str:
    return os.path.join(OUTPUT_DIR, name)

# ------------- UI Logic -------------

# Most tools need a PDF file, except "Merge PDFs"
if tool == "Merge PDFs":
    uploaded_files = st.file_uploader("Upload PDFs to merge", type=["pdf"], accept_multiple_files=True)
    if uploaded_files:
        if st.button("Merge"):
            merged = merge_pdfs(uploaded_files)  # returns BytesIO
            download_bytes("📥 Download Merged PDF", merged.getvalue(), "merged.pdf", "application/pdf")
else:
    uploaded = st.file_uploader("Upload PDF", type=["pdf"])
    if uploaded:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded.read())
            pdf_path = tmp.name

        if tool == "Split PDF Pages":
            # Read total pages for UI
            from PyPDF2 import PdfReader as _Reader
            total_pages = len(_Reader(pdf_path).pages)
            option = st.radio("Select Option", ["All Pages", "Page Range", "Single Page"], horizontal=True)

            if option == "All Pages":
                start_page, end_page = 1, total_pages
            elif option == "Page Range":
                start_page = st.number_input("Start Page", 1, total_pages, 1)
                end_page = st.number_input("End Page", start_page, total_pages, total_pages)
            else:
                start_page = st.number_input("Page Number", 1, total_pages, 1)
                end_page = start_page

            if st.button("Split & Download ZIP"):
                zip_bytesio = split_pdf_pages(pdf_path, int(start_page), int(end_page))
                download_bytes("📥 Download ZIP", zip_bytesio.getvalue(), "split_pages.zip", "application/zip")

        elif tool == "Extract Page Range":
            from PyPDF2 import PdfReader as _Reader
            total_pages = len(_Reader(pdf_path).pages)
            start_page = st.number_input("Start Page", 1, total_pages, 1)
            end_page = st.number_input("End Page", start_page, total_pages, total_pages)
            if st.button("Extract Range"):
                out = extract_page_range(pdf_path, int(start_page), int(end_page))
                download_bytes("📥 Download Extracted PDF", out.getvalue(), "extracted_range.pdf", "application/pdf")

        elif tool == "Remove First/Last Pages":
            remove_first = st.checkbox("Remove First Page", value=True)
            remove_last = st.checkbox("Remove Last Page", value=False)
            if st.button("Remove & Download"):
                out = remove_first_last_pages(pdf_path, remove_first, remove_last)
                download_bytes("📥 Download Modified PDF", out.getvalue(), "modified.pdf", "application/pdf")

        elif tool == "Keyword Search & Highlight":
            keyword = st.text_input("Keyword to highlight", "")
            if st.button("Search & Highlight") and keyword.strip():
                out_path = keyword_highlight_pdf(pdf_path, keyword.strip(), out_file("highlighted.pdf"))
                with open(out_path, "rb") as f:
                    download_bytes("📥 Download Highlighted PDF", f.read(), "highlighted.pdf", "application/pdf")

        elif tool == "Extract Images":
            folder = extract_images(pdf_path, output_folder="images_out")
            # st.success(f"Extracted images → {folder}")
            if isinstance(folder, list):
                folder = folder[0]

            if os.path.isdir(folder) and len(os.listdir(folder)) > 0:
                zbytes = zip_folder_to_bytes(folder)
                if st.download_button("📥 Download Images (ZIP)", zbytes, "images.zip", "application/zip"):
                    shutil.rmtree(folder)
                if os.path.isdir(folder):
                    image_files = [os.path.join(folder, f) for f in sorted(os.listdir(folder))]
                    # st.write("### Extracted Images Preview")
                    cols = st.columns(3)  # grid with 3 columns
                    for i, img in enumerate(image_files):
                        with cols[i % 3]:
                            st.image(img, caption=os.path.basename(img), use_container_width=True)

        elif tool == "Extract Tables":
            tables = extract_tables(pdf_path)
            if not tables:
                st.info("No tables detected.")
            else:
                try:
                    import pandas as pd
                except ImportError:
                    st.warning("Install pandas to view tables nicely.")
                    st.write(tables)
                else:
                    for i, t in enumerate(tables):
                        if hasattr(t, "to_csv"):  # Camelot DataFrame
                            df = t
                        else:  # pdfplumber list-of-rows
                            df = pd.DataFrame(t)
                        st.subheader(f"Table {i+1}")
                        st.dataframe(df)

        elif tool == "OCR Scanned PDF":
            # st.info("Requires Tesseract installed on your system.")
            lang = st.selectbox(
                "Select OCR language",
                ["eng", "hin", "fra", "deu", "jpn", "kor"],  # Add more as needed
                index=0
            )
            if st.button("Run OCR"):
                text = ocr_pdf(pdf_path, lang)
                st.text_area("OCR Output", text, height=300)

        elif tool == "Reorder Pages":
            st.caption("Enter comma-separated 0-indexed page order. Example for 3 pages: 2,0,1")
            order_str = st.text_input("New order", "")
            if st.button("Reorder") and order_str.strip():
                new_order = [int(x.strip()) for x in order_str.split(",") if x.strip().isdigit()]
                out_path = reorder_pages(pdf_path, new_order, out_file("reordered.pdf"))
                with open(out_path, "rb") as f:
                    download_bytes("📥 Download Reordered PDF", f.read(), "reordered.pdf", "application/pdf")

        elif tool == "Rotate Pages":
            st.caption("Enter 0-indexed pages, comma-separated. Angle typically 90/180/270.")
            pages_str = st.text_input("Pages to rotate", "")
            angle = st.number_input("Angle", min_value=0, max_value=360, value=90, step=90)
            if st.button("Rotate") and pages_str.strip():
                pages = [int(x.strip()) for x in pages_str.split(",") if x.strip().isdigit()]
                out_path = rotate_pages(pdf_path, pages, int(angle), out_file("rotated.pdf"))
                with open(out_path, "rb") as f:
                    download_bytes("📥 Download Rotated PDF", f.read(), "rotated.pdf", "application/pdf")

        elif tool == "Add Watermark":
            wm = st.text_input("Watermark text", "CONFIDENTIAL")
            if st.button("Apply Watermark"):
                out_path = add_watermark(pdf_path, wm, out_file("watermarked.pdf"))
                with open(out_path, "rb") as f:
                    download_bytes("📥 Download Watermarked PDF", f.read(), "watermarked.pdf", "application/pdf")

        elif tool == "Extract Metadata":
            meta = extract_metadata(pdf_path)
            st.json(meta)

        elif tool == "Summarize PDF":
            text = extract_text_from_pdf(pdf_path)
            # st.info("Using Together.ai LLaMA for summarization. Set TOGETHER_API_KEY in your environment.")
            if st.button("Summarize"):
                with st.spinner("Summarizing... Please wait ⏳"):
                    summary = summarize_text(text)
                st.write(summary)

        elif tool == "Ask Questions on PDF (RAG)":
            # st.info("Uses FAISS + MiniLM embeddings + Together.ai LLaMA. Set TOGETHER_API_KEY in your environment.")
            question = st.text_input("Your question")
            if st.button("Ask") and question.strip():
                text = extract_text_from_pdf(pdf_path)
                with st.spinner("Analyzing... Please wait ⏳"):
                    answer, sources = rag_qa(text, question)
                st.subheader("Answer")
                st.write(answer)
                if sources:
                    st.subheader("Top source chunks")
                    for i, s in enumerate(sources, start=1):
                        st.markdown(f"**Source {i}:**\n\n{getattr(s, 'page_content', '')[:800]}")

        elif tool == "Export to Word (.docx)":
            out = export_to_word(pdf_path, out_file("export.docx"))
            with open(out, "rb") as f:
                download_bytes("📥 Download DOCX", f.read(), "export.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

        elif tool == "Export to Text (.txt)":
            out = export_to_text(pdf_path, out_file("export.txt"))
            with open(out, "rb") as f:
                download_bytes("📥 Download TXT", f.read(), "export.txt", "text/plain")

        elif tool == "Export to Markdown (.md)":
            text = extract_text_from_pdf(pdf_path)
            out = export_text_to_markdown(text, out_file("export.md"))
            with open(out, "rb") as f:
                download_bytes("📥 Download MD", f.read(), "export.md", "text/markdown")
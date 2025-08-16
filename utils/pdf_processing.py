import os
import io
import zipfile
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import pdfplumber
import camelot
from PyPDF2 import PdfReader, PdfWriter


# -------------------------
# BASIC PDF TOOLS (your originals)
# -------------------------

def split_pdf_pages(pdf_path: str, start_page: int, end_page: int) -> io.BytesIO:
    """
    Split selected pages into separate PDFs and return a ZIP (in-memory).
    start_page/end_page are 1-indexed (inclusive).
    """
    reader = PdfReader(pdf_path)
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for i in range(start_page, end_page + 1):
            writer = PdfWriter()
            writer.add_page(reader.pages[i - 1])
            pdf_bytes = io.BytesIO()
            writer.write(pdf_bytes)
            pdf_bytes.seek(0)
            zipf.writestr(f"page_{i}.pdf", pdf_bytes.read())
    zip_buffer.seek(0)
    return zip_buffer


def merge_pdfs(files_or_paths) -> io.BytesIO:
    """
    Merge multiple PDFs. Accepts a list of file-like objects or file paths.
    Returns merged PDF as BytesIO.
    """
    writer = PdfWriter()
    for f in files_or_paths:
        reader = PdfReader(f) if hasattr(f, "read") else PdfReader(str(f))
        for page in reader.pages:
            writer.add_page(page)
    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out


def extract_page_range(pdf_path: str, start_page: int, end_page: int) -> io.BytesIO:
    """Extract a page range (1-indexed, inclusive) into a single PDF (in-memory)."""
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    for i in range(start_page, end_page + 1):
        writer.add_page(reader.pages[i - 1])
    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out


def remove_first_last_pages(pdf_path: str, remove_first: bool, remove_last: bool) -> io.BytesIO:
    """Remove first and/or last page and return modified PDF (in-memory)."""
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    total = len(reader.pages)
    for i in range(total):
        if (remove_first and i == 0) or (remove_last and i == total - 1):
            continue
        writer.add_page(reader.pages[i])
    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out


# -------------------------
# ADVANCED UTILITIES
# -------------------------

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract selectable text (not OCR) via PyMuPDF."""
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    return text


def keyword_highlight_pdf(pdf_path: str, keyword: str, output_path: str = "highlighted.pdf") -> str:
    """Search keyword and highlight occurrences in the PDF (case-insensitive)."""
    doc = fitz.open(pdf_path)
    for page in doc:
        matches = page.search_for(keyword, quads=False)
        for rect in matches:
            page.add_highlight_annot(rect)
    doc.save(output_path, garbage=4, deflate=True)
    return output_path


def extract_images(pdf_path: str, output_folder: str = "extracted_images") -> list[str]:
    """Extract embedded images to a folder; returns list of saved image paths."""
    os.makedirs(output_folder, exist_ok=True)
    saved = []
    with fitz.open(pdf_path) as doc:
        for i, page in enumerate(doc):
            for idx, img in enumerate(page.get_images(full=True)):
                xref = img[0]
                base = doc.extract_image(xref)
                img_bytes = base["image"]
                ext = base.get("ext", "png")
                out_path = os.path.join(output_folder, f"page_{i+1}_img_{idx+1}.{ext}")
                with open(out_path, "wb") as f:
                    f.write(img_bytes)
                saved.append(out_path)
    return saved


def extract_tables(pdf_path: str):
    """
    Try Camelot first; fall back to pdfplumber.
    Returns list of DataFrames (Camelot) or list-of-rows tables (pdfplumber).
    """
    try:
        tables = camelot.read_pdf(pdf_path, pages="all")
        if tables.n > 0:
            return [t.df for t in tables]
    except Exception:
        pass

    results = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_tables = page.extract_tables()
            results.extend(page_tables or [])
    return results


def ocr_pdf(pdf_path: str, lang: str = "eng") -> str:
    """OCR image-only pages via Tesseract and PyMuPDF rasterization."""
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            pix = page.get_pixmap()
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            custom_config = r'--oem 3 --psm 6'
            text += pytesseract.image_to_string(img, lang=lang, config=custom_config) + "\n"
    return text


def reorder_pages(pdf_path: str, new_order: list[int], output_path: str = "reordered.pdf") -> str:
    """Reorder pages by 0-indexed positions. Saves to output_path."""
    src = fitz.open(pdf_path)
    dst = fitz.open()
    for i in new_order:
        dst.insert_pdf(src, from_page=i, to_page=i)
    dst.save(output_path)
    return output_path


def rotate_pages(pdf_path: str, pages_to_rotate: list[int], angle: int, output_path: str = "rotated.pdf") -> str:
    """Rotate selected 0-indexed pages by angle (e.g., 90/180/270)."""
    doc = fitz.open(pdf_path)
    for p in pages_to_rotate:
        doc[p].set_rotation(angle)
    doc.save(output_path)
    return output_path


def add_watermark(pdf_path: str, watermark_text: str, output_path: str = "watermarked.pdf") -> str:
    """Add semi-transparent diagonal text watermark to all pages."""
    doc = fitz.open(pdf_path)
    for page in doc:
        rect = page.rect
        page.insert_text(
            (rect.width * 0.25, rect.height * 0.5),
            watermark_text,
            fontsize=30,
            rotate=0,
            color=(0.59, 0.59, 0.59)
        )
    doc.save(output_path)
    return output_path


def extract_metadata(pdf_path: str) -> dict:
    """Return PDF metadata dictionary."""
    with fitz.open(pdf_path) as doc:
        return doc.metadata or {}

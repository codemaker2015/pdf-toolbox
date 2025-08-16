import fitz
from pdf2docx import Converter
import pypandoc


def export_to_word(pdf_path: str, output_path: str = "output.docx") -> str:
    """Convert PDF to DOCX (layout-aware)."""
    cv = Converter(pdf_path)
    cv.convert(output_path, start=0, end=None)
    cv.close()
    return output_path


def export_to_text(pdf_path: str, output_path: str = "output.txt") -> str:
    """Export selectable text to TXT."""
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
    return output_path


def export_text_to_markdown(text: str, output_path: str = "output.md") -> str:
    """Export text (already extracted) to Markdown."""
    pypandoc.convert_text(text, "md", format="md", outputfile=output_path, extra_args=["--standalone"])
    return output_path

# 📄 PDF Toolbox  

A versatile PDF processing tool built with Python. This toolbox provides functionality for:  
- Extracting and analyzing text from PDFs  
- Exporting processed content  
- Performing custom PDF operations  

---

## 🚀 Features
- 🔍 **PDF Analysis** – Extract and analyze text from PDF files  
- 📑 **PDF Export** – Save processed or annotated PDF content  
- ⚙️ **PDF Processing Utilities** – Modular functions for handling different tasks  

---

## Demos

### PDF Processing
![pdf processing](demos/pdf_processing_demo.gif)

### Advanced Processing
![advanced processing](demos/advanced_processing.gif)

### Analysis
![analysis](demos/analysis.gif)

### Export
![export](demos/export.gif)

---

## 🛠️ Installation  

Clone the repository and set up the environment:  

```bash
git clone https://github.com/codemaker2015/pdf-toolbox.git
cd pdf-toolbox
```

Install dependencies (using [uv](https://github.com/astral-sh/uv) or pip):  

```bash
uv venv
.venv\Scripts\activate
uv sync
```

---

## ▶️ Usage  

Run the main script:  

```bash
streamlit run main.py
```

---

## 📂 Project Structure  

```
pdf-toolbox/
│── main.py                # Entry point
│── utils/
│   ├── pdf_analysis.py     # Extract and analyze PDF text
│   ├── pdf_export.py       # Export processed PDFs
│   ├── pdf_processing.py   # Core PDF processing utilities
│── .env                    # Environment variables (if needed)
│── pyproject.toml          # Project dependencies and metadata
│── uv.lock                 # Lock file for uv
│── README.md               # Project documentation
```

---

## ⚡ Requirements  
- Python 3.10+  
- Dependencies listed in `pyproject.toml`  

---

## 🤝 Contributing  
Contributions are welcome! Please fork the repo and submit a pull request.  

---

## 📜 License  
This project is licensed under the MIT License.  
import os
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI

from dotenv import load_dotenv
load_dotenv()

# Build FAISS retriever from raw text
def build_retriever_from_text(text: str, chunk_size: int = 800, overlap: int = 100, k: int = 3):
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
    chunks = splitter.split_text(text)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vs = FAISS.from_texts(chunks, embeddings)
    return vs.as_retriever(search_kwargs={"k": k})


# Together.ai LLM (LLaMA) factory
def together_llm(model: str = "meta-llama/Llama-Vision-Free", temperature: float = 0.2, max_tokens: int = 512):
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        openai_api_key=os.getenv("TOGETHER_API_KEY"),
        openai_api_base="https://api.together.xyz/v1"
    )


# Q&A over PDF (RAG)
def rag_qa(text: str, question: str, model: str = "meta-llama/Llama-Vision-Free"):
    retriever = build_retriever_from_text(text)
    llm = together_llm(model=model)
    qa = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
        chain_type="stuff"
    )
    result = qa({"query": question})
    return result["result"], result.get("source_documents", [])


# Summarize PDF text
def summarize_text(text: str, model: str = "meta-llama/Llama-Vision-Free"):
    prompt = (
        "You are a concise technical summarizer. Summarize the following document in 6-10 bullet points, "
        "preserving key facts, numbers, and definitions. Text:\n\n"
        f"{text}"
    )
    llm = together_llm(model=model, temperature=0.2, max_tokens=400)
    output = llm.invoke(prompt)
    return output.content.strip()

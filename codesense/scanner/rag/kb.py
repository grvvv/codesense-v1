import os, logging
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from .config import (
    get_kb_path,
    set_knowledge_base,
    set_qa_chain,
    get_knowledge_base,
    get_qa_chain,
)
from .embeddings import get_embeddings
from .llm import get_llm

def load_knowledge_base(kb_path: str = None):
    if get_knowledge_base() and get_qa_chain():
        return get_knowledge_base(), get_qa_chain()

    if not kb_path:
        kb_path = get_kb_path()
    if not kb_path:
        raise ValueError("KB path not set. Provide it or use set_kb_path() before loading.")
    
    faiss_path = os.path.join(kb_path, "index.faiss")
    pkl_path = os.path.join(kb_path, "index.pkl")

    if not os.path.exists(faiss_path):
        raise FileNotFoundError(f"Missing FAISS index at {faiss_path}")
    if not os.path.exists(pkl_path):
        raise FileNotFoundError(f"Missing pickle at {pkl_path}")


    embeddings = get_embeddings()
    kb = FAISS.load_local(
        folder_path=kb_path,
        embeddings=embeddings,
        allow_dangerous_deserialization=True,
    )


    qa_chain = RetrievalQA.from_chain_type(
        llm=get_llm(),
        chain_type="stuff",
        retriever=kb.as_retriever(search_type="similarity", search_kwargs={"k": 5}),
        return_source_documents=True,
        verbose=False,
    )

    set_knowledge_base(kb)
    set_qa_chain(qa_chain)
    logging.info("Knowledge base and QA chain loaded successfully.")

    return kb, qa_chain
from langchain_community.embeddings import OllamaEmbeddings

def get_embeddings():
    return OllamaEmbeddings(model="codellama:13b")

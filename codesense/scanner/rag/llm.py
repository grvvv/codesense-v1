from langchain_community.llms import Ollama

def get_llm():
    return Ollama(
        model="codellama:13b", 
        temperature=0.1, 
        num_ctx=4096,
        num_predict=1024
    )

from langchain_community.llms import Ollama

llm = Ollama(model="mistral")
response = llm.invoke("What is the capital of France?")
print(response)
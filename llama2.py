from huggingface_hub import InferenceClient

client = InferenceClient(model="meta-llama/Llama-2-7b-chat-hf", token="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")

# Send a request to the model
response = client.text_generation("Hello! How can I assist you today?")
print(response)

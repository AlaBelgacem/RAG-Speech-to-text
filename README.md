
# Speech Analysis + RAG for Technical Support

This project aims to streamline and enhance technical support by providing documented responses from telephone conversations. Using Speech Analysis combined with Retrieval-Augmented Generation (RAG), the framework processes conversation input to generate comprehensive, relevant documentation that supports technical resolutions. Leveraging locally hosted large language models (LLMs) with ollama and langchain, this solution ensures both efficiency and data privacy.


## Features

- Speech Recognition: Transcribes spoken language from telephone conversations.
- Retrieval-Augmented Generation (RAG): Retrieves relevant documents to ground responses with accurate technical information.
- Locally Run LLMs: Using ollama and LLMs with langchain to deliver high-performance language understanding.
- Privacy-Focused: Ensures that sensitive support interactions remain local and secure.


## Tech Stack

**Programming Language:** Python

**Frameworks:** LangChain for LLM-based applications, Ollama CLI for model management

**Libraries:** Speech Recognition, Retrieval-Augmented Generation, Hugging Face Transformers 


## Installation

Python 3.8+ is required for compatibility with the libraries used.

Ollama CLI: Ensure ollama is installed and configured for running local LLMs.

```bash
    # Install ollama
    brew install ollama
```

Clone the repository:

```bash
    git clone https://github.com/AlaBelgacem/RAG-Speech-to-text.git
    cd speech-analysis-RAG-support

    
```

Installing libraries
```bash
    pip install -r requirements.txt
```
## Usage

**Input Speech:** The application captures spoken technical support conversations via the microphone or audio files.

**Retrieve Relevant Documents:** RAG searches a database of technical support documents to identify relevant resources.

**Generate Responses:** The LLM processes the retrieved documents and provides a coherent, documented response.


## License

This project is licensed under the [MIT](https://choosealicense.com/licenses/mit/) license


## Acknowledgements

 - [Langchain](https://python.langchain.com/docs/introduction/)
 - [Hugging Face](https://huggingface.co/)
 - [Ollama](https://ollama.com/)


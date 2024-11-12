import queue
import re
import sys
import time

from google.cloud import speech
import pyaudio
import eel

import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "speech-demo.json"




@eel.expose
def playAssistantSound():
    return "Playing sound"

from langchain_community.embeddings.ollama import OllamaEmbeddings
from langchain_community.embeddings.bedrock import BedrockEmbeddings


def get_embedding_function():
    # embeddings = BedrockEmbeddings(
    #     credentials_profile_name="default", region_name="us-east-1"
    # )
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    return embeddings

import argparse
from langchain.vectorstores.chroma import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_community.llms.ollama import Ollama



CHROMA_PATH = "chroma"

PROMPT_TEMPLATE = """
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""



def query_rag(query_text: str):
    # Prepare the DB.
    embedding_function = get_embedding_function()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    # Search the DB.
    results = db.similarity_search_with_score(query_text, k=5)

    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query_text)
    # print(prompt)

    model = Ollama(model="mistral")
    response_text = model.invoke(prompt)

    sources = [doc.metadata.get("id", None) for doc, _score in results]
    formatted_response = f"Response: {response_text}\nSources: {sources}"
    print(formatted_response)
    return response_text


#***************************************   **************************************/


# Audio recording parameters
STREAMING_LIMIT = 240000  # 4 minutes
SAMPLE_RATE = 16000
CHUNK_SIZE = int(SAMPLE_RATE / 10)  # 100ms

RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"


def get_current_time() -> int:
    """Return Current Time in MS.

    Returns:
        int: Current Time in MS.
    """

    return int(round(time.time() * 1000))


class ResumableMicrophoneStream:
    """Opens a recording stream as a generator yielding the audio chunks."""

    def __init__(
        self: object,
        rate: int,
        chunk_size: int,
    ) -> None:
        """Creates a resumable microphone stream.

        Args:
        self: The class instance.
        rate: The audio file's sampling rate.
        chunk_size: The audio file's chunk size.

        returns: None
        """
        self._rate = rate
        self.chunk_size = chunk_size
        self._num_channels = 1
        self._buff = queue.Queue()
        self.closed = True
        self.start_time = get_current_time()
        self.restart_counter = 0
        self.audio_input = []
        self.last_audio_input = []
        self.result_end_time = 0
        self.is_final_end_time = 0
        self.final_request_end_time = 0
        self.bridging_offset = 0
        self.last_transcript_was_final = False
        self.new_stream = True
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=self._num_channels,
            rate=self._rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            # Run the audio stream asynchronously to fill the buffer object.
            # This is necessary so that the input device's buffer doesn't
            # overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer,
        )

    def __enter__(self: object) -> object:
        """Opens the stream.

        Args:
        self: The class instance.

        returns: None
        """
        self.closed = False
        return self

    def __exit__(
        self: object,
        type: object,
        value: object,
        traceback: object,
    ) -> object:
        """Closes the stream and releases resources.

        Args:
        self: The class instance.
        type: The exception type.
        value: The exception value.
        traceback: The exception traceback.

        returns: None
        """
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(
        self: object,
        in_data: object,
        *args: object,
        **kwargs: object,
    ) -> object:
        """Continuously collect data from the audio stream, into the buffer.

        Args:
        self: The class instance.
        in_data: The audio data as a bytes object.
        args: Additional arguments.
        kwargs: Additional arguments.

        returns: None
        """
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self: object) -> object:
        """Stream Audio from microphone to API and to local buffer

        Args:
            self: The class instance.

        returns:
            The data from the audio stream.
        """
        while not self.closed:
            data = []

            if self.new_stream and self.last_audio_input:
                chunk_time = STREAMING_LIMIT / len(self.last_audio_input)

                if chunk_time != 0:
                    if self.bridging_offset < 0:
                        self.bridging_offset = 0

                    if self.bridging_offset > self.final_request_end_time:
                        self.bridging_offset = self.final_request_end_time

                    chunks_from_ms = round(
                        (self.final_request_end_time - self.bridging_offset)
                        / chunk_time
                    )

                    self.bridging_offset = round(
                        (len(self.last_audio_input) - chunks_from_ms) * chunk_time
                    )

                    for i in range(chunks_from_ms, len(self.last_audio_input)):
                        data.append(self.last_audio_input[i])

                self.new_stream = False

            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self._buff.get()
            self.audio_input.append(chunk)

            if chunk is None:
                return
            data.append(chunk)
            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)

                    if chunk is None:
                        return
                    data.append(chunk)
                    self.audio_input.append(chunk)

                except queue.Empty:
                    break

            yield b"".join(data)


# def listen_print_loop(responses: object, stream: object) -> None:
#     """Iterates through server responses and prints them.

#     The responses passed is a generator that will block until a response
#     is provided by the server.

#     Each response may contain multiple results, and each result may contain
#     multiple alternatives; for details, see https://goo.gl/tjCPAU.  Here we
#     print only the transcription for the top alternative of the top result.

#     In this case, responses are provided for interim results as well. If the
#     response is an interim one, print a line feed at the end of it, to allow
#     the next result to overwrite it, until the response is a final one. For the
#     final one, print a newline to preserve the finalized transcription.

#     Arg:
#         responses: The responses returned from the API.
#         stream: The audio stream to be processed.
#     """
#     for response in responses:
#         if get_current_time() - stream.start_time > STREAMING_LIMIT:
#             stream.start_time = get_current_time()
#             break

#         if not response.results:
#             continue

#         result = response.results[0]

#         if not result.alternatives:
#             continue

#         transcript = result.alternatives[0].transcript
#         eel.DisplayMessage(transcript)
#         result_seconds = 0
#         result_micros = 0

#         if result.result_end_time.seconds:
#             result_seconds = result.result_end_time.seconds

#         if result.result_end_time.microseconds:
#             result_micros = result.result_end_time.microseconds

#         stream.result_end_time = int((result_seconds * 1000) + (result_micros / 1000))

#         corrected_time = (
#             stream.result_end_time
#             - stream.bridging_offset
#             + (STREAMING_LIMIT * stream.restart_counter)
#         )
#         # Display interim results, but with a carriage return at the end of the
#         # line, so subsequent lines will overwrite them.

#         if result.is_final:
#             sys.stdout.write(GREEN)
#             sys.stdout.write("\033[K")
#             sys.stdout.write(str(corrected_time) + ": " + transcript + "\n")

#             stream.is_final_end_time = stream.result_end_time
#             stream.last_transcript_was_final = True

#             # Exit recognition if any of the transcribed phrases could be
#             # one of our keywords.
#             if re.search(r"\b(stop|quitter)\b", transcript, re.I):
#                 sys.stdout.write(YELLOW)
#                 sys.stdout.write("Exiting...\n")
#                 stream.closed = True
#                 break
#         else:
#             sys.stdout.write(RED)
#             sys.stdout.write("\033[K")
#             sys.stdout.write(str(corrected_time) + ": " + transcript + "\r")

#             stream.last_transcript_was_final = False




def listen_print_loop(responses, stream):
    for response in responses:
        if not response.results:
            continue

        result = response.results[0]
        transcript = result.alternatives[0].transcript
        eel.DisplayMessage(transcript)
        
        if result.is_final:
            # Get the final transcript
            transcript = result.alternatives[0].transcript
            print(f"Transcript: {transcript}")
            
            # Trigger RAG with the final transcription as input
            response_text = query_rag(transcript)
            eel.DisplayMessage(response_text)
            print(f"Generated Response: {response_text}")
            #print("\nSources: ", [doc.metadata.get("id", None) for doc, _ in results])  # Optional: print sources


@eel.expose
def main() -> None:
    """start bidirectional streaming from microphone input to speech API"""
    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=SAMPLE_RATE,
        language_code="fr-FR",
        max_alternatives=1,
        model="command_and_search",
    )

    streaming_config = speech.StreamingRecognitionConfig(
        config=config, interim_results=True
        
    )

    mic_manager = ResumableMicrophoneStream(SAMPLE_RATE, CHUNK_SIZE)
    print(mic_manager.chunk_size)
    sys.stdout.write(YELLOW)
    sys.stdout.write('\nListening, say "Quit" or "Exit" to stop.\n\n')
    sys.stdout.write("End (ms)       Transcript Results/Status\n")
    sys.stdout.write("=====================================================\n")

    with mic_manager as stream:
        while not stream.closed:
            stream.audio_input = []
            audio_generator = stream.generator()

            requests = (
                speech.StreamingRecognizeRequest(audio_content=content)
                for content in audio_generator
            )

            responses = client.streaming_recognize(streaming_config, requests)
            listen_print_loop(responses, stream)


#***************************************   **************************************/
import inspect
import sys
from typing import Optional

from ..event import LLMEvent
from ..session import Session
from agentops.helpers import get_ISO_time, check_call_stack_for_agent_id
from .instrumented_provider import InstrumentedProvider
from ..singleton import singleton

original_func = {}


@singleton
class OllamaProvider(InstrumentedProvider):
    original_create = None
    original_create_async = None

    def handle_response(
        self, response, kwargs, init_timestamp, session: Optional[Session] = None
    ) -> dict:
        self.llm_event = LLMEvent(init_timestamp=init_timestamp, params=kwargs)

        def handle_stream_chunk(chunk: dict):
            message = chunk.get("message", {"role": None, "content": ""})

            if chunk.get("done"):
                self.llm_event.completion["content"] += message.get("content")
                self.llm_event.end_timestamp = get_ISO_time()
                self.llm_event.model = f'ollama/{chunk.get("model")}'
                self.llm_event.returns = chunk
                self.llm_event.returns["message"] = self.llm_event.completion
                self.llm_event.prompt = kwargs["messages"]
                self.llm_event.agent_id = check_call_stack_for_agent_id()
                self.client.record(self.llm_event)

            if self.llm_event.completion is None:
                self.llm_event.completion = message
            else:
                self.llm_event.completion["content"] += message.get("content")

        if inspect.isgenerator(response):

            def generator():
                for chunk in response:
                    handle_stream_chunk(chunk)
                    yield chunk

            return generator()

        self.llm_event.end_timestamp = get_ISO_time()

        self.llm_event.model = f'ollama/{response["model"]}'
        self.llm_event.returns = response
        self.llm_event.agent_id = check_call_stack_for_agent_id()
        self.llm_event.prompt = kwargs["messages"]
        self.llm_event.completion = response["message"]

        self._safe_record(session, self.llm_event)
        return response

    def override(self):
        self._override_chat_client()
        self._override_chat()
        self._override_chat_async_client()

    def undo_override(self):
        if original_func is not None and len(original_func.keys()) > 0:
            import ollama

            ollama.chat = original_func["ollama.chat"]
            ollama.Client.chat = original_func["ollama.Client.chat"]
            ollama.AsyncClient.chat = original_func["ollama.AsyncClient.chat"]

    def __init__(self, client):
        super().__init__(client)

    def _override_chat(self):
        import ollama

        original_func["ollama.chat"] = ollama.chat

        def patched_function(*args, **kwargs):
            # Call the original function with its original arguments
            init_timestamp = get_ISO_time()
            result = original_func["ollama.chat"](*args, **kwargs)
            return self.handle_response(
                result, kwargs, init_timestamp, session=kwargs.get("session", None)
            )

        # Override the original method with the patched one
        ollama.chat = patched_function

    def _override_chat_client(self):
        from ollama import Client

        original_func["ollama.Client.chat"] = Client.chat

        def patched_function(*args, **kwargs):
            # Call the original function with its original arguments
            init_timestamp = get_ISO_time()
            result = original_func["ollama.Client.chat"](*args, **kwargs)
            return self.handle_response(result, kwargs, init_timestamp)

        # Override the original method with the patched one
        Client.chat = patched_function

    def _override_chat_async_client(self):
        from ollama import AsyncClient

        original_func["ollama.AsyncClient.chat"] = AsyncClient.chat

        async def patched_function(*args, **kwargs):
            # Call the original function with its original arguments
            init_timestamp = get_ISO_time()
            result = await original_func["ollama.AsyncClient.chat"](*args, **kwargs)
            return self.handle_response(result, kwargs, init_timestamp)

        # Override the original method with the patched one
        AsyncClient.chat = patched_function
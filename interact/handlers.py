import json
import os
from typing import Callable, Iterable, TypeVar

from openai import AsyncOpenAI
from openai._utils import async_transform
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.chat_completion_content_part_param import (
    ChatCompletionContentPartParam,
)
from openai.types.chat.completion_create_params import CompletionCreateParams
from pydantic import BaseModel

from interact import Handler, HandlerChain, Message
from interact.exceptions import HandlerError
from interact.retrieval import Record, VectorDB


class OpenAiLLM(Handler):
    """Handler for generating a response using OpenAI's Language Model."""

    def __init__(
        self,
        role: str | None = None,
        model: str = "gpt-4o-mini",
        structure: type[BaseModel] | None = None,
        **openai_kwgs,
    ) -> None:
        self.role = role if role else "OpenAiLLM"
        self.model = model
        self.client = AsyncOpenAI(**openai_kwgs)
        self.structure = structure

    async def process(self, msg: Message, chain: HandlerChain) -> Message:
        """Generate a response using the message passed to this handler. If OpenAI api
        key is not set in the environment, then the api key can be passed as a variable
        in the HandlerChain.variables dictionary.

        Args:
            msg (Message): user response sent to OpenAI chatGPT.
            chain (HandlerChain): Casccade that this handler is a part of.

        Returns:
            Message: response from OpenAI chatGPT.
        """

        api_key = chain.variables.get("api_key", None)
        if api_key:
            self.client.api_key = api_key

        if msg.image:
            content = [
                {"type": "text", "text": str(msg)},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{msg.image}",
                        "detail": msg.info.get("image_detail", "auto"),
                    },
                },
            ]
        else:
            content = str(msg)

        # Add completion_config to the message if not already present
        completion_config = msg.info.get("completion_config", {})
        if "model" not in completion_config and self.model:
            completion_config["model"] = self.model
        if "response_format" in completion_config:
            structure = completion_config["response_format"]
            if not isinstance(structure, dict):
                self.structure = structure

        res = await self.request(completion_config, content)

        reply = ". ".join([str(ch.message.content) for ch in res.choices])
        if self.structure:
            response = Message(
                primary=reply,
                sender=self.role,
                openai_response=dict(res),
                structure=res.choices[0].message.parsed,  # type: ignore
            )
        else:
            response = Message(
                primary=reply, sender=self.role, openai_response=dict(res)
            )
        return response

    async def request(
        self,
        completion_config: dict,
        content: str | Iterable[ChatCompletionContentPartParam],
    ) -> ChatCompletion:
        if self.structure:
            completion_config["response_format"] = self.structure
            return await self.client.beta.chat.completions.parse(
                **completion_config,
                messages=[
                    {"role": "user", "content": content},
                ],
            )
        else:
            return await self.client.chat.completions.create(
                **completion_config,
                messages=[
                    {"role": "user", "content": content},
                ],
            )


class GeminiLLM(OpenAiLLM):
    def __init__(
        self,
        role: str | None = None,
        model: str = "gemini-1.5-flash",
        structure: type[BaseModel] | None = None,
        **openai_kwgs,
    ) -> None:
        openai_kwgs["base_url"] = (
            "https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        api_key = os.getenv("GOOGLE_API_KEY")
        if "api_key" not in openai_kwgs and api_key:
            openai_kwgs["api_key"] = api_key
        super().__init__(role=role, model=model, structure=structure, **openai_kwgs)


class AssignRole(Handler):
    """Assign a role to the last message sent to this Handler by the current HandlerChain."""

    def __init__(self, role: str) -> None:
        self.role = role

    async def process(self, msg: Message, chain: HandlerChain) -> Message:
        return msg


class RetryHandlerChain(Handler):
    """Retry a HandlerChain until it produces some output before max_attempts.

    Args:
        sub_chain (HandlerChain): HandlerChain to be retried.
        max_attempts (int, optional): Maximum number of times to retry. Defaults to 3.
        role (str, optional): Role of the handler. Defaults to "RetryHandlerChain".
    """  # noqa: E501

    def __init__(
        self,
        sub_chain: HandlerChain,
        max_attempts: int = 3,
    ) -> None:
        self.role = "RetryHandlerChain"
        self.sub_chain = sub_chain
        self.max_attempts = max_attempts

    async def process(self, msg: Message, chain: HandlerChain) -> Message:
        attempts = 0

        while attempts < self.max_attempts:
            try:
                output = await self.sub_chain.run(msg)
                break
            except Exception as e:
                print(e)
                attempts += 1

        if attempts == self.max_attempts:
            raise HandlerError("RetryHandlerChain failed after max attempts")

        return output


class BatchInputOpenAiLLM(Handler):
    def __init__(
        self, role: str | None = None, model: str = "gpt-4o-mini", **openai_kwgs
    ) -> None:
        self.role = role if role else ""
        self.model = model
        # self.client = AsyncOpenAI(**openai_kwgs)

    async def process(self, msg: Message, chain: HandlerChain) -> str:
        """Generate a response using the message passed to this handler. If OpenAI api
        key is not set in the environment, then the api key can be passed as a variable
        in the HandlerChain.variables dictionary.

        Args:
            msg (Message): user response sent to OpenAI chatGPT.
            chain (HandlerChain): Casccade that this handler is a part of.

        Returns:
            Message: response from OpenAI chatGPT.
        """
        if not self.role:
            self.role = msg.sender

        if msg.image:
            content = [
                {"type": "text", "text": str(msg)},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{msg.image}",
                        "detail": msg.info.get("image_detail", "auto"),
                    },
                },
            ]
        else:
            content = str(msg)

        # Add completion_config to the message if not already present
        completion_config: dict = msg.info.get("completion_config", {})
        if "model" not in completion_config and self.model:
            completion_config["model"] = self.model

        messages = [{"role": "user", "content": content}]
        completion_config.update(messages=messages)
        # res = await self.client.chat.completions.create(
        #     **completion_config,
        #     messages=[
        #         {"role": "user", "content": content},
        #     ],
        # )
        data = await async_transform(
            completion_config,
            CompletionCreateParams,
        )

        # reply = ". ".join([str(ch.message.content) for ch in res.choices])
        # return Message(primary=reply, sender=self.role, openai_response=dict(res))

        assert "custom_id" in msg.info, (
            "unique id for the message is required in `info['custom_id']`"
        )
        line = {
            "custom_id": msg.info["custom_id"],
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": data,
        }
        line_s = json.dumps(line)
        return line_s


T = TypeVar("T", bound=Record)


class SimilarityRetriever(Handler):
    """Initialize a Retriever object.

    Args:
        index_db (VectorDB): The index database.
        k (int, optional): The number of records to retrieve. Defaults to 5.
        reranker (Callable[[list[Record]], list[Record]] | None, optional): The reranker function. Defaults to None.
        k_reranked (int, optional): The number of records to keep after reranking. Defaults to 3.
        join_policy (str | Callable[[list[Record]], str | Message], optional): The policy for joining the retrieved records. It can be a string or a callable function. Defaults to "\\\\n\\\\n".

            - If it is a string, the records will be joined using the string as a separator.
            - If it is a callable function, the function should accept a list of records and return a str or a Message.

    """

    role = "retriever"

    def __init__(
        self,
        index_db: VectorDB[T],
        k: int = 5,
        reranker: Callable[[Message, list[T]], list[T]] | None = None,
        k_reranked: int = 3,
        join_policy: str | Callable[[list[T]], str | Message] = "\n\n",
    ) -> None:
        self.index_db = index_db
        self.k = k
        self.join_policy = join_policy
        self.reranker = reranker
        self.k_reranked = k_reranked

    async def process(self, msg: Message, chain: HandlerChain) -> str | Message:
        """
        Process the given message and retrieve similar records.
        Args:
            msg (Message): The message to process.
            chain (HandlerChain): The handler chain.
        Returns:
            str | Message: The joined records as a string or a message.
        Raises:
            ValueError: If the join policy is invalid.
        """
        records = self.index_db.query(msg, k=self.k)
        chain.variables["query"] = msg
        chain.variables["records"] = records
        if self.reranker:
            records = self.reranker(msg, records)
            records = records[: self.k_reranked]
        if callable(self.join_policy):
            return self.join_policy(records)
        elif isinstance(self.join_policy, str):
            return self.join_policy.join(str(record) for record in records)
        else:
            raise ValueError("Invalid join policy.")

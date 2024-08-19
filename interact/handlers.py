import json

from openai import AsyncOpenAI
from openai._utils import async_transform
from openai.types.chat.completion_create_params import CompletionCreateParams

from interact import Handler, HandlerChain, Message
from interact.exceptions import HandlerError


class OpenAiLLM(Handler):
    """Handler for generating a response using OpenAI's Language Model."""

    def __init__(
        self, role: str | None = None, model: str = "gpt-4o-mini", **openai_kwgs
    ) -> None:
        self.role = role if role else ""
        self.model = model
        self.client = AsyncOpenAI(**openai_kwgs)

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
        if not self.role:
            self.role = msg.sender

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

        res = await self.client.chat.completions.create(
            **completion_config,
            messages=[
                {"role": "user", "content": content},
            ],
        )

        reply = ". ".join([str(ch.message.content) for ch in res.choices])
        return Message(primary=reply, sender=self.role, openai_response=dict(res))


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

        assert (
            "custom_id" in msg.info
        ), "unique id for the message is required in `info['custom_id']`"
        line = {
            "custom_id": msg.info["custom_id"],
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": data,
        }
        line_s = json.dumps(line)
        return line_s

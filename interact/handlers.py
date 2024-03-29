from openai import AsyncOpenAI

from interact.base import Cascade, Handler, Message
from interact.exceptions import CascadeError


class OpenAiLLM(Handler):
    """Handler for generating a response using OpenAI's Language Model."""

    def __init__(self, role: str | None = None, model: str = "gpt-3.5-turbo", **openai_kwgs) -> None:
        self.role = role if role else ""
        self.model = model
        self.client = AsyncOpenAI(**openai_kwgs)

    async def process(self, msg: Message, csd: Cascade) -> Message:
        """Generate a response using the message passed to this handler. If OpenAI api
        key is not set in the environment, then the api key can be passed as a variable
        in the Cascade.vars dictionary.

        Args:
            msg (Message): user response sent to OpenAI chatGPT.
            csd (Cascade): Casccade that this handler is a part of.

        Returns:
            Message: response from OpenAI chatGPT.
        """
        if not self.role:
            self.role = msg.sender

        api_key = csd.vars.get("api_key", None)
        if api_key:
            self.client.api_key = api_key
        res = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": str(msg)},
            ],
        )

        reply = ". ".join([str(ch.message.content) for ch in res.choices])
        return Message(primary=reply, sender=self.role, openai_response=dict(res))


class AssignRole(Handler):
    """Assign a role to the last message sent to this Handler by the current Cascade."""

    def __init__(self, role: str) -> None:
        self.role = role

    async def process(self, msg: Message, csd: Cascade) -> Message:
        return msg


class RetryCascade(Handler):
    """Retry a Cascade until it produces some output before max_attempts.

    Args:
        sub_csd (Cascade): Cascade to be retried.
        max_attempts (int, optional): Maximum number of times to retry. Defaults to 3.
        role (str, optional): Role of the handler. Defaults to "RetryCascade".
    """  # noqa: E501
    def __init__(
        self,
        sub_csd: Cascade,
        max_attempts: int = 3,
    ) -> None:
        self.role = "RetryCascade"
        self.sub_csd = sub_csd
        self.max_attempts = max_attempts

    async def process(self, msg: Message, csd: Cascade) -> Message:
        attempts = 0

        output = None
        while (attempts < self.max_attempts):
            try:
                output = await self.sub_csd.start(msg)
                break
            except Exception as e:
                print(e)
                attempts += 1

        if output is None:
            raise CascadeError("RetryCascade failed after max attempts")

        return output.last_msg

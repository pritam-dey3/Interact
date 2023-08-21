from src.base import Handler, Message
from typing import Callable
import openai


class UserInput(Handler):
    def __init__(self, input_func: Callable[..., str] = None):
        self.role = "user"
        if input_func is not None:
            self.input = input_func
        else:
            self.input = input

    def process(self, msg: Message) -> Message:
        user_query = self.input()
        msg = msg.format(user_query=user_query)
        msg["user_query"] = user_query
        return msg


class OpenAiLLM(Handler):
    role = "assistant"

    def process(self, msg: Message) -> Message:
        res = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": msg["primary"]},
            ],
        )

        reply = ". ".join(c["message"]["content"] for c in res["choices"])
        return Message(
            {"primary": reply, "openai_response": dict(res)}
        )


class AssignRole(Handler):
    def __init__(self, role: str) -> None:
        self.role = role

    def process(self, msg: Message) -> Message:
        return msg


class DecideIf(Handler):
    def __init__(
        self, condition: Callable[[Message], bool], *, then: Handler, otherwise: Handler
    ) -> None:
        self.condition = condition
        self.then = then
        self.otherwise = otherwise

    def process(self, msg: Message) -> Message:
        if self.condition(msg):
            handler = self.then
        else:
            handler = self.otherwise

        msg = msg >> handler
        self.role = handler.role

        return msg

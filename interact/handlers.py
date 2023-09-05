import openai

from interact.base import Cascade, Handler, Message


class OpenAiLLM(Handler):
    role = "Assistant"

    def __init__(self, role: str = None) -> None:
        if role is not None:
            self.role = role

    async def process(self, msg: Message, csd: Cascade) -> Message:
        api_key = csd.vars.get("api_key", None)
        res = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            api_key=api_key,
            messages=[
                {"role": "user", "content": str(msg)},
            ],
        )

        reply = ". ".join(c["message"]["content"] for c in res["choices"])
        return Message(primary=reply, sender=self.role, openai_response=dict(res))


class AssignRole(Handler):
    def __init__(self, role: str) -> None:
        self.role = role

    async def process(self, msg: Message, csd: Cascade) -> Message:
        return msg

import asyncio

from interact import Cascade, Message, handler


@handler
async def upper_case(msg: Message, csd: Cascade) -> Message:
    return msg.upper()


@handler
async def remove_punctuation(msg: Message, csd: Cascade) -> str:
    return "".join([char for char in str(msg) if char.isalnum()])


@handler
async def reverse(msg: Message, csd: Cascade) -> Message:
    return msg[::-1]


def main():
    cascade = upper_case >> remove_punctuation >> reverse
    msg = Message("You are awesome!")
    last_msg, history = asyncio.run(cascade.run(msg, return_history=True))

    first_msg = history[0]  # = Message("You are awesome!")

    # `cascade` behaves like a list of messages
    # find a message with a specific role
    msg_rm_punc = [handler for handler in cascade if handler.role == "remove_punctuation"][0]

    # get last handler
    last_handler = cascade.pop()
    assert last_handler.role == "reverse"

    print(first_msg, last_msg, msg_rm_punc, sep="\n")

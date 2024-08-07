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
    res = asyncio.run(cascade.run(msg))

    # `res` behave like a list
    first_msg = res[0]  # = Message("You are awesome!")
    last_msg = res.pop()  # similar to res.last_msg
    # find a message with a specific role
    msg_rm_punc = [msg for msg in res if msg.role == "remove_punctuation"][0]

    print(first_msg, last_msg, msg_rm_punc, sep="\n")

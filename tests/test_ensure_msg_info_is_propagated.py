import asyncio

from interact import HandlerChain, Message, handler


@handler
async def upper_case(msg: Message, chain: HandlerChain) -> Message:
    return msg.upper()


@handler
async def remove_punctuation(msg: Message, chain: HandlerChain) -> Message:
    _msg = "".join([char for char in str(msg) if char.isalnum()])
    next_msg = Message(_msg)
    next_msg.info = {"info-1": "info-1", "info-2": "info-2"}
    return next_msg


@handler
async def reverse(msg: Message, chain: HandlerChain) -> Message:
    assert msg.info == {"info-1": "info-1", "info-2": "info-2"}, f"Message info not propagated, {msg.info}"
    return msg[::-1]


def test_ensure_msg_info_is_propagated():
    chain = upper_case >> remove_punctuation >> reverse
    msg = Message("You are awesome!")
    last_msg, history = asyncio.run(chain.run(msg, return_history=True))
    print(last_msg)


if __name__ == "__main__":
    test_ensure_msg_info_is_propagated()
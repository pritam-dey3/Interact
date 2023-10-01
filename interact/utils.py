from __future__ import annotations

import string
from typing import TYPE_CHECKING
from warnings import warn

if TYPE_CHECKING:
    from explorations.dumps.base import Message, Handler

string_formatter = string.Formatter()


def get_format_args(s: str):
    return [tup[1] for tup in string_formatter.parse(s) if tup[1] is not None]


def check_msg_is_formatted(msg: Message, handler: Handler):
    """Check if the message is formatted. If not, then warn the user.

    Args:
        msg (Message): message to check
        handler (Handler): handler that the message was passed to
    """
    args = get_format_args(msg["primary"])
    if len(args) > 0:
        warn(
            f"{msg=} has unformatted `primary` message but was passed to"
            f" {type(handler)=}"
        )


def find_last(key: str, history: list[Message]):
    """Find the last message in the history that has the given key in Message.info
    dictionary..

    Args:
        key (str): key to search for
        history (list[Message]): history of the current Cascade

    Raises:
        RuntimeError: if the key is not found in the history

    Returns:
        Any: value of the key in the last message in the history that has the key
    """
    value = None
    for msg in reversed(history):
        if key in msg:
            value = msg[key]
            break
    else:
        raise RuntimeError(f"key {key} could not be found in history.")

    return value

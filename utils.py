from __future__ import annotations

import string
from typing import TYPE_CHECKING
from warnings import warn

if TYPE_CHECKING:
    from src.base import Message, Handler

string_formatter = string.Formatter()


def get_format_args(s: str):
    return [tup[1] for tup in string_formatter.parse(s) if tup[1] is not None]


def check_msg_is_formatted(msg: Message, handler: Handler):
    args = get_format_args(msg["primary"])
    if len(args) > 0:
        warn(
            f"{msg=} has unformatted `primary` message but was passed to"
            f" {type(handler)=}"
        )

from __future__ import annotations

import base64
import string
from io import BytesIO
from typing import TYPE_CHECKING
from warnings import warn

import numpy as np
from PIL import Image

if TYPE_CHECKING:
    from interact import Handler, Message, History

string_formatter = string.Formatter()


def get_format_args(s: str):
    return [tup[1] for tup in string_formatter.parse(s) if tup[1] is not None]


def check_msg_is_formatted(msg: Message, handler: Handler):
    """Check if the message is formatted. If not, then warn the user.

    Args:
        msg (Message): message to check
        handler (Handler): handler that the message was passed to
    """
    args = get_format_args(msg.primary)
    if len(args) > 0:
        warn(
            f"{msg=} has unformatted `primary` message but was passed to"
            f" {type(handler)=}"
        )


def find_last(key: str, history: History):
    """Find the last message in the history that has the given key in Message.info
    dictionary..

    Args:
        key (str): key to search for
        history (History): history of the current HandlerChain

    Raises:
        RuntimeError: if the key is not found in the history

    Returns:
        Any: value of the key in the last message in the history that has the key
    """
    value = None
    for msg in reversed(history):
        if key in msg:
            value = msg.info[key]
            break
    else:
        raise RuntimeError(f"key {key} could not be found in history.")

    return value


def image_to_base64(image: Image.Image | np.ndarray) -> str:
    """
    Convert an image to a base64 encoded string.

    Parameters:
    image (PIL.Image.Image, np.ndarray): The input image.

    Returns:
    str: The base64 encoded string of the image.
    """
    # Convert NumPy ndarray to PIL Image if necessary
    if isinstance(image, np.ndarray):
        image = Image.fromarray(image)
    if not isinstance(image, Image.Image):
        raise ValueError(
            "Input image must be a PIL Image or a NumPy ndarray, received: ",
            type(image),
        )

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    byte_data = buffer.getvalue()
    base64_str = base64.b64encode(byte_data).decode("utf-8")

    return base64_str

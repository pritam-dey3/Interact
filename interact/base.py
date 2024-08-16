from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections import UserString
from collections.abc import Sequence
from copy import copy
from typing import Any, Callable, Coroutine, Literal, overload

from interact.exceptions import HandlerError, UnsupportedCascade
from interact.types import Variables
from interact.utils import image_to_base64


class Message(UserString):
    """Message object that is passed between handlers in a Cascade. Each message object
    has

    Args:
        primary (str): the main content of the message
        sender (str): the role of the sender of the message
        kwargs (dict): additional information about the message
    """

    def __init__(self, primary: str, sender: str = "Unknown", **kwargs) -> None:
        self.primary = primary
        self.sender = sender
        if "image" in kwargs:
            self.image = image_to_base64(kwargs["image"])
        else:
            self.image = None

        self.info: dict[str, Any] = kwargs
        super().__init__(primary)

    def __add__(self, other: object) -> Message:
        if not (isinstance(other, str) or isinstance(other, UserString)):
            raise TypeError(
                f"Can only concatenate str or UserString (Message) to Message. Got {type(other)}"
            )
        return super().__add__(other)

    def __radd__(self, other: object) -> Message:
        if not (isinstance(other, str) or isinstance(other, UserString)):
            raise TypeError(
                f"Can only concatenate str or UserString (Message) to Message. Got {type(other)}"
            )
        return super().__radd__(other)

    def __repr__(self):
        return f"Message({self.primary}, sender='{self.sender}', info={self.info})"

    def __str__(self) -> str:
        return f"{self.sender}: {self.primary}"


class Handler(ABC):
    """Base class for all handlers. Each handler has a role and a process method.
    The process method takes a Message object and a Cascade object as input and returns
    a transformed Message object.

    Raises:
        NotImplementedError: if the process method is not implemented
        HandlerError: if the output of process is not a Message or str
        UnsupportedCascade: if the next object in the sequence is not a Handler or
        Cascade.
    """

    role: str

    @abstractmethod
    async def process(self, msg: Message, csd: Cascade) -> str | Message:
        """Process a message and return a new transformed message.

        Args:
            msg (Message): Message to be processed / transformed.
            csd (Cascade): current Cascade object that is executing this handler.

        Raises:
            NotImplementedError: if the process method is not implemented

        Returns:
            str | Message: transformed message
        """
        raise NotImplementedError

    async def _process(self, msg: Message, csd: Cascade) -> Message:
        """Get the next message in the cascade. This method is called by the Cascade
        that is executing this handler. The output of process is converted to a Message,
        and the sender is set to the role of this handler.

        Args:
            msg (Message): Message to be processed / transformed.
            csd (Cascade): current Cascade object that is executing this handler.

        Raises:
            HandlerError: if the output of process is not a Message or str

        Returns:
            Message: transformed message
        """
        _next_msg = await self.process(msg, csd)
        if isinstance(_next_msg, Message):
            next_msg = copy(_next_msg)
            next_msg.sender = self.role
        elif isinstance(_next_msg, str):
            next_msg = Message(_next_msg, sender=self.role)
        else:
            raise HandlerError(
                f"Output of process should be either str or Message. But got {msg} in"
                f" {self.__class__}"
            )
        logging.debug(repr(next_msg))
        return next_msg

    def __rshift__(self, other) -> Cascade:
        """Create a Cascade object with this handler and the other object. If the other
        object is a Cascade, then this handler is appended to the Cascade.

        Args:
            other: next Handler or Cascade object in the sequence

        Raises:
            UnsupportedCascade: if the other object is not a Handler or Cascade

        Returns:
            Cascade: Cascade object
        """
        if isinstance(other, Handler):
            return Cascade(self, other)
        elif isinstance(other, Cascade):
            return other.__rrshift__(self)
        else:
            raise UnsupportedCascade(self, other)


class History(Sequence[Message]):
    """History is a sequence of messages that were processed by a Cascade. It is a
    read-only list of messages.

    Args:
        messages (list[Message]): list of messages in the history
    """

    def __init__(self, *messages: Message) -> None:
        self.messages = tuple(messages)

    def __getitem__(self, index: int) -> Message:
        return self.messages[index]

    def __len__(self) -> int:
        return len(self.messages)

    def __repr__(self) -> str:
        return f"History({self.messages})"


class Cascade(Sequence[Handler]):
    """Cascade is a sequence of handlers that are executed in order.

    Parameters:
        handlers (list[Handler]): list of handlers in the cascade
        vars (dict): variables that are shared between handlers
        last_msg (Message): last message that was processed by the last handler in the cascade
        history (list[Message]): list of all messages that were processed
        step (int): step counter during execution
    """  # noqa: E501

    def __init__(self, *handlers: Handler, variables: Variables = {}) -> None:
        self.handlers = handlers
        self.variables = variables
        self.history: History = History()
        self.step: int | None = None

    @overload
    async def run(
        self,
        msg: str | Message,
        vars: dict[str, Any] = {},
        return_history: Literal[False] = ...,
    ) -> Message: ...
    @overload
    async def run(
        self,
        msg: str | Message,
        vars: dict[str, Any] = {},
        return_history: Literal[True] = ...,
    ) -> tuple[Message, History]: ...

    async def run(
        self,
        msg: str|Message="",
        vars: dict[str, Any]={},
        return_history: bool=False,
    ):
        """Start execution of the cascade. The first message is either a string
        (converted to Message with sender "Cascade-Start) or a Message object.
        Additional variables can be passed to the cascade with the vars argument.

        Handlers are executed in order. Each handler receives the last message as input
        and returns a new message.

        Args:
            msg (str | Message, optional): Starting message for the Cascade. Defaults to "".
            vars (dict[str, Any], optional): Additional variables those will be shared by all handlers. Handlers can update the variables during their processing stage. Defaults to {}.
            return_history (bool, optional): If True, the history of all messages is returned. Defaults to False.

        Returns:
            Self: Cascade object
        """  # noqa: E501
        self.variables.update(vars)
        if not isinstance(msg, Message):
            msg = Message(msg, sender="Input")
        self.last_msg = msg
        self.history = History(*self.history, msg)

        for self.step, handler in enumerate(self):
            msg = await handler._process(self.last_msg, self)
            self.history = History(*self.history, msg)
            self.last_msg = msg

        if return_history:
            return self.last_msg, self.history
        else:
            return self.last_msg

    def __rshift__(self, other) -> Cascade:
        """Append a handler to the cascade. If the other object is a Cascade, then
        the handlers and variables of the other cascade are appended to this cascade.

        Args:
            other: Handler or Cascade object

        Raises:
            UnsupportedCascade: if the other object is not a Handler or Cascade

        Returns:
            Self: Cascade object
        """
        if isinstance(other, Handler):
            new_csd = Cascade(*self, other)
        elif isinstance(other, Cascade):
            self.variables.update(other.variables)
            new_csd = Cascade(*self, *other)
        else:
            raise UnsupportedCascade(self, other)
        return new_csd

    def __rrshift__(self, other) -> Cascade:
        """Prepend a handler to the cascade.

        Args:
            other: Handler object

        Raises:
            UnsupportedCascade: if the other object is not a Handler

        Returns:
            Self: Cascade object
        """
        if isinstance(other, Handler):
            return Cascade(other, *self)
        else:
            raise UnsupportedCascade(other, self)

    def __getitem__(self, index: int) -> Handler:
        return self.handlers[index]

    def __len__(self) -> int:
        return len(self.handlers)

    __call__ = run


def handler(
    func: Callable[[Message, Cascade], Coroutine[None, None, str | Message]],
) -> Handler:
    """Decorator to convert any async function to a Handler object.

    Args:
        func: async function that takes a Message and Cascade object as input and
        returns a str or Message object.

    Returns:
        type[Handler]: Handler object
    """

    class HandlerWrapper(Handler):
        role = func.__name__

        async def process(self, msg: Message, csd: Cascade) -> str | Message:
            return await func(msg, csd)

    return HandlerWrapper()

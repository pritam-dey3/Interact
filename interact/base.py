from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections import UserString
from collections.abc import Sequence
from copy import copy
from typing import Any, Callable, Coroutine, Literal, overload

from interact.exceptions import HandlerError, UnsupportedHandlerChain
from interact.types import Variables
from interact.utils import image_to_base64


class Message(UserString):
    """Message object that is passed between handlers in a HandlerChain. Each message object
    has a primary content, a sender role, and additional information.

    Args:
        primary (str): The main content of the message.
        sender (str, optional): The role of the sender of the message. Defaults to "Unknown".
        kwargs (dict): Additional information about the message.
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

    # def __repr__(self):
    #     return f"Message({self.primary}, sender='{self.sender}', info={self.info})"

    def __str__(self) -> str:
        return self.primary

    def __copy__(self) -> Message:
        return Message(self.primary, sender=self.sender, **self.info)


class Handler(ABC):
    """Base class for all handlers. Each handler has a role and a process method.
    The process method takes a Message object and a HandlerChain object as input and returns
    a transformed Message object.

    Raises:
        NotImplementedError: If the process method is not implemented.
        HandlerError: If the output of process is not a Message or str.
        UnsupportedHandlerChain: If the next object in the sequence is not a Handler or HandlerChain.
    """

    role: str

    @abstractmethod
    async def process(self, msg: Message, chain: HandlerChain) -> str | Message:
        """Process a message and return a new transformed message.

        Args:
            msg (Message): Message to be processed / transformed.
            chain (HandlerChain): Current HandlerChain object that is executing this handler.

        Raises:
            NotImplementedError: If the process method is not implemented.

        Returns:
            str | Message: Transformed message.
        """
        raise NotImplementedError

    async def _process(self, msg: Message, chain: HandlerChain) -> Message:
        """Get the next message in the HandlerChain. This method is called by the HandlerChain
        that is executing this handler. The output of process is converted to a Message,
        and the sender is set to the role of this handler.

        Args:
            msg (Message): Message to be processed / transformed.
            chain (HandlerChain): Current HandlerChain object that is executing this handler.

        Raises:
            HandlerError: If the output of process is not a Message or str.

        Returns:
            Message: Transformed message.
        """
        next_msg = await self.process(msg, chain)
        if isinstance(next_msg, Message):
            next_msg = copy(next_msg)
            next_msg.sender = self.role
        elif isinstance(next_msg, str):
            next_msg = Message(next_msg, sender=self.role)
        else:
            raise HandlerError(
                f"Output of process should be either str or Message. But got {msg} in {self.__class__}"
            )
        logging.debug(repr(next_msg))
        return next_msg

    def __rshift__(self, other) -> HandlerChain:
        """Create a HandlerChain object with this handler and the other object. If the other
        object is a HandlerChain, then this handler is appended to the HandlerChain.

        Args:
            other: Next Handler or HandlerChain object in the sequence.

        Raises:
            UnsupportedHandlerChain: If the other object is not a Handler or HandlerChain.

        Returns:
            HandlerChain: HandlerChain object.
        """
        if isinstance(other, Handler):
            return HandlerChain(self, other)
        elif isinstance(other, HandlerChain):
            return other.__rrshift__(self)
        else:
            raise UnsupportedHandlerChain(self, other)


class History(Sequence[Message]):
    """History is a sequence of messages that were processed by a HandlerChain.
    Attributes:
        messages (tuple[Message]): Tuple of messages in the history.
    """

    def __init__(self, *messages: Message) -> None:
        self.messages = tuple(messages)

    @overload
    def __getitem__(self, index: slice) -> History: ...
    @overload
    def __getitem__(self, index: int) -> Message: ...
    def __getitem__(self, index):
        if isinstance(index, slice):
            return History(*self.messages[index])
        return self.messages[index]

    def __len__(self) -> int:
        return len(self.messages)

    def __repr__(self) -> str:
        return f"History({self.messages})"


class HandlerChain(Sequence[Handler]):
    """HandlerChain is a sequence of handlers that are executed in order.

    Args:
        handlers (tuple[Handler, ...]): Array of handlers in the chain.
        variables (dict): Variables that are shared between handlers.

    Attributes:
        handlers (tuple[Handler, ...]): Array of handlers in the chain.
        variables (dict): Variables that are shared between handlers.
        last_msg (Message): Last message that was processed by the last handler in the chain.
        history (History): History of all messages that were processed.
        step (int): Step counter during execution.
    """

    def __init__(self, *handlers: Handler, variables: Variables = {}) -> None:
        self.handlers = handlers
        self.variables = variables
        self.history: History = History()
        self.step: int | None = None

    @overload
    async def run(
        self,
        msg: str | Message,
        variables: dict[str, Any] = {},
        return_history: Literal[False] = ...,
    ) -> Message: ...
    @overload
    async def run(
        self,
        msg: str | Message,
        variables: dict[str, Any] = {},
        return_history: Literal[True] = ...,
    ) -> tuple[Message, History]: ...

    async def run(
        self,
        msg: str | Message = "",
        variables: dict[str, Any] = {},
        return_history: bool = False,
    ):
        """Start execution of the HandlerChain.

        The first message is either a string (converted to Message with sender "input") or a Message object.
        Additional variables can be passed to the HandlerChain with the variables argument.

        Handlers are executed in order. Each handler receives the last message as input
        and returns a new transformed message.

        Args:
            msg (str | Message, optional): Starting message for the HandlerChain. Defaults to "".
            variables (dict[str, Any], optional): Additional variables that will be shared by all handlers. Handlers can update the variables during their processing stage. Defaults to {}.
            return_history (bool, optional): If True, the history of all messages is returned. Defaults to False.

        Returns:
            Message | tuple[Message, History]: Transformed message or tuple of transformed message and history.
        """
        self.variables.update(variables)
        if not isinstance(msg, Message):
            msg = Message(msg, sender="input")
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

    def __rshift__(self, other) -> HandlerChain:
        """Append a handler to the HandlerChain. If the other object is a HandlerChain, then
        the handlers and variables of the other HandlerChain are appended to this HandlerChain.

        Args:
            other: Handler or HandlerChain object.

        Raises:
            UnsupportedHandlerChain: If the other object is not a Handler or HandlerChain.

        Returns:
            Self: HandlerChain object.
        """
        if isinstance(other, Handler):
            new_chain = HandlerChain(*self, other)
        elif isinstance(other, HandlerChain):
            self.variables.update(other.variables)
            new_chain = HandlerChain(*self, *other)
        else:
            raise UnsupportedHandlerChain(self, other)
        return new_chain

    def __rrshift__(self, other) -> HandlerChain:
        """Prepend a handler to the HandlerChain.

        Args:
            other: Handler object.

        Raises:
            UnsupportedHandlerChain: If the other object is not a Handler.

        Returns:
            Self: HandlerChain object.
        """
        if isinstance(other, Handler):
            return HandlerChain(other, *self)
        else:
            raise UnsupportedHandlerChain(other, self)

    def __getitem__(self, index: int) -> Handler:
        return self.handlers[index]

    def __len__(self) -> int:
        return len(self.handlers)

    __call__ = run


def handler(
    func: Callable[[Message, HandlerChain], Coroutine[None, None, str | Message]],
) -> Handler:
    """Decorator to convert any async function to a Handler object.

    Args:
        func: Async function that takes a Message and HandlerChain object as input and
        returns a str or Message object.

    Returns:
        type[Handler]: Handler object.
    """

    class HandlerWrapper(Handler):
        role = func.__name__

        async def process(self, msg: Message, chain: HandlerChain) -> str | Message:
            return await func(msg, chain)

    return HandlerWrapper()

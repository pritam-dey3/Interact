from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, MutableMapping, Sequence
from typing import Any, Callable, Self
from interact.utils import check_msg_is_formatted, get_format_args
from typing import overload


MessageInfo = MutableMapping[str, Any]


class Message(MutableMapping):
    """
    Abstract base class for the medium of communication between entities.
    """

    def __init__(
        self,
        info: str | Mapping[str, Any],
        sender: str = None,
        history: list[Message] = None,
    ) -> None:
        if isinstance(info, str):
            self._info = {"primary": info}
        elif isinstance(info, Mapping):
            if "primary" not in info.keys():
                raise KeyError(
                    f"Message info must contain `primary` key. Recieved {info=}"
                )
            self._info = dict(info)
        else:
            raise ValueError(
                "Message must be initiated with either a string or a Mapping."
                f" Recieved {info=}"
            )

        self.sender = sender
        self.history = history

    def __getitem__(self, key):
        return self._info[key]

    def __setitem__(self, key: str, val: Any):
        self._info[key] = val

    def __delitem__(self, key):
        del self._info[key]

    def __iter__(self):
        return iter(self._info)

    def __len__(self) -> int:
        return len(self._info)

    def format(self, **kwargs) -> Self:
        if ("call" in kwargs) and isinstance(kwargs["call"], Callable):  # type: ignore
            self._info = kwargs["call"](self._info)
        else:
            primary = self._info["primary"]
            format_args = get_format_args(primary)
            assert all([key in format_args for key in kwargs]), (
                f"{self=} requires the following formatting"
                f" arguments\n{format_args}\nbut received {kwargs}"
            )
            self._info["primary"] = primary.format(**kwargs)
        return self

    def __repr__(self):
        return f"{type(self)}(info={self._info}, sender={self.sender})"


class Handler(ABC):
    """
    Abstract base class for any system that can interact and share messages.
    """

    role: str

    @abstractmethod
    def process(self, msg: Message) -> Message:
        """
        Send a message to the entity.

        Args:
            message (Message): The message to be sent.
        """
        pass

    @overload
    def __rrshift__(self, msg: Message) -> Message:
        ...

    @overload
    def __rrshift__(self, handler: Handler) -> HandlerSequence:
        ...

    def __rrshift__(self, entity):
        if isinstance(entity, Message):
            if not isinstance(self, HandlerSequence):
                check_msg_is_formatted(entity, handler=self)

            history = entity.history or []

            msg = self.process(entity)
            msg.sender = self.role

            if not isinstance(self, HandlerSequence):
                history = history + [msg]
                msg.history = history
            return msg

        elif isinstance(entity, Handler):
            if isinstance(entity, HandlerSequence):
                entity.add_handler(self)
                return entity
            else:
                handler_seq = HandlerSequence()
                handler_seq.add_handler(entity)
                handler_seq.add_handler(self)
                return handler_seq

        raise RuntimeError(
            f"Expected entity of type `Handler` but recieved {entity} (type:"
            f" {type(entity)})"
        )


class HandlerSequence(Handler):
    def __init__(self) -> None:
        self._handlers: list[Handler] = []
        self.role = None

    def add_handler(self, handler: Handler) -> None:
        if isinstance(handler, Handler):
            self._handlers.append(handler)
        else:
            raise ValueError("HandlerSequence can only contain instances of Handler")

    def process(self, msg: Message) -> Message:
        if len(self._handlers) == 0:
            raise RuntimeError(f"Empty handlers found in `HandlerSequence` {self}")
        for handler in self._handlers:
            msg = msg >> handler

        if not self.role:
            # assign the same role as the last handler
            self.role = self._handlers[-1].role
        return msg


class History(Sequence):
    """Stores all the history between different Entities"""

    def __init__(self) -> None:
        self.messages: list[Message]

    def __getitem__(self, index):
        return self.messages[index]

    def append(self, msg: Message):
        self.messages.append(msg)

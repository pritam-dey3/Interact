from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from copy import copy
from typing import Any, Self

from interact.exceptions import CascadeError, HandlerError, UnsupportedCascade
from interact.types import CascadeVars


class Message:
    def __init__(self, primary: str, sender: str, **kwargs) -> None:
        self.primary = primary
        self.sender = sender
        self.info: dict[str, Any] = kwargs

    def __getitem__(self, key):
        return self.info[key]

    def __repr__(self):
        return f"{self.sender}: {self.primary}"

    def __str__(self) -> str:
        return self.primary


class Cascade:
    def __init__(self, handlers: list[Handler], vars: CascadeVars = {}) -> None:
        self.handlers = handlers
        self.vars = vars
        self.last_msg: Message = None
        self.history: list[Message] = []
        self.step: int = None  # step counter during execution

    async def start(self, msg: str | Message = "", vars: dict[str, Any] = {}) -> Self:
        self.vars.update(vars)
        if not isinstance(msg, Message):
            msg = Message(msg, sender="Cascade-Start")
        self.last_msg = msg
        self.history.append(self.last_msg)

        for self.step, handler in enumerate(self.handlers):
            msg = await handler.get_next_message(self.last_msg, self)
            self.history.append(msg)
            self.last_msg = msg
        return self

    def find_recent(self, role) -> Message:
        target: Message = None
        for msg in reversed(self.history):
            if msg.sender == role:
                target = msg
                break
        else:
            raise CascadeError(
                f"No such role {role} found prior to {self.handlers[self.step]} in"
                " Cascade handlers"
            )

        return target

    def __rshift__(self, other):
        if isinstance(other, Handler):
            self.handlers.append(other)
        elif isinstance(other, Cascade):
            self.vars.update(other.vars)
            self.handlers.extend(other.handlers)
        else:
            raise UnsupportedCascade(self, other)
        return self

    def __rrshift__(self, other) -> Cascade:
        if isinstance(other, Handler):
            self.handlers.insert(0, other)
        else:
            raise UnsupportedCascade(other, self)
        return self


class Handler(ABC):
    role: str

    @abstractmethod
    async def process(self, msg: Message, csd: Cascade) -> str | Message:
        raise NotImplementedError

    async def get_next_message(self, msg: Message, csd: Cascade) -> Message:
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
        if isinstance(other, Handler):
            return Cascade([self, other])
        elif isinstance(other, Cascade):
            return other.__rrshift__(self)
        else:
            raise UnsupportedCascade(self, other)

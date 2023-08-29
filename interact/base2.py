from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from exceptions import UnsupportedCascade


CascadeVars = dict[str, Any]


class Cascade:
    def __init__(self, handlers: list[Handler], vars: CascadeVars = {}) -> None:
        self.handlers = handlers
        self.vars = vars
        self.last_msg: str = None

    async def start(self, msg: str):
        self.last_msg = msg
        for handler in self.handlers:
            self.last_msg = await handler.process(self.last_msg, self)

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
    async def process(self, msg: str, csd: Cascade) -> str:
        raise NotImplementedError

    def __rshift__(self, other) -> Cascade:
        if isinstance(other, Handler):
            return Cascade([self, other])
        elif isinstance(other, Cascade):
            return other.__rrshift__(self)
        else:
            raise UnsupportedCascade(self, other)

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod

from interact.base import Cascade, Message
from interact.exceptions import ChatInterruptionError
from interact.types import Variables


class ChatManager(ABC):
    """Chat is a sequence of messages between two agents.

    Parameters:
        agents (list[Agent]): List of agents in the chat
        vars (dict): v=Variables that are shared between agents
        chat (list[Message]): List of all messages that were processed
        chat_interrupted (asyncio.Event): Event that is set to True when the chat is interrupted
    """  # noqa: E501

    agents: dict[str, BaseAgent]
    vars: Variables = {}
    conversation_hist: list[Message] = []
    is_interrupted = asyncio.Event()

    def __init_subclass__(cls) -> None:
        """Monkey patch key methods of a subclass.
        """
        super().__init_subclass__()
        cls._user_run = cls.run  # type: ignore
        cls.run = cls._run

    @abstractmethod
    async def run(self, msg: Message, vars: Variables = {}) -> list[Message]:
        """Run the chat and manage the conversation between agents.

        Raises:
            ChatInterruptionError: If the chat is interrupted by user.

        Returns:
            list[Message]: List of all messages that were processed
        """
        raise NotImplementedError

    async def _run(self, msg: Message, vars: Variables = {}) -> list[Message]:
        """Start the conversation with an initial message. This is a wrapper around `run` method
        Additionally
            * sets the chat_interrupted event to false
            * adds the initial message to the chat history

        Raises:
            ChatInterruptionError: If the chat is interrupted by user.

        Returns:
            list[Message]: List of all messages that were processed
        """  # noqa: E501
        self.is_interrupted.clear()
        self.conversation_hist.append(msg)
        return await self._user_run(msg, vars)  # type: ignore

    def last_msg(self, by: BaseAgent | None = None) -> Message | None:
        """Get the last message in the chat.

        Args:
            by (Agent): The agent that sent the message. If by is None, the last message is returned.

        Returns:
            Last message sent by the agent, or None if no message was sent by the agent
        """  # noqa: E501
        if by is None:
            return self.conversation_hist[-1]
        else:
            for msg in reversed(self.conversation_hist):
                if msg.sender == by.name:
                    return msg
            return None


class BaseAgent(ABC):
    name: str = "Agent"

    def __init_subclass__(cls, *args, **kwargs) -> None:
        """Monkey patch key methods of a subclass."""
        super().__init_subclass__(*args, **kwargs)

        # this is causing a recursion error
        cls._user_respond_to = cls.respond_to  # type: ignore
        cls.respond_to = cls._respond_to

    @abstractmethod
    async def respond_to(self, prompt: Message, chat: ChatManager) -> Message:
        """Respond or send a message to the chat.

        Args:
            prompt (Message): Prompt to respond to
            chat (ChatManager): Chat this agent is participating in

        Raises:
            ChatInterruptionError: If the chat is interrupted by user.

        Returns:
            Message: Response to the prompt
        """
        raise NotImplementedError

    async def _respond_to(self, prompt: Message, chat: ChatManager) -> Message:
        """Private respond method that patches `respond`.
        Additionally
            * checks if the chat is interrupted
            * adds the response to the chat history

        Raises:
            ChatInterruptionError: If the chat is interrupted by user.

        Args:
            prompt (Message): Prompt to respond to
            chat (ChatManager): Chat this agent is participating in

        Returns:
            Message: Response to the prompt
        """  # noqa: E501
        if chat.is_interrupted.is_set():
            raise ChatInterruptionError("Chat was interrupted.")
        msg = await self._user_respond_to(prompt, chat)  # type: ignore
        chat.conversation_hist.append(msg)
        return msg


class CascadeAgent(BaseAgent):
    """CascadeAgent is an agent that responds to prompts using a Cascade.

    Parameters:
        cascade (Cascade): Cascade used to respond to prompts
        name (str): Name of the agent
    """

    def __init__(self, cascade: Cascade, name: str = "CascadeAgent") -> None:
        self.cascade = cascade
        self.name = name

    async def respond_to(self, prompt: Message, chat: ChatManager) -> Message:
        """Respond to a prompt using the cascade.

        Args:
            prompt (Message): Prompt to respond to
            chat (ChatManager): Chat this agent is participating in

        Returns:
            Message: Response to the prompt
        """
        csd = await self.cascade.start(prompt, chat.vars)
        return csd.last_msg

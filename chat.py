from __future__ import annotations
from bisect import bisect_right
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from game import Color
from messages import JsonifyableBase


@dataclass
class ChatMessage(JsonifyableBase):
    """
    A container class for chat messages

    Attributes:

        timestamp: float - the server time, in seconds, when the message was
        received

        color: Color - the color of the player who created the message

        message: str - the message contents

        id: str - the message ID. NB: auto generated. only set from source
    """

    timestamp: float
    color: Color
    message: str
    id: Optional[str] = None

    def jsonifyable(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "color": self.color.name,
            "message": self.message,
            "id": self.id,
        }

    def __repr__(self) -> str:
        return (
            f"ChatMessage("
            f"timestamp={self.timestamp}"
            f", color={self.color}"
            f", message={self.message}"
            f", id={self.id})"
        )


@dataclass
class ChatThread(JsonifyableBase):
    """
    An ordered thread of chat messages

    Attributes:

        thread: List[ChatMessage] = [] - the complete thread of messages
    """

    thread: List[ChatMessage] = None

    def __post_init__(self):
        if self.thread is None:
            self.thread = []

    def jsonifyable(self) -> List[Dict]:
        return [msg.jsonifyable() for msg in self.thread]

    def __repr__(self) -> str:
        return repr(self.thread)

    def get_after(self, after_id: int = 0) -> ChatThread:
        """
        Return a thread consisting of all messages with an id strictly greater
        than `after_id`. As ids begin at 1, a value of 0 for `after_id`
        guarantees that the full thread is returned and is thus equivalent to
        the current object
        """

        return ChatThread(self.thread[bisect_right(self.thread, after_id) :])

    def append(self, *messages: ChatMessage) -> None:
        """
        Append `messages` to the thread, where `messages` is assumed without
        validation to be sorted by id and contain only messages with ids greater
        than the final message in the thread so far. Appending messages that do
        not meet these constraints will result in undefined behavior for other
        class methods, especially `get_after`
        """

        self.thread.extend(messages)

    def extend(self, other_thread: ChatThread) -> None:
        """
        Append `other_thread` to the end of the current thread. See
        `ChatThread.append` for caveats
        """

        self.thread.extend(other_thread.thread)

from __future__ import annotations
from bisect import bisect_right
from typing import Dict, Iterator, List, Optional
from game import Color
from serialization import JsonifyableBaseDataClass


class ChatMessage(JsonifyableBaseDataClass):
    """
    A container class for chat messages

    Attributes:

        timestamp: float - the server time, in seconds, when the message was
        received

        color: Color - the color of the player who created the message

        message: str - the message contents

        id: Optional[int] - the message ID. NB: auto generated. only set from
        source outside of test code
    """

    timestamp: float
    color: Color
    message: str
    id: Optional[int] = None

    def jsonifyable(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "color": self.color.name,
            "message": self.message,
            "id": self.id,
        }

    @classmethod
    def _deserialize(cls, data: Dict) -> ChatMessage:
        return ChatMessage(
            data["timestamp"], Color[data["color"]], data["message"], data["id"]
        )

    def __repr__(self) -> str:
        return (
            f"ChatMessage("
            f"timestamp={self.timestamp}"
            f", color={self.color}"
            f", message={self.message}"
            f", id={self.id if self.id is not None else '(not yet assigned)'})"
        )


class ChatThread(JsonifyableBaseDataClass):
    """
    An ordered thread of chat messages

    Attributes:

        thread: List[ChatMessage] = [] - the complete thread of messages

        is_complete: bool = False - True if this represents a complete thread,
        i.e. contains every message from the first onward, or False otherwise
    """

    # don't freak out! dataclassy can handle mutable defaults
    thread: List[ChatMessage] = []
    is_complete: bool = False

    def jsonifyable(self) -> List[Dict]:
        return {
            "thread": [msg.jsonifyable() for msg in self.thread],
            "isComplete": self.is_complete,
        }

    @classmethod
    def _deserialize(cls, data: Dict) -> JsonifyableBaseDataClass:
        return ChatThread(
            [ChatMessage.deserialize(msg) for msg in data["thread"]], data["isComplete"]
        )

    def __len__(self) -> int:
        return len(self.thread)

    def __iter__(self) -> Iterator[ChatMessage]:
        for msg in self.thread:
            yield msg

    def get_after(self, after_id: int = 0) -> ChatThread:
        """
        Return a thread consisting of all messages with an id strictly greater
        than `after_id`. As ids begin at 1, a value of 0 for `after_id`
        guarantees that the full thread is returned and is thus equivalent to
        the current object
        """

        after = self.thread[bisect_right([msg.id for msg in self.thread], after_id) :]
        return ChatThread(
            after, self.is_complete if len(after) == len(self.thread) else False
        )

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

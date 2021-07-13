from __future__ import annotations
from typing import Any
import json
from dataclassy import dataclass
from abc import ABC, ABCMeta, abstractmethod


class JsonifyableBase(ABC):
    """
    Base class for classes usable as OutgoingMessage data. Classes may also
    choose to implement a deserialization method, which is useful for python
    client applications
    """

    __slots__ = ()

    @abstractmethod
    def jsonifyable(self) -> Any:
        raise NotImplementedError()

    @classmethod
    def deserialize(cls, data: Any) -> JsonifyableBase:
        """
        Deserialize `data`, which is either a json string or a deserialized
        object (which may also be a string), into the class implementing this
        method.

        NOTE: when implementing this class, do not override this function.
        Rather, override `_deserialize`
        """

        if isinstance(data, str):
            # note that:
            # string_literal = "foo"
            # json.loads(string_literal) == string_literal
            data = json.loads(data)
        return cls._deserialize(data)

    @classmethod
    @abstractmethod
    def _deserialize(cls, data: Any) -> JsonifyableBase:
        raise NotImplementedError()


@dataclass(slots=True)
class JsonifyableBaseDataClass(metaclass=ABCMeta):
    """
    Dataclass version of base class for classes usable as OutgoingMessage data.

    A note about why this is separate from `JsonifyableBase`: because
    `dataclassy`'s `@dataclass` decorator uses a metaclass, and metaclasses of
    derived classes must be subclasses of the metaclasses of all bases,
    `metaclass=ABCMeta` (*not* `ABC`) and `@dataclass` must be applied at the
    same time. However, `dataclass` is an inappropriate model for some of the
    classes, e.g. `game.Game`, that need to implement `jsonifyable`. The only
    way to get everything we want, i.e. use `abc` and also optionally use
    `dataclassy`, is to have two base classes
    """

    @abstractmethod
    def jsonifyable(self) -> Any:
        raise NotImplementedError()

    @classmethod
    def deserialize(cls, data: Any) -> JsonifyableBaseDataClass:
        """
        Deserialize `data`, which is either a json string or a deserialized
        object (which may also be a string), into the class implementing this
        method.

        NOTE: when implementing this class, do not override this function.
        Rather, override `_deserialize`
        """

        if isinstance(data, str):
            data = json.loads(data)
        return cls._deserialize(data)

    @classmethod
    @abstractmethod
    def _deserialize(cls, data: Any) -> JsonifyableBaseDataClass:
        raise NotImplementedError()

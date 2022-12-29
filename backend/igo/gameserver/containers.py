from __future__ import annotations
from .chat import ChatThread
from typing import Dict, Optional
from dataclassy import dataclass
from igo.game import Color, Game
from igo.serialization import JsonifyableBase, JsonifyableBaseDataClass


@dataclass(slots=True)
class KeyPair:
    player_key: str
    ai_secret: Optional[str] = None


class KeyContainer(JsonifyableBase):
    """
    A container for player keys and AI secrets. When serialized, AI secrets are
    dropped, they being secrets and all. The preferred method of accessing the
    contained `KeyPair` objects is via indexing
    """

    _keys_w: KeyPair
    _keys_b: KeyPair

    def __init__(
        self,
        key_w: str,
        key_b: str,
        ai_secret_w: Optional[str] = None,
        ai_secret_b: Optional[str] = None,
    ) -> None:
        self._keys_w = KeyPair(key_w, ai_secret_w)
        self._keys_b = KeyPair(key_b, ai_secret_b)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"{Color.white.name}={self._keys_w}"
            f", {Color.black.name}={self._keys_b})"
        )

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, self.__class__):
            return False
        return self._keys_w == o._keys_w and self._keys_b == o._keys_b

    def jsonifyable(self) -> Dict[str, str]:
        return {
            Color.white.name: self._keys_w.player_key,
            Color.black.name: self._keys_b.player_key,
        }

    @classmethod
    def _deserialize(cls, data: Dict) -> KeyContainer:
        res: KeyContainer = cls.__new__(cls)
        res._keys_w = KeyPair(data[Color.white.name])
        res._keys_b = KeyPair(data[Color.black.name])
        return res

    def __getitem__(self, color: Color) -> KeyPair:
        return self._keys_w if color is Color.white else self._keys_b


@dataclass(slots=True)
class ClientData:
    """
    ClientData is a container for all of the various data that a single client
    is concerned with.

    Attributes:

        keys: KeyPair - the client's player key and AI secret, if relevant

        color: Color - the client's color

        game: Optional[Game] = None - the current game

        time_played: Optional[float] = None - the time in seconds that the game
        has been actively played thus far

        chat_thread: Optional[ChatThread] = None - the chat thread associated
        with the current game

        opponent_connected: Optional[bool] = None - whether or not the client's
        opponent in the current game is connected to a game server
    """

    keys: KeyPair
    color: Color
    game: Optional[Game] = None
    time_played: Optional[float] = None
    chat_thread: Optional[ChatThread] = None
    opponent_connected: Optional[bool] = None

    def __post_init__(self) -> None:
        self.chat_thread = ChatThread(is_complete=True)


class ResponseContainer(JsonifyableBaseDataClass):
    """
    A base container for responses which implements jsonifyable

    Attributes:

        success: bool - indicator of the input action's success

        explanation: str - explanation of success
    """

    success: bool
    explanation: str

    def jsonifyable(self):
        return {"success": self.success, "explanation": self.explanation}

    @classmethod
    def _deserialize(cls, data: Dict) -> ResponseContainer:
        res: ResponseContainer = cls.__new__(cls)
        res.success = data["success"]
        res.explanation = data["explanation"]
        return res


class GameResponseContainer(ResponseContainer):
    """
    A base container for the response to a game request which implements
    jsonifyable

    Attributes:

        success: bool - whether or not the request succeeded

        explanation: str - an explanatory string

        keys: Optional[KeyContainer] = None - if success, KeyContainer, and None
        otherwise

        your_color: Optional[Color] = None - if success, the color that the
        user is subscribed to, and None otherwise
    """

    keys: Optional[KeyContainer] = None
    your_color: Optional[Color] = None

    def jsonifyable(self):
        return {
            **{
                "keys": self.keys.jsonifyable() if self.keys else None,
                "yourColor": self.your_color.name if self.your_color else None,
            },
            **super().jsonifyable(),
        }

    @classmethod
    def _deserialize(cls, data: Dict) -> GameResponseContainer:
        res: GameResponseContainer = super(GameResponseContainer, cls)._deserialize(
            data
        )
        res.keys = KeyContainer.deserialize(data["keys"]) if res.success else None
        res.your_color = Color[data["yourColor"]] if res.success else None
        return res


class NewGameResponseContainer(GameResponseContainer):
    """
    A container for the response to a new game request which implements
    jsonifyable

    Attributes:

        success: bool - indicator of the input action's success

        explanation: str - explanation of success

        keys: Optional[KeyContainer] = None - if success, KeyContainer, and None
        otherwise

        your_color: Optional[Color] = None - if success, the color that the
        user is subscribed to, and None otherwise
    """

    @classmethod
    def _deserialize(cls, data: Dict) -> NewGameResponseContainer:
        return super(NewGameResponseContainer, cls)._deserialize(data)


class JoinGameResponseContainer(GameResponseContainer):
    """
    A container for the response to a join game request which implements
    jsonifyable

    Attributes:

        success: bool - whether or not the join request succeeded

        explanation: str - an explanatory string

        keys: Optional[KeyContainer] = None - if success, KeyContainer, and None
        otherwise

        your_color: Optional[Color] = None - if success, the color that the
        user is subscribed to, and None otherwise
    """

    @classmethod
    def _deserialize(cls, data: Dict) -> JoinGameResponseContainer:
        return super(JoinGameResponseContainer, cls)._deserialize(data)


class ActionResponseContainer(ResponseContainer):
    """
    A container for the response from Game.take_action which implements
    jsonifyable

    Attributes:

        success: bool - indicator of the input action's success

        explanation: str - explanation of success
    """

    @classmethod
    def _deserialize(cls, data: Dict) -> ActionResponseContainer:
        return super(ActionResponseContainer, cls)._deserialize(data)


class OpponentConnectedContainer(JsonifyableBaseDataClass):
    """
    Simple container for opponent's connectedness indicator which implements jsonifyable

    Attributes:

        opponent_connected: bool - indicator of the client's opponent's
        connectedness
    """

    opponent_connected: bool

    def jsonifyable(self) -> Dict:
        return {"opponentConnected": self.opponent_connected}

    @staticmethod
    def _deserialize(data: Dict) -> OpponentConnectedContainer:
        return OpponentConnectedContainer(data["opponentConnected"])


class GameStatusContainer(JsonifyableBaseDataClass):
    """
    A container for transmitting game status which implements jsonifyable.
    Combines a Game object with its time played value.
    """

    game: Game
    time_played: float

    def jsonifyable(self) -> Dict:
        return {**self.game.jsonifyable(), "timePlayed": self.time_played}

    @staticmethod
    def _deserialize(data: Dict) -> GameStatusContainer:
        return GameStatusContainer(Game.deserialize(data), data["timePlayed"])


class ErrorContainer(JsonifyableBaseDataClass):
    """
    A container for server error messages which implements jsonifyable

    Serialization note: the contained exception is pared down to just its string
    form when serialized. As such, the deserialized form is just a generic
    Exception which contains no specific type or stack trace information
    """

    exception: Exception

    def jsonifyable(self) -> Dict:
        return {"errorMessage": str(self.exception)}

    @staticmethod
    def _deserialize(data: Dict) -> ErrorContainer:
        return ErrorContainer(Exception(data["errorMessage"]))

from __future__ import annotations
from typing import Dict, Optional
from game import Color, Game
from serialization import JsonifyableBaseDataClass


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

        keys: Optional[Dict[Color, str]] = None - if success, a color to key
        mapping, and None otherwise

        your_color: Optional[Color] = None - if success, the color that the
        user is subscribed to, and None otherwise
    """

    keys: Optional[Dict[Color, str]] = None
    your_color: Optional[Color] = None

    def jsonifyable(self):
        return {
            **{
                "keys": {k.name: v for k, v in self.keys.items()}
                if self.keys
                else None,
                "yourColor": self.your_color.name if self.your_color else None,
            },
            **super().jsonifyable(),
        }

    @classmethod
    def _deserialize(cls, data: Dict) -> GameResponseContainer:
        res: GameResponseContainer = super(GameResponseContainer, cls)._deserialize(
            data
        )
        res.keys = (
            {color: data["keys"][color.name] for color in Color}
            if res.success
            else None
        )
        res.your_color = Color[data["yourColor"]] if res.success else None
        return res


class NewGameResponseContainer(GameResponseContainer):
    """
    A container for the response to a new game request which implements
    jsonifyable

    Attributes:

        success: bool - indicator of the input action's success

        explanation: str - explanation of success

        keys: Optional[Dict[Color, str]] = None - if success, a color to key
        mapping, and None otherwise

        your_color: Optional[Color] = None - if success, the color that the
        user is subscribed to, and None otherwise
    """

    @classmethod
    def _deserialize(cls, data: Dict) -> GameResponseContainer:
        return super(NewGameResponseContainer, cls)._deserialize(data)


class JoinGameResponseContainer(GameResponseContainer):
    """
    A container for the response to a join game request which implements
    jsonifyable

    Attributes:

        success: bool - whether or not the join request succeeded

        explanation: str - an explanatory string

        keys: Optional[Dict[Color, str]] = None - if success, a color to key
        mapping, and None otherwise

        your_color: Optional[Color] = None - if success, the color that the
        user is subscribed to, and None otherwise
    """

    @classmethod
    def _deserialize(cls, data: Dict) -> GameResponseContainer:
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
    def _deserialize(cls, data: Dict) -> GameResponseContainer:
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
        return ErrorContainer(Exception(data["exception"]))

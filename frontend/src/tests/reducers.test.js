import gameReducer from "../reducers/game";
import * as types from "../constants/ActionTypes";
import { POINTS, SIZE } from "../constants/BoardKeys";
import {
  BOARD,
  CONNECTED,
  MESSAGE,
  REJOIN_NEEDED,
  KEYS as KEYS_STATE,
  YOUR_COLOR as YOUR_COLOR_STATE,
  PAST_GAMES,
  OPPONENT_CONNECTED,
  CHAT_MESSAGES,
} from "../constants/StateKeys";
import {
  EXPLANATION,
  KEYS as KEYS_MSG,
  SUCCESS,
  YOUR_COLOR as YOUR_COLOR_MSG,
} from "../constants/IncomingMessageDataKeys";
import { clearMessage, clearRejoinNeeded } from "../actions";
import {
  DATA,
  MESSAGE_TYPE,
  MESSAGE as PAYLOAD_MESSAGE,
} from "../constants/IncomingMessagePayloadKeys";
import {
  GAME_ACTION_RESPONSE,
  GAME_STATUS,
  JOIN_GAME_RESPONSE,
  NEW_GAME_RESPONSE,
} from "../constants/IncomingMessageTypes";
import { BLACK, WHITE } from "../constants/Colors";

describe("game reducer", () => {
  const initialState = {
    [BOARD]: {
      [SIZE]: 19,
      [POINTS]: Array.from({ length: 19 }, () =>
        Array.from({ length: 19 }, () => ["", false, false, ""])
      ),
    },
    [CONNECTED]: false,
    [PAST_GAMES]: {},
  };

  it("should return the initial state", () => {
    expect(gameReducer(undefined, {})).toEqual(initialState);
  });

  it("should clear a message", () => {
    expect(
      gameReducer(
        { [MESSAGE]: "blah blah good boy blah what a good boy blah" },
        clearMessage()
      )
    ).toEqual({ [MESSAGE]: "" });
  });

  it("should clear rejoin needed", () => {
    expect(gameReducer({ [REJOIN_NEEDED]: true }, clearRejoinNeeded())).toEqual(
      { [REJOIN_NEEDED]: false }
    );
  });

  it("should set connected and unset rejoined needed", () => {
    expect(
      gameReducer({ [CONNECTED]: false }, { type: types.WS_OPEN })
    ).toEqual({ [CONNECTED]: true, [REJOIN_NEEDED]: false });
  });

  it("should set connected and rejoined needed", () => {
    expect(
      gameReducer(
        { [CONNECTED]: false, [KEYS_STATE]: {} },
        { type: types.WS_OPEN }
      )
    ).toMatchObject({ [CONNECTED]: true, [REJOIN_NEEDED]: true });
  });

  it("should unset connected", () => {
    expect(
      gameReducer({ [CONNECTED]: true }, { type: types.WS_CLOSED })
    ).toMatchObject({ [CONNECTED]: false });
  });
});

describe("game reducer incoming message", () => {
  const keysState = { [WHITE]: "9876543210", [BLACK]: "0123456789" };
  const keysResponse = { [WHITE]: "0123456789", [BLACK]: "9876543210" };
  const msgSuccess = "Success";
  const msgFailure = "Failure";
  const newGameResponseSuccess = {
    type: types.WS_MESSAGE,
    payload: {
      [PAYLOAD_MESSAGE]: {
        [MESSAGE_TYPE]: NEW_GAME_RESPONSE,
        [DATA]: {
          [SUCCESS]: true,
          [KEYS_MSG]: keysResponse,
          [YOUR_COLOR_MSG]: WHITE,
          [EXPLANATION]: msgSuccess,
        },
      },
    },
  };

  it("should write keys, color, and message (new game)", () => {
    expect(gameReducer({}, newGameResponseSuccess)).toEqual({
      [KEYS_STATE]: keysResponse,
      [YOUR_COLOR_STATE]: WHITE,
      [MESSAGE]: msgSuccess,
    });
  });

  const newGameResponseFailure = {
    type: types.WS_MESSAGE,
    payload: {
      [PAYLOAD_MESSAGE]: {
        [MESSAGE_TYPE]: NEW_GAME_RESPONSE,
        [DATA]: {
          [SUCCESS]: false,
          [EXPLANATION]: msgFailure,
        },
      },
    },
  };

  it("should retain old keys and color and write message (new game)", () => {
    expect(
      gameReducer(
        {
          [KEYS_STATE]: keysState,
          [YOUR_COLOR_STATE]: BLACK,
        },
        newGameResponseFailure
      )
    ).toEqual({
      [KEYS_STATE]: keysState,
      [YOUR_COLOR_STATE]: BLACK,
      [MESSAGE]: msgFailure,
    });
  });

  const joinGameResponseSuccess = JSON.parse(
    JSON.stringify(newGameResponseSuccess)
  );
  joinGameResponseSuccess.payload[PAYLOAD_MESSAGE][MESSAGE_TYPE] =
    JOIN_GAME_RESPONSE;

  it("should write keys, color, and message (join game)", () => {
    expect(gameReducer({}, joinGameResponseSuccess)).toEqual({
      [KEYS_STATE]: keysResponse,
      [YOUR_COLOR_STATE]: WHITE,
      [MESSAGE]: msgSuccess,
    });
  });

  const joinGameResponseFailure = JSON.parse(
    JSON.stringify(newGameResponseFailure)
  );
  joinGameResponseFailure.payload[PAYLOAD_MESSAGE][MESSAGE_TYPE] =
    JOIN_GAME_RESPONSE;

  it("should retain old keys and color and write message (join game)", () => {
    expect(
      gameReducer(
        {
          [KEYS_STATE]: keysState,
          [YOUR_COLOR_STATE]: BLACK,
        },
        joinGameResponseFailure
      )
    ).toEqual({
      [KEYS_STATE]: keysState,
      [YOUR_COLOR_STATE]: BLACK,
      [MESSAGE]: msgFailure,
    });
  });

  const gameActionSuccess = {
    type: types.WS_MESSAGE,
    payload: {
      [PAYLOAD_MESSAGE]: {
        [MESSAGE_TYPE]: GAME_ACTION_RESPONSE,
        [DATA]: {
          [SUCCESS]: true,
          [EXPLANATION]: msgSuccess,
        },
      },
    },
  };

  it("should not write a message", () => {
    expect(gameReducer({}, gameActionSuccess)).toEqual({});
  });

  const gameActionFailure = {
    type: types.WS_MESSAGE,
    payload: {
      [PAYLOAD_MESSAGE]: {
        [MESSAGE_TYPE]: GAME_ACTION_RESPONSE,
        [DATA]: {
          [SUCCESS]: false,
          [EXPLANATION]: msgFailure,
        },
      },
    },
  };

  it("should write a message", () => {
    expect(gameReducer({}, gameActionFailure)).toEqual({
      [MESSAGE]: msgFailure,
    });
  });

  const updatedBoard = {
    [BOARD]: {
      [SIZE]: 19,
      [POINTS]: Array.from({ length: 19 }, () =>
        Array.from({ length: 19 }, () => ["w", false, false, ""])
      ),
    },
  };
  const gameStatus = {
    type: types.WS_MESSAGE,
    payload: {
      [PAYLOAD_MESSAGE]: {
        [MESSAGE_TYPE]: GAME_STATUS,
        [DATA]: updatedBoard,
      },
    },
  };
  const myKey = keysState[WHITE];
  const theirKey = keysState[BLACK];
  const initStateWithKeys = {
    [KEYS_STATE]: keysState,
    [YOUR_COLOR_STATE]: WHITE,
    [PAST_GAMES]: { [myKey]: 0, [theirKey]: 0 },
  };

  it("should update the board", () => {
    expect(gameReducer(initStateWithKeys, gameStatus)).toEqual(
      expect.objectContaining(updatedBoard)
    );
  });

  it("should update past games", () => {
    const newState = gameReducer(initStateWithKeys, gameStatus);
    expect(newState[PAST_GAMES][myKey]).toBeGreaterThan(0);
  });

  it("should not blow away unrelated past games state", () => {
    const newState = gameReducer(initStateWithKeys, gameStatus);
    expect(newState[PAST_GAMES][theirKey]).toBe(0);
  });
});

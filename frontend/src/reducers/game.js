import {
  CLEAR_MESSAGE,
  CLEAR_REJOIN_NEEDED,
  CLEAR_ERROR,
  WS_CLOSED,
  WS_MESSAGE,
  WS_OPEN,
} from "../constants/ActionTypes";
import { POINTS, SIZE } from "../constants/BoardKeys";
import { IS_COMPLETE, THREAD } from "../constants/ChatThreadKeys";
import {
  EXPLANATION,
  KEYS as KEYS_MSG,
  SUCCESS,
  YOUR_COLOR as YOUR_COLOR_MSG,
} from "../constants/IncomingMessageDataKeys";
import {
  MESSAGE as PAYLOAD_MESSAGE,
  DATA,
  MESSAGE_TYPE,
} from "../constants/IncomingMessagePayloadKeys";
import {
  CHAT,
  ERROR,
  GAME_ACTION_RESPONSE,
  GAME_STATUS,
  JOIN_GAME_RESPONSE,
  NEW_GAME_RESPONSE,
  OPPONENT_CONNECTED,
} from "../constants/IncomingMessageTypes";
import {
  MESSAGE,
  BOARD,
  CONNECTED,
  REJOIN_NEEDED,
  KEYS as KEYS_STATE,
  YOUR_COLOR as YOUR_COLOR_STATE,
  PAST_GAMES,
  CHAT_MESSAGES,
  ERROR_MESSAGE,
} from "../constants/StateKeys";

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

export default function game(state = initialState, action) {
  switch (action.type) {
    case CLEAR_MESSAGE:
      return {
        ...state,
        [MESSAGE]: "",
      };
    case CLEAR_REJOIN_NEEDED:
      return {
        ...state,
        [REJOIN_NEEDED]: false,
      };
    case CLEAR_ERROR:
      return {
        ...state,
        [ERROR_MESSAGE]: "",
      };
    case WS_MESSAGE:
      const msg = action.payload[PAYLOAD_MESSAGE];
      const data = msg[DATA];
      // check the type and process accordingly
      switch (msg[MESSAGE_TYPE]) {
        case NEW_GAME_RESPONSE:
        case JOIN_GAME_RESPONSE:
          return {
            ...state,
            // we want to be careful to preserve state on failure in case we are
            // already in a game
            [KEYS_STATE]: data[SUCCESS] ? data[KEYS_MSG] : state[KEYS_STATE],
            [YOUR_COLOR_STATE]: data[SUCCESS]
              ? data[YOUR_COLOR_MSG]
              : state[YOUR_COLOR_STATE],
            [MESSAGE]: data[EXPLANATION],
          };
        case GAME_ACTION_RESPONSE:
          // there's no reason to alert the player after a successful game
          // action, only on failure
          if (!data[SUCCESS]) {
            return {
              ...state,
              [MESSAGE]: data[EXPLANATION],
            };
          }
          return state;
        case GAME_STATUS:
          return {
            ...state,
            ...data,
            [PAST_GAMES]: {
              ...state[PAST_GAMES],
              [state[KEYS_STATE][state[YOUR_COLOR_STATE]]]: Date.now(),
            },
          };
        case CHAT:
          return {
            ...state,
            [CHAT_MESSAGES]:
              data[IS_COMPLETE] || !(CHAT_MESSAGES in state)
                ? data[THREAD]
                : state[CHAT_MESSAGES].concat(data[THREAD]),
          };
        case OPPONENT_CONNECTED:
          return {
            ...state,
            ...data,
          };
        case ERROR:
          return {
            ...state,
            ...data,
          };
        default:
          throw new TypeError(
            `Unknown incoming message type ${msg[MESSAGE_TYPE]} encountered`
          );
      }
    case WS_OPEN:
      return {
        ...state,
        [CONNECTED]: true,
        [REJOIN_NEEDED]: KEYS_STATE in state,
      };
    case WS_CLOSED:
      return {
        ...state,
        [CONNECTED]: false,
      };

    default:
      return state;
  }
}

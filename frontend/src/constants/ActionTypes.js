import {
  DEFAULT_PREFIX,
  WEBSOCKET_CLOSED,
  WEBSOCKET_CONNECT,
  WEBSOCKET_MESSAGE,
  WEBSOCKET_OPEN,
  WEBSOCKET_SEND,
} from "@giantmachines/redux-websocket";

// websocket actions
export const WS_CLOSED = `${DEFAULT_PREFIX}::${WEBSOCKET_CLOSED}`;
export const WS_OPEN = `${DEFAULT_PREFIX}::${WEBSOCKET_OPEN}`;
export const WS_MESSAGE = `${DEFAULT_PREFIX}::${WEBSOCKET_MESSAGE}`;
export const WS_SEND = `${DEFAULT_PREFIX}::${WEBSOCKET_SEND}`;
export const WS_CONNECT = `${DEFAULT_PREFIX}::${WEBSOCKET_CONNECT}`;

// internal actions
export const CLEAR_MESSAGE = "CLEAR_MESSAGE";
export const CLEAR_REJOIN_NEEDED = "CLEAR_REJOIN_NEEDED";
export const CLEAR_ERROR = "CLEAR_ERROR";

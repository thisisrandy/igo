import * as types from "../constants/ActionTypes";

export const clearMessage = () => ({
  type: types.CLEAR_MESSAGE,
  payload: {},
});

export const clearRejoinNeeded = () => ({
  type: types.CLEAR_REJOIN_NEEDED,
  payload: {},
});

export const clearError = () => ({
  type: types.CLEAR_ERROR,
  payload: {},
});

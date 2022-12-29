import * as actions from "../actions";
import * as types from "../constants/ActionTypes";

describe("actions", () => {
  it("should create an action to clear a message", () => {
    const expected = {
      type: types.CLEAR_MESSAGE,
      payload: {},
    };
    expect(actions.clearMessage()).toEqual(expected);
  });
  it("should create an action to clear rejoin needed status", () => {
    const expected = {
      type: types.CLEAR_REJOIN_NEEDED,
      payload: {},
    };
    expect(actions.clearRejoinNeeded()).toEqual(expected);
  });
});

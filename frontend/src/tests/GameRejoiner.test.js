import { BLACK, WHITE } from "../constants/Colors";
import {
  YOUR_COLOR,
  KEYS,
  REJOIN_NEEDED,
  CONNECTED,
} from "../constants/StateKeys";
import createMockStore from "redux-mock-store";
import { render } from "@testing-library/react";
import { Provider } from "react-redux";
import GameRejoiner from "../components/GameRejoiner";
import { CLEAR_REJOIN_NEEDED, WS_SEND } from "../constants/ActionTypes";
import { TYPE } from "../constants/OutgoingMessageKeys";
import { JOIN_GAME } from "../constants/OutgoingMessageTypes";
import { GAME } from "../constants/ReducerKeys";

const keyW = "0123456789";
const keyB = "9876543210";
const initialState = {
  game: {
    [KEYS]: { [WHITE]: keyW, [BLACK]: keyB },
    [YOUR_COLOR]: BLACK,
    [REJOIN_NEEDED]: true,
    [CONNECTED]: true,
  },
};

const mockStore = createMockStore([]);

test("dispatches nothing when no rejoin needed", () => {
  const state = JSON.parse(JSON.stringify(initialState));
  state[GAME][REJOIN_NEEDED] = false;
  const store = mockStore(state);
  render(
    <Provider store={store}>
      <GameRejoiner />
    </Provider>
  );

  expect(store.getActions().length).toBe(0);
});

test("dispatches nothing when not connected", () => {
  const state = JSON.parse(JSON.stringify(initialState));
  state[GAME][CONNECTED] = false;
  const store = mockStore(state);
  render(
    <Provider store={store}>
      <GameRejoiner />
    </Provider>
  );

  expect(store.getActions().length).toBe(0);
});

test("dispatches correct actions when rejoin needed and connected", () => {
  const store = mockStore(initialState);
  render(
    <Provider store={store}>
      <GameRejoiner />
    </Provider>
  );

  const actions = store.getActions();
  expect(actions.length).toBe(2);
  expect(actions[0].type).toBe(WS_SEND);
  expect(actions[0].payload[TYPE]).toBe(JOIN_GAME);
  expect(actions[1].type).toBe(CLEAR_REJOIN_NEEDED);
});

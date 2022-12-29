import {
  KEYS,
  PENDING_REQUEST,
  STATUS,
  YOUR_COLOR,
} from "../constants/StateKeys";
import createMockStore from "redux-mock-store";
import { act, render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import { BLACK, WHITE } from "../constants/Colors";
import { MARK_DEAD } from "../constants/RequestType";
import { ENDGAME, REQUEST_PENDING } from "../constants/GameStatus";
import RequestResponseDialog from "../components/RequestResponseDialog";
import { INITIATOR, REQUEST_TYPE } from "../constants/RequestKeys";
import { ACTION_TYPE } from "../constants/OutgoingMessageKeys";
import { ACCEPT, REJECT } from "../constants/GameActionTypes";
import { GAME } from "../constants/ReducerKeys";

const keyW = "0123456789";
const keyB = "9876543210";
const initialState = {
  game: {
    [STATUS]: REQUEST_PENDING,
    [PENDING_REQUEST]: { [INITIATOR]: WHITE, [REQUEST_TYPE]: MARK_DEAD },
    [YOUR_COLOR]: BLACK,
    [KEYS]: { [WHITE]: keyW, [BLACK]: keyB },
  },
};
const mockStore = createMockStore([]);

function setUp(state = initialState) {
  const store = mockStore(state);
  render(
    <Provider store={store}>
      <RequestResponseDialog zIndex={1} />
    </Provider>
  );

  return store;
}

test("not open when no request pending", () => {
  setUp({ game: { ...initialState[GAME], [STATUS]: ENDGAME } });
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
});

test("not open when pending request is made by current player", () => {
  setUp({
    game: {
      ...initialState[GAME],
      [PENDING_REQUEST]: {
        ...initialState[GAME][PENDING_REQUEST],
        [INITIATOR]: BLACK,
      },
    },
  });
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
});

test("displays when pending request is made by other player", () => {
  setUp();
  expect(screen.queryByRole("dialog")).toBeInTheDocument();
});

test("accept sends correct action", () => {
  const store = setUp();
  const accept = screen.queryByRole("button", { name: /yes/i });
  act(() => {
    accept.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  });
  expect(store.getActions().length).toBe(1);
  expect(store.getActions()[0].payload[ACTION_TYPE]).toBe(ACCEPT);
});

test("reject sends correct action", () => {
  const store = setUp();
  const accept = screen.queryByRole("button", { name: /no/i });
  act(() => {
    accept.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  });
  expect(store.getActions().length).toBe(1);
  expect(store.getActions()[0].payload[ACTION_TYPE]).toBe(REJECT);
});

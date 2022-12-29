import { GAME } from "../constants/ReducerKeys";
import {
  KEYS,
  PENDING_REQUEST,
  STATUS,
  YOUR_COLOR,
} from "../constants/StateKeys";
import createMockStore from "redux-mock-store";
import { render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import { BLACK, WHITE } from "../constants/Colors";
import { MARK_DEAD } from "../constants/RequestType";
import { ENDGAME, REQUEST_PENDING } from "../constants/GameStatus";
import { INITIATOR, REQUEST_TYPE } from "../constants/RequestKeys";
import RequestResponsePendingAlert from "../components/RequestResponsePendingAlert";

const keyW = "0123456789";
const keyB = "9876543210";
const initialState = {
  game: {
    [STATUS]: REQUEST_PENDING,
    [PENDING_REQUEST]: { [INITIATOR]: BLACK, [REQUEST_TYPE]: MARK_DEAD },
    [YOUR_COLOR]: BLACK,
    [KEYS]: { [WHITE]: keyW, [BLACK]: keyB },
  },
};
const mockStore = createMockStore([]);

function setUp(state = initialState) {
  const store = mockStore(state);
  render(
    <Provider store={store}>
      <RequestResponsePendingAlert zIndex={1} />
    </Provider>
  );

  return store;
}

test("not open when no request pending", () => {
  setUp({ game: { ...initialState[GAME], [STATUS]: ENDGAME } });
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
});

test("not open when pending request is made by other player", () => {
  setUp({
    game: {
      ...initialState[GAME],
      [PENDING_REQUEST]: {
        ...initialState[GAME][PENDING_REQUEST],
        [INITIATOR]: WHITE,
      },
    },
  });
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
});

test("displays when pending request is made by current player", () => {
  setUp();
  expect(screen.queryByRole("dialog")).toBeInTheDocument();
});

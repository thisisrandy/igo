import createMockStore from "redux-mock-store";
import { render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import { WHITE, BLACK } from "../constants/Colors";
import {
  KEYS,
  KOMI,
  PRISONERS,
  TERRITORY,
  YOUR_COLOR,
  OPPONENT_CONNECTED,
  TURN,
} from "../constants/StateKeys";
import PlayerCard from "../components/PlayerCard";
import { GAME } from "../constants/ReducerKeys";

const keyW = "0123456789";
const keyB = "9876543210";
const state = {
  game: {
    [YOUR_COLOR]: BLACK,
    [PRISONERS]: { [WHITE]: 5, [BLACK]: 10 },
    [TERRITORY]: { [WHITE]: 6, [BLACK]: 11 },
    [KOMI]: 6.5,
    [KEYS]: { [WHITE]: keyW, [BLACK]: keyB },
    [OPPONENT_CONNECTED]: true,
    [TURN]: BLACK,
  },
};

const mockStore = createMockStore([]);

test("empty info with empty state", () => {
  const store = mockStore({ game: {} });
  render(
    <Provider store={store}>
      <PlayerCard color={BLACK} joinedToGame={false} playing={false} />
    </Provider>
  );

  expect(screen.getByLabelText(/prisoner count/).innerHTML).toBe("-");
  expect(screen.getByLabelText(/territory count/).innerHTML).toBe("-");
  expect(screen.getByLabelText(/total score/).innerHTML).toBe("-");
  expect(screen.queryByLabelText(/it's .*?'s turn/)).not.toBeInTheDocument();
  expect(screen.getByLabelText(/player key for black/).innerHTML).toBe(
    "Player Key: -"
  );
  expect(screen.queryByLabelText(/connection status/)).not.toBeInTheDocument();
});

test("values displayed correctly for self", () => {
  const store = mockStore(state);
  render(
    <Provider store={store}>
      <PlayerCard color={BLACK} joinedToGame={true} playing={true} />
    </Provider>
  );

  expect(screen.getByLabelText(/prisoner count/).innerHTML).toBe("10");
  expect(screen.getByLabelText(/territory count/).innerHTML).toBe("11");
  expect(screen.getByLabelText(/total score/).innerHTML).toBe("21");
  expect(screen.getByLabelText(/it's black's turn/)).toBeInTheDocument();
  expect(screen.getByLabelText(/player key for black/).innerHTML).toBe(
    `Player Key: ${keyB}`
  );
  expect(screen.getByLabelText(/connection status/).innerHTML).toBe("(you)");
});

test("values displayed correctly for connected opponent", () => {
  const store = mockStore(state);
  render(
    <Provider store={store}>
      <PlayerCard color={WHITE} joinedToGame={true} playing={true} />
    </Provider>
  );

  expect(screen.getByLabelText(/prisoner count/).innerHTML).toBe("5");
  expect(screen.getByLabelText(/territory count/).innerHTML).toBe("6");
  expect(screen.getByLabelText(/total score/).innerHTML).toBe("17.5");
  expect(screen.queryByLabelText(/it's .*?'s turn/)).not.toBeInTheDocument();
  expect(screen.getByLabelText(/player key for white/).innerHTML).toBe(
    `Player Key: ${keyW}`
  );
  expect(screen.getByLabelText(/connection status/).innerHTML).toBe(
    "(connected)"
  );
});

test("not connected opponent displays as such", () => {
  const store = mockStore({
    game: { ...state[GAME], [OPPONENT_CONNECTED]: false },
  });
  render(
    <Provider store={store}>
      <PlayerCard color={WHITE} joinedToGame={true} playing={true} />
    </Provider>
  );

  expect(screen.getByLabelText(/connection status/).innerHTML).toBe(
    "(not connected)"
  );
});

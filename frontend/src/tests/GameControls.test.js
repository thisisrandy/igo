import { BLACK, WHITE } from "../constants/Colors";
import {
  YOUR_COLOR,
  KEYS,
  CONNECTED,
  PAST_GAMES,
} from "../constants/StateKeys";
import createMockStore from "redux-mock-store";
import { ACTION_TYPE } from "../constants/OutgoingMessageKeys";
import {
  PASS_TURN,
  REQUEST_DRAW,
  REQUEST_TALLY_SCORE,
  RESIGN,
} from "../constants/GameActionTypes";
import {
  render,
  act,
  screen,
  waitForElementToBeRemoved,
} from "@testing-library/react";
import { Provider } from "react-redux";
import GameControls from "../components/GameControls";

const keyW = "0123456789";
const keyB = "9876543210";
const initialState = {
  game: {
    [YOUR_COLOR]: BLACK,
    [KEYS]: { [WHITE]: keyW, [BLACK]: keyB },
    [CONNECTED]: true,
    [PAST_GAMES]: {},
  },
};

const mockStore = createMockStore([]);

test("correct buttons displayed while game not in progress", () => {
  render(
    <Provider store={mockStore(initialState)}>
      <GameControls
        playing={false}
        endGame={false}
        gameInProgress={false}
        myTurn={false}
      />
    </Provider>
  );

  const newGame = screen.getByRole("button", { name: "New Game" });
  expect(newGame).toBeInTheDocument();
  const joinGame = screen.getByRole("button", { name: "Join/Resume Game" });
  expect(joinGame).toBeInTheDocument();
});

test("new game click brings up dialog", () => {
  render(
    <Provider store={mockStore(initialState)}>
      <GameControls
        playing={false}
        endGame={false}
        gameInProgress={false}
        myTurn={false}
      />
    </Provider>
  );

  const newGame = screen.getByRole("button", { name: "New Game" });
  act(() => {
    newGame.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  });
  const dialog = screen.getByRole("dialog");
  expect(dialog).toBeInTheDocument();
  const dialogHeading = screen.getByRole("heading", { name: "New Game" });
  expect(dialogHeading).toBeInTheDocument();
});

test("join game click brings up dialog", () => {
  render(
    <Provider store={mockStore(initialState)}>
      <GameControls
        playing={false}
        endGame={false}
        gameInProgress={false}
        myTurn={false}
      />
    </Provider>
  );

  const joinGame = screen.getByRole("button", { name: "Join/Resume Game" });
  act(() => {
    joinGame.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  });
  const dialog = screen.getByRole("dialog");
  expect(dialog).toBeInTheDocument();
  const dialogHeading = screen.getByRole("heading", {
    name: "Join/Resume Game",
  });
  expect(dialogHeading).toBeInTheDocument();
});

test("correct buttons displayed while game in progress", () => {
  render(
    <Provider store={mockStore(initialState)}>
      <GameControls
        playing={true}
        endGame={false}
        gameInProgress={true}
        myTurn={false}
      />
    </Provider>
  );

  const pass = screen.getByRole("button", { name: "Pass" });
  expect(pass).toBeInTheDocument();
  const resign = screen.getByRole("button", { name: "Resign" });
  expect(resign).toBeInTheDocument();
  const requestDraw = screen.getByRole("button", { name: "Request Draw" });
  expect(requestDraw).toBeInTheDocument();
  const requestTally = screen.getByRole("button", {
    name: "Request Tally Score",
  });
  expect(requestTally).toBeInTheDocument();
});

test("pass button dispatches correct action", () => {
  const store = mockStore(initialState);
  render(
    <Provider store={store}>
      <GameControls
        playing={true}
        endGame={false}
        gameInProgress={true}
        myTurn={true}
      />
    </Provider>
  );

  const passButton = screen.getByRole("button", { name: "Pass" });
  act(() => {
    passButton.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  });
  expect(store.getActions().pop().payload[ACTION_TYPE]).toBe(PASS_TURN);
});

test("resign button dispatches correct action", async () => {
  const store = mockStore(initialState);
  render(
    <Provider store={store}>
      <GameControls
        playing={true}
        endGame={false}
        gameInProgress={true}
        myTurn={true}
      />
    </Provider>
  );

  const resignButton = screen.getByRole("button", { name: "Resign" });
  act(() => {
    resignButton.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  });
  const confirmationDialog = screen.getByRole("dialog");
  expect(confirmationDialog).toBeInTheDocument();
  const dialogHeading = screen.getByRole("heading", { name: "Confirmation" });
  expect(dialogHeading).toBeInTheDocument();
  const yesButton = screen.getByRole("button", { name: "Yes" });
  act(() => {
    yesButton.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  });
  expect(store.getActions().pop().payload[ACTION_TYPE]).toBe(RESIGN);
  await waitForElementToBeRemoved(() => screen.queryByRole("dialog"));
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
});

test("request draw button dispatches correct action", () => {
  const store = mockStore(initialState);
  render(
    <Provider store={store}>
      <GameControls
        playing={true}
        endGame={false}
        gameInProgress={true}
        myTurn={true}
      />
    </Provider>
  );

  const requestDrawButton = screen.getByRole("button", {
    name: "Request Draw",
  });
  act(() => {
    requestDrawButton.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  });
  expect(store.getActions().pop().payload[ACTION_TYPE]).toBe(REQUEST_DRAW);
});

test("request tally button dispatches correct action", () => {
  const store = mockStore(initialState);
  render(
    <Provider store={store}>
      <GameControls
        playing={false}
        endGame={true}
        gameInProgress={true}
        myTurn={true}
      />
    </Provider>
  );

  const requestTallyButton = screen.getByRole("button", {
    name: "Request Tally Score",
  });
  act(() => {
    requestTallyButton.dispatchEvent(
      new MouseEvent("click", { bubbles: true })
    );
  });
  expect(store.getActions().pop().payload[ACTION_TYPE]).toBe(
    REQUEST_TALLY_SCORE
  );
});

import Board from "../components/Board";
import { POINTS, SIZE } from "../constants/BoardKeys";
import { BLACK, WHITE } from "../constants/Colors";
import {
  BOARD,
  YOUR_COLOR,
  KEYS,
  CONNECTED,
  LAST_MOVE,
} from "../constants/StateKeys";
import createMockStore from "redux-mock-store";
import {
  ACTION_TYPE,
  COORDS,
  KEY,
  TYPE,
} from "../constants/OutgoingMessageKeys";
import { GAME_ACTION } from "../constants/OutgoingMessageTypes";
import { MARK_DEAD, PLACE_STONE } from "../constants/GameActionTypes";
import { render, act, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import { WS_SEND } from "../constants/ActionTypes";
import { GAME } from "../constants/ReducerKeys";

const keyW = "0123456789";
const keyB = "9876543210";
const boardSize = 9;
const emptyBoard = {
  game: {
    [BOARD]: {
      [SIZE]: boardSize,
      [POINTS]: Array.from({ length: boardSize }, () =>
        Array.from({ length: boardSize }, () => ["", false, false, ""])
      ),
    },
    [YOUR_COLOR]: BLACK,
    [KEYS]: { [WHITE]: keyW, [BLACK]: keyB },
    [CONNECTED]: true,
  },
};

const mockStore = createMockStore([]);

test("renders empty Board", () => {
  render(
    <Provider store={mockStore(emptyBoard)}>
      <Board myTurn={true} playing={true} endGame={false} />
    </Provider>
  );

  const board = screen.getByAltText("go board");
  expect(board).toBeInTheDocument();
  const stone = screen.queryByAltText(/stone/);
  expect(stone).not.toBeInTheDocument();
});

test("renders Board with white stone", () => {
  const board = JSON.parse(JSON.stringify(emptyBoard));
  board[GAME][BOARD][POINTS][0][0][0] = "w";
  render(
    <Provider store={mockStore(board)}>
      <Board myTurn={true} playing={true} endGame={false} />
    </Provider>
  );

  const white = screen.getByAltText("white stone");
  expect(white).toBeInTheDocument();
  const black = screen.queryByAltText("black stone");
  expect(black).not.toBeInTheDocument();
});

test("renders Board with black stone", () => {
  const board = JSON.parse(JSON.stringify(emptyBoard));
  board[GAME][BOARD][POINTS][0][0][0] = "b";
  render(
    <Provider store={mockStore(board)}>
      <Board myTurn={true} playing={true} endGame={false} />
    </Provider>
  );

  const white = screen.queryByAltText("white stone");
  expect(white).not.toBeInTheDocument();
  const black = screen.getByAltText("black stone");
  expect(black).toBeInTheDocument();
});

test("renders Board with several stones", () => {
  const board = JSON.parse(JSON.stringify(emptyBoard));
  board[GAME][BOARD][POINTS][0][0][0] = "b";
  board[GAME][BOARD][POINTS][0][1][0] = "b";
  board[GAME][BOARD][POINTS][1][0][0] = "b";
  board[GAME][BOARD][POINTS][0][5][0] = "w";
  board[GAME][BOARD][POINTS][0][6][0] = "w";
  render(
    <Provider store={mockStore(board)}>
      <Board myTurn={true} playing={true} endGame={false} />
    </Provider>
  );

  const white = screen.getAllByAltText("white stone");
  expect(white.length).toBe(2);
  const black = screen.getAllByAltText("black stone");
  expect(black.length).toBe(3);
});

test("board size is correct", () => {
  render(
    <Provider store={mockStore(emptyBoard)}>
      <Board myTurn={true} playing={true} endGame={false} />
    </Provider>
  );

  const bottomRight = screen.getByRole("button", {
    name: new RegExp(`\\(${boardSize - 1}, ${boardSize - 1}\\)`),
  });
  expect(bottomRight).toBeInTheDocument();
  const tooFarDown = screen.queryByRole("button", {
    name: new RegExp(`\\(${boardSize}, ${boardSize - 1}\\)`),
  });
  expect(tooFarDown).not.toBeInTheDocument();
  const tooFarRight = screen.queryByRole("button", {
    name: new RegExp(`\\(${boardSize - 1}, ${boardSize}\\)`),
  });
  expect(tooFarRight).not.toBeInTheDocument();
});

test("board button labels are correct during play on my turn", () => {
  const board = JSON.parse(JSON.stringify(emptyBoard));
  board[GAME][BOARD][POINTS][0][0][0] = "b";
  board[GAME][BOARD][POINTS][0][1][0] = "w";
  render(
    <Provider store={mockStore(board)}>
      <Board myTurn={true} playing={true} endGame={false} />
    </Provider>
  );

  const blackStone = screen.getByRole("button", {
    name: /unclickable black stone.*\(0, 0\)/,
  });
  expect(blackStone).toBeInTheDocument();
  const whiteStone = screen.getByRole("button", {
    name: /unclickable white stone.*\(0, 1\)/,
  });
  expect(whiteStone).toBeInTheDocument();
  const emptyPoint = screen.getByRole("button", {
    name: /^clickable point.*\(1, 1\)/,
  });
  expect(emptyPoint).toBeInTheDocument();
});

test("board button labels are correct during play on my opponent's turn", () => {
  render(
    <Provider store={mockStore(emptyBoard)}>
      <Board myTurn={false} playing={true} endGame={false} />
    </Provider>
  );

  const emptyPoint = screen.getByRole("button", {
    name: /unclickable point.*\(1, 1\)/,
  });
  expect(emptyPoint).toBeInTheDocument();
});

test("board button labels are correct during the endgame", () => {
  const board = JSON.parse(JSON.stringify(emptyBoard));
  board[GAME][BOARD][POINTS][0][0][0] = "b";
  render(
    <Provider store={mockStore(board)}>
      <Board myTurn={true} playing={false} endGame={true} />
    </Provider>
  );

  const blackStone = screen.getByRole("button", {
    name: /^clickable black stone.*\(0, 0\)/,
  });
  expect(blackStone).toBeInTheDocument();
  const emptyPoint = screen.getByRole("button", {
    name: /unclickable point.*\(1, 1\)/,
  });
  expect(emptyPoint).toBeInTheDocument();
});

test("clicks dispatch correct actions during play", () => {
  const store = mockStore(emptyBoard);
  render(
    <Provider store={store}>
      <Board myTurn={true} playing={true} endGame={false} />
    </Provider>
  );

  const emptyPoint = screen.getByRole("button", { name: /\(0, 0\)/ });
  act(() => {
    emptyPoint.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  });
  expect(store.getActions().length).toBe(1);
  const action = store.getActions().pop();
  expect(action.type).toBe(WS_SEND);
  expect(action.payload).toEqual({
    [TYPE]: GAME_ACTION,
    [KEY]: keyB,
    [ACTION_TYPE]: PLACE_STONE,
    [COORDS]: [0, 0],
  });
});

test("clicks dispatch correct actions during endgame", () => {
  const board = JSON.parse(JSON.stringify(emptyBoard));
  board[GAME][BOARD][POINTS][0][0][0] = "b";
  const store = mockStore(board);
  render(
    <Provider store={store}>
      <Board myTurn={true} playing={false} endGame={true} />
    </Provider>
  );

  const blackStone = screen.getByRole("button", { name: /\(0, 0\)/ });
  act(() => {
    blackStone.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  });
  expect(store.getActions().length).toBe(1);
  const action = store.getActions().pop();
  expect(action.type).toBe(WS_SEND);
  expect(action.payload).toEqual({
    [TYPE]: GAME_ACTION,
    [KEY]: keyB,
    [ACTION_TYPE]: MARK_DEAD,
    [COORDS]: [0, 0],
  });
});

test("marked dead stones display correctly", () => {
  const board = JSON.parse(JSON.stringify(emptyBoard));
  board[GAME][BOARD][POINTS][0][0][0] = "b";
  board[GAME][BOARD][POINTS][0][0][1] = true;
  const store = mockStore(board);
  render(
    <Provider store={store}>
      <Board myTurn={true} playing={false} endGame={true} />
    </Provider>
  );

  const deadMark = screen.getByLabelText(/marked as dead.*\(0, 0\)/);
  expect(deadMark).toBeInTheDocument();
});

test("counted points display correctly", () => {
  const board = JSON.parse(JSON.stringify(emptyBoard));
  board[GAME][BOARD][POINTS][0][0] = ["b", false, false, ""];
  board[GAME][BOARD][POINTS][0][1] = ["", false, true, "b"];
  board[GAME][BOARD][POINTS][1][0] = ["", false, true, "w"];
  board[GAME][BOARD][POINTS][1][1] = ["", false, true, ""];
  const store = mockStore(board);
  render(
    <Provider store={store}>
      <Board myTurn={true} playing={false} endGame={false} />
    </Provider>
  );

  const shouldNotBeCounted = screen.queryByLabelText(/counted for.*\(0, 0\)/);
  expect(shouldNotBeCounted).not.toBeInTheDocument();
  const countedBlack = screen.queryByLabelText(/counted for black.*\(0, 1\)/);
  expect(countedBlack).toBeInTheDocument();
  const countedWhite = screen.queryByLabelText(/counted for white.*\(1, 0\)/);
  expect(countedWhite).toBeInTheDocument();
  const countedNoOne = screen.queryByLabelText(/counted for no one.*\(1, 1\)/);
  expect(countedNoOne).toBeInTheDocument();
});

test("last stone placed is correctly highlighted", () => {
  const board = JSON.parse(JSON.stringify(emptyBoard));
  board[GAME][BOARD][POINTS][0][0][0] = "b";
  board[GAME][LAST_MOVE] = [0, 0];
  const store = mockStore(board);
  render(
    <Provider store={store}>
      <Board myTurn={false} playing={true} endGame={false} />
    </Provider>
  );

  const deadMark = screen.getByLabelText(/\(0, 0\), which was the last move/);
  expect(deadMark).toBeInTheDocument();
});

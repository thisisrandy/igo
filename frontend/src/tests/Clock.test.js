import { act, render, screen } from "@testing-library/react";
import Clock from "../components/Clock";
import { TIME_PLAYED, STATUS } from "../constants/StateKeys";
import { COMPLETE, PLAY } from "../constants/GameStatus";
import createMockStore from "redux-mock-store";
import { Provider } from "react-redux";

const mockStore = createMockStore([]);

test("renders Clock", () => {
  render(
    <Provider store={mockStore({ game: {} })}>
      <Clock />
    </Provider>
  );
  const clock = screen.getByText("Time played: 00:00:00");
  expect(clock).toBeInTheDocument();
});

test("Clock uses server time", () => {
  render(
    <Provider
      store={mockStore({ game: { [TIME_PLAYED]: 92165, [STATUS]: PLAY } })}
    >
      <Clock />
    </Provider>
  );
  const clock = screen.getByText("Time played: 1d, 01:36:05");
  expect(clock).toBeInTheDocument();
});

test("Clock ticks during play", () => {
  jest.useFakeTimers();
  render(
    <Provider store={mockStore({ game: { [TIME_PLAYED]: 0, [STATUS]: PLAY } })}>
      <Clock />
    </Provider>
  );
  act(() => {
    jest.advanceTimersByTime(66000);
  });
  const clock = screen.getByText("Time played: 00:01:06");
  expect(clock).toBeInTheDocument();
});

test("Clock doesn't tick after play complete", () => {
  jest.useFakeTimers();
  render(
    <Provider
      store={mockStore({ game: { [TIME_PLAYED]: 0, [STATUS]: COMPLETE } })}
    >
      <Clock />
    </Provider>
  );
  act(() => {
    jest.advanceTimersByTime(66000);
  });
  const clock = screen.getByText("Time played: 00:00:00");
  expect(clock).toBeInTheDocument();
});

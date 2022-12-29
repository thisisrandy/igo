import { render, act, screen } from "@testing-library/react";
import createMockStore from "redux-mock-store";
import { Provider } from "react-redux";
import { CONNECTED } from "../constants/StateKeys";
import ConnectionAlert from "../components/ConnectionAlert";
import { CONNECTION_ALERT_DELAY_MS } from "../constants/ConnectionSettings";

const mockStore = createMockStore([]);
const queryExpr = /Connection to the game server.*lost/;

test("alert not present when connected", () => {
  render(
    <Provider store={mockStore({ game: { [CONNECTED]: true } })}>
      <ConnectionAlert zIndex={1} />
    </Provider>
  );

  const alert = screen.queryByText(queryExpr);
  expect(alert).not.toBeInTheDocument();
});

test("alert present when disconnected", () => {
  jest.useFakeTimers();
  render(
    <Provider store={mockStore({ game: { [CONNECTED]: false } })}>
      <ConnectionAlert zIndex={1} />
    </Provider>
  );

  // there is a delay built into the display, so make sure to account for it
  let alert = screen.queryByText(queryExpr);
  expect(alert).not.toBeInTheDocument();
  act(() => {
    jest.advanceTimersByTime(CONNECTION_ALERT_DELAY_MS);
  });
  alert = screen.queryByText(queryExpr);
  expect(alert).toBeInTheDocument();
});

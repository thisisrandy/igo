import { render } from "@testing-library/react";
import { Provider } from "react-redux";
import createMockStore from "redux-mock-store";
import ConnectionManager from "../components/ConnectionManager";
import { WS_CONNECT } from "../constants/ActionTypes";
import { RECONNECT_INTERVAL_MS } from "../constants/ConnectionSettings";
import { CONNECTED } from "../constants/StateKeys";

const mockStore = createMockStore([]);

test("no reconnect attempts made when connected", () => {
  jest.useFakeTimers();
  const store = mockStore({ game: { [CONNECTED]: true } });
  render(
    <Provider store={store}>
      <ConnectionManager />
    </Provider>
  );

  jest.advanceTimersByTime(60000);
  expect(store.getActions().length).toBe(0);
});

test(`attempts to reconnect every ${
  RECONNECT_INTERVAL_MS / 1000
} seconds when disconnected`, () => {
  jest.useFakeTimers();
  const store = mockStore({ game: { [CONNECTED]: false } });
  render(
    <Provider store={store}>
      <ConnectionManager />
    </Provider>
  );

  const advanceBy = 60000;
  jest.advanceTimersByTime(advanceBy);
  expect(store.getActions().length).toBe(
    1 + Math.floor(advanceBy / RECONNECT_INTERVAL_MS)
  );
  expect(store.getActions().every((act) => act.type === WS_CONNECT)).toBe(true);
});

import { MESSAGE } from "../constants/StateKeys";
import createMockStore from "redux-mock-store";
import { act, render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import { CLEAR_MESSAGE } from "../constants/ActionTypes";
import Message from "../components/Message";

const mockStore = createMockStore([]);

function setUp(state) {
  const store = mockStore(state);
  render(
    <Provider store={store}>
      <Message zIndex={1} />
    </Provider>
  );

  return { store };
}

test("not open when message not set", () => {
  setUp({ game: {} });
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
});

test("to display when message is set and to clear message on close", () => {
  const { store } = setUp({ game: { [MESSAGE]: "hello" } });
  expect(screen.getByRole("dialog")).toBeInTheDocument();
  const button = screen.getByRole("button", { name: /okay/i });
  act(() => {
    button.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  });
  expect(store.getActions().length).toBe(1);
  expect(store.getActions()[0].type).toBe(CLEAR_MESSAGE);
});

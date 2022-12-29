import { CONNECTED, PAST_GAMES } from "../constants/StateKeys";
import createMockStore from "redux-mock-store";
import { act, render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import { TYPE } from "../constants/OutgoingMessageKeys";
import { JOIN_GAME } from "../constants/OutgoingMessageTypes";
import JoinResumeDialog from "../components/JoinResumeDialog";
import userEvent from "@testing-library/user-event";

const initialState = { game: { [CONNECTED]: true, [PAST_GAMES]: {} } };

const mockStore = createMockStore([]);

function setUp() {
  const store = mockStore(initialState);
  const joinResumeDialogOpen = true;
  const setJoinResumeDialogOpen = jest.fn();
  render(
    <Provider store={store}>
      <JoinResumeDialog
        {...{ joinResumeDialogOpen, setJoinResumeDialogOpen }}
      />
    </Provider>
  );

  return { store, setJoinResumeDialogOpen };
}

test("dispatches correct action and set closed when submit clicked", () => {
  const { store, setJoinResumeDialogOpen } = setUp();
  expect(screen.getByRole("dialog")).toBeInTheDocument();
  const input = screen.getByLabelText("Player key");
  expect(input).toBeInTheDocument();
  // NOTE: we need userEvent here because fireEvent doesn't seem to trigger
  // onInput, which we rely on in the component to record text changes
  // NOTE: arrowdown and enter below are needed to properly interact with the
  // auto-complete menu
  userEvent.type(input, "0123456789{arrowdown}{enter}");
  const submit = screen.getByRole("button", { name: "Submit" });
  expect(submit).toBeInTheDocument();
  act(() => {
    submit.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  });
  expect(setJoinResumeDialogOpen.mock.calls.length).toBe(1);
  expect(store.getActions().length).toBe(1);
  expect(store.getActions()[0].payload[TYPE]).toBe(JOIN_GAME);
});

test("submit disabled when input is wrong length", () => {
  setUp();
  const input = screen.getByLabelText("Player key");
  userEvent.type(input, "01234");
  const submit = screen.getByRole("button", { name: "Submit" });
  expect(submit.disabled).toBe(true);
});

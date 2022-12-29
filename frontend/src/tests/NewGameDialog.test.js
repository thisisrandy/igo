import { CONNECTED } from "../constants/StateKeys";
import createMockStore from "redux-mock-store";
import { act, render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import { TYPE } from "../constants/OutgoingMessageKeys";
import { NEW_GAME } from "../constants/OutgoingMessageTypes";
import userEvent from "@testing-library/user-event";
import NewGameDialog from "../components/NewGameDialog";
import { within } from "@testing-library/react";

const initialState = { game: { [CONNECTED]: true } };

const mockStore = createMockStore([]);

function setUp() {
  const store = mockStore(initialState);
  const [newGameDialogOpen, setNewGameDialogOpen] = [true, jest.fn()];
  render(
    <Provider store={store}>
      <NewGameDialog {...{ newGameDialogOpen, setNewGameDialogOpen }} />
    </Provider>
  );

  return { store, setNewGameDialogOpen };
}

test("dispatches correct action and set closed when submit clicked", () => {
  const { store, setNewGameDialogOpen } = setUp();
  expect(screen.getByRole("dialog")).toBeInTheDocument();
  const submit = screen.getByRole("button", { name: "Submit" });
  expect(submit).toBeInTheDocument();
  act(() => {
    submit.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  });
  expect(setNewGameDialogOpen.mock.calls.length).toBe(1);
  expect(store.getActions().length).toBe(1);
  expect(store.getActions()[0].payload[TYPE]).toBe(NEW_GAME);
});

test("submit disabled when komi is invalid", () => {
  setUp();
  const komiFieldSet = screen
    .getByText(/komi/i, { selectfor: "legend" })
    .closest("div");
  const input = within(komiFieldSet).getByRole("spinbutton");
  // NOTE: we need userEvent here because fireEvent doesn't seem to trigger
  // onChange, which we rely on in the component to record text changes
  userEvent.type(input, "4.1");
  const submit = screen.getByRole("button", { name: "Submit" });
  expect(submit.disabled).toBe(true);
});

import { act, render, screen } from "@testing-library/react";
import TopBar from "../components/TopBar";

test("renders TopBar", () => {
  render(<TopBar />);
  const topBar = screen.getByText("囲碁 - igo");
  expect(topBar).toBeInTheDocument();
});

test("drawer is hidden and appears on button click", () => {
  render(<TopBar />);
  expect(screen.queryByText("How do I play?")).toBeNull();
  expect(screen.queryByText("Show me the code!")).toBeNull();
  const button = document.querySelector("button");
  expect(button).toBeInTheDocument();
  act(() => {
    button.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  });
  const playButton = screen.getByText("How do I play?");
  const codeButton = screen.getByText("Show me the code!");
  expect(playButton).toBeInTheDocument();
  expect(codeButton).toBeInTheDocument();
});

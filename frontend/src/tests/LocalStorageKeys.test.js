import * as keys from "../constants/LocalStorageKeys";

test("all keys are unique", () => {
  expect(Object.keys(keys).length).toBe(new Set(Object.values(keys)).size);
});

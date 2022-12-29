import * as ids from "../constants/Ids";

test("all ids are unique", () => {
  expect(Object.keys(ids).length).toBe(new Set(Object.values(ids)).size);
});

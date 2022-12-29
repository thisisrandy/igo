import {
  breakLongWords,
  capitalizeFirstLetter,
  getDaysSince,
  truncate,
} from "../utils";

describe("test capitalizeFirstLetter", () => {
  test("capitalizes the first letter", () => {
    expect(capitalizeFirstLetter("foo")).toBe("Foo");
  });

  test("doesn't change other letters' capitalization", () => {
    expect(capitalizeFirstLetter("FoO")).toBe("FoO");
  });
});

describe("test breakLongWords", () => {
  test("correctly breaks long words", () => {
    expect(breakLongWords("hello world", 4)).toBe("hel- lo wor- ld");
  });
});

describe("test daysSince", () => {
  test("returns correct number of days having passed", () => {
    expect(
      getDaysSince(
        new Date("1/1/20 11:59:00 PM"),
        new Date("1/2/20 12:00:00 AM")
      )
    ).toBe(1);
    expect(
      getDaysSince(
        new Date("1/1/20 11:59:00 PM"),
        new Date("1/2/20 10:05:44 PM")
      )
    ).toBe(1);
    expect(
      getDaysSince(
        new Date("1/1/20 11:59:00 AM"),
        new Date("1/1/20 12:00:00 PM")
      )
    ).toBe(0);
    expect(
      getDaysSince(
        new Date("11/1/20 1:00:00 PM"),
        new Date("12/2/20 10:00:00 AM")
      )
    ).toBe(31);
  });

  test("works with millisecond inputs", () => {
    expect(
      getDaysSince(
        new Date("1/1/20 11:59:00 PM").valueOf(),
        new Date("1/2/20 12:00:00 AM").valueOf()
      )
    ).toBe(1);
    expect(
      getDaysSince(
        new Date("11/1/20 1:00:00 PM").valueOf(),
        new Date("12/2/20 10:00:00 AM").valueOf()
      )
    ).toBe(31);
  });
});

describe("test truncate", () => {
  test("returns original string if less than or equal to maxLength", () => {
    expect(truncate("foobar", 6, false)).toBe("foobar");
    expect(truncate("foobar", 7, false)).toBe("foobar");
  });

  test("add ellipsis when string is too long", () => {
    expect(truncate("foobar", 5)).toBe("fo...");
  });
});

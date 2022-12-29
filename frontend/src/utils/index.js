export function capitalizeFirstLetter(
  [first, ...rest],
  locale = navigator.language
) {
  return [first.toLocaleUpperCase(locale), ...rest].join("");
}

/**
 * Assuming that lines are wrapped at `lineWidth` in the display, break words
 * longer than `lineWidth` at the appropriate points, ignoring language
 * conventions and observing only length, with a dash. This is only perfect
 * given a fixed-width font; any variable-length font's width cannot be reliably
 * measured via character length
 */
export function breakLongWords(text, lineWidth) {
  if (!Number.isInteger(lineWidth) || lineWidth <= 1) {
    console.error(
      `Bad width ${lineWidth} supplied to breakLongWords. Giving up`
    );
    return text;
  }

  const res = [];
  let curWidth = 0;
  for (let word of text.split(/\s+/)) {
    while (word.length > lineWidth) {
      // we are appending a dash, so need at least 2 chars to fill
      if (lineWidth - curWidth > 1) {
        res.push(`${word.slice(0, lineWidth - curWidth - 1)}-`);
        word = word.slice(lineWidth - curWidth - 1);
      }
      curWidth = 0;
    }
    if (lineWidth - curWidth < word.length) {
      curWidth = 0;
    }
    res.push(word);
    curWidth += word.length + 1;
  }

  return res.join(" ");
}

/**
 * Return the number of whole days that have passed between time and now. For
 * example, if time corresponds to 1/1/20 11:59 PM and it is now 1/2/20 12:00AM,
 * the return value is 1, because although only 1 minute has passed, the day (in
 * local time) has changed
 */
export function getDaysSince(time, now = Date.now()) {
  if (isNaN(time))
    throw new TypeError(`time (${time}) is not a number or Date`);
  if (isNaN(now)) throw new TypeError(`now (${now}) is not a number or Date`);

  const midnight = (t) => {
    t = t instanceof Date ? t : new Date(t);
    return new Date(t.toDateString()).valueOf();
  };

  // 24 * 60 * 60 * 1000 = 86400000
  return Math.floor((midnight(now) - midnight(time)) / 86400000);
}

/**
 * Truncate string to a maximum length of maxLength and add an ellipsis if any
 * text was truncated. maxLength must be at least 4 to allow for one character
 * plus an ellipsis
 */
export function truncate(string, maxLength) {
  if (maxLength < 4)
    throw new RangeError(`maxLength (${maxLength}) must be >= 4`);

  return string.length <= maxLength
    ? string
    : `${string.slice(0, maxLength - 3)}...`;
}

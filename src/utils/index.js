export function capitalizeFirstLetter(
  [first, ...rest],
  locale = navigator.language
) {
  return [first.toLocaleUpperCase(locale), ...rest].join("");
}

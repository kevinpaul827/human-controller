const ARROW_KEYS = new Set([
  "up",
  "down",
  "left",
  "right",
  "arrowup",
  "arrowdown",
  "arrowleft",
  "arrowright",
]);

export const isArrowKey = (keyName: string) =>
  ARROW_KEYS.has(keyName.toLowerCase());

export const BINDABLE_KEYS = [
  "ArrowUp",
  "ArrowDown",
  "ArrowLeft",
  "ArrowRight",
  "Space",
  "Shift",
  "Ctrl",
  "E",
  "Q",
  "Z",
] as const;

export const keyLabel = (keyName: string) => {
  const normalized = keyName.toLowerCase();
  if (ARROW_KEYS.has(normalized)) {
    const direction = normalized.replace("arrow", "");
    return `${direction.charAt(0).toUpperCase()}${direction.slice(1)} Arrow`;
  }
  return keyName;
};

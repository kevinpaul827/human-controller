const KEY_LABELS: Record<string, string> = {
  ArrowUp: "↑  Up Arrow",
  ArrowDown: "↓  Down Arrow",
  ArrowLeft: "←  Left Arrow",
  ArrowRight: "→  Right Arrow",
  Space: "Space",
};

export const normaliseKey = (key: string) => {
  if (key === " ") {
    return "Space";
  }
  if (key.length === 1) {
    return key.toUpperCase();
  }
  return key;
};

export const formatKey = (key: string) => KEY_LABELS[key] ?? key;

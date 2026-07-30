export const initialsOf = (name: string) =>
  name
    .trim()
    .split(/\s+/)
    .map((part) => part[0] ?? "")
    .slice(0, 2)
    .join("")
    .toUpperCase() || "?";

export const relativeTime = (iso: string | null | undefined) => {
  if (!iso) {
    return null;
  }

  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) {
    return null;
  }

  const days = Math.floor((Date.now() - then) / 86_400_000);
  if (days <= 0) {
    return "today";
  }
  if (days === 1) {
    return "yesterday";
  }
  if (days < 30) {
    return `${days} days ago`;
  }
  const months = Math.floor(days / 30);
  return months === 1 ? "a month ago" : `${months} months ago`;
};

function timeago(current) {
  const isoString = current.replace(" ", "T").slice(0, 23) + "Z";
  const currentUTC = new Date(isoString);

  const now = new Date();
  const diff = now - currentUTC;

  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(diff / (1000 * 60));
  const hours = Math.floor(diff / (1000 * 60 * 60));
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));

  if (seconds < 60) {
    return "less than a minute ago";
  } else if (minutes < 60) {
    return `about ${minutes} minute${minutes === 1 ? "" : "s"} ago`;
  } else if (hours < 24) {
    return `about ${hours} hour${hours === 1 ? "" : "s"} ago`;
  } else {
    return `on ${currentUTC.toLocaleString(undefined, {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
      timeZone: "UTC",
    })}`;
  }
}

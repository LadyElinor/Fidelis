export function wilsonInterval(num, den, z = 1.96) {
  const n = Number(den);
  const k = Number(num);
  if (!Number.isFinite(n) || n <= 0) return { value: null, low: null, high: null };
  const phat = k / n;
  if (!Number.isFinite(phat)) return { value: null, low: null, high: null };
  const z2 = z * z;
  const denom = 1 + z2 / n;
  const center = (phat + z2 / (2 * n)) / denom;
  const rad = (z / denom) * Math.sqrt((phat * (1 - phat) + z2 / (4 * n)) / n);
  return {
    value: phat,
    low: Math.max(0, center - rad),
    high: Math.min(1, center + rad),
  };
}

export function rateDelta(curr, prev) {
  // prev: {value, low, high}; curr: same
  if (curr?.value == null || prev?.value == null) return null;
  const delta = curr.value - prev.value;
  // conservative band: combine half-widths
  const prevHw = (prev.high - prev.low) / 2;
  const currHw = (curr.high - curr.low) / 2;
  const band = (Number.isFinite(prevHw) ? prevHw : 0) + (Number.isFinite(currHw) ? currHw : 0);
  return { delta, approx_band: band };
}

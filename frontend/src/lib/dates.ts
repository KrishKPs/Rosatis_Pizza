export function priorPeriod(start: string, end: string): { start: string; end: string } {
  const s = new Date(start + "T00:00:00");
  const e = new Date(end + "T00:00:00");
  const days = Math.round((e.getTime() - s.getTime()) / 86400000) + 1;
  const prevEnd = new Date(s.getTime() - 86400000);
  const prevStart = new Date(prevEnd.getTime() - (days - 1) * 86400000);
  return { start: prevStart.toISOString().slice(0, 10), end: prevEnd.toISOString().slice(0, 10) };
}

export function pctDelta(current: number, prior: number): number | null {
  if (!prior) return null;
  return ((current - prior) / Math.abs(prior)) * 100;
}

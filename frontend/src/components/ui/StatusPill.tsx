const CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  ok: { label: "In stock", color: "var(--profit)", bg: "var(--profit-bg)" },
  low: { label: "Time to reorder", color: "var(--accent)", bg: "var(--accent-bg)" },
  out: { label: "Out of stock", color: "var(--loss)", bg: "var(--loss-bg)" },
  uncounted: { label: "Not counted yet", color: "var(--text-tertiary)", bg: "var(--surface-3)" },
};

export function StatusPill({ status }: { status: "ok" | "low" | "out" | "uncounted" }) {
  const cfg = CONFIG[status];
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 font-mono text-[11.5px] font-medium"
      style={{ color: cfg.color, background: cfg.bg }}
    >
      <span className="h-1.5 w-1.5 rounded-full" style={{ background: cfg.color }} />
      {cfg.label}
    </span>
  );
}

export function ProfitPill({ value }: { value: number }) {
  const positive = value > 0;
  const zero = value === 0;
  return (
    <span
      className="inline-flex items-center gap-1.5 font-mono text-[12px] font-medium"
      style={{ color: zero ? "var(--text-tertiary)" : positive ? "var(--profit)" : "var(--loss)" }}
    >
      <span
        className="h-1.5 w-1.5 rounded-full"
        style={{ background: zero ? "var(--text-tertiary)" : positive ? "var(--profit)" : "var(--loss)" }}
      />
      {positive ? "Makes money" : zero ? "Breaks even" : "Loses money"}
    </span>
  );
}

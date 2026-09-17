export function StatCard({
  label,
  value,
  delta,
  hero = false,
  tone = "neutral",
}: {
  label: string;
  value: string;
  delta?: number | null;
  hero?: boolean;
  tone?: "neutral" | "profit" | "loss";
}) {
  const valueColor =
    tone === "profit" ? "text-profit" : tone === "loss" ? "text-loss" : "text-text-primary";

  return (
    <div
      className={`rounded-xl p-4 sm:p-5 ${
        hero
          ? "bg-gradient-to-br from-accent/[0.14] to-surface-1 border border-accent/30"
          : "bg-surface-1 border border-border"
      }`}
    >
      <div className="font-mono text-[12px] tracking-tight text-text-secondary">{label}</div>
      <div
        className={`mt-2 font-mono leading-tight font-semibold ${
          hero ? "text-[25px] text-accent sm:text-[32px]" : `text-[17px] sm:text-[20px] ${valueColor}`
        }`}
      >
        {value}
      </div>
      {delta !== undefined && delta !== null && !Number.isNaN(delta) && (
        <div
          className={`mt-1.5 font-mono text-[12px] ${
            delta > 0 ? "text-profit" : delta < 0 ? "text-loss" : "text-text-tertiary"
          }`}
        >
          {delta > 0 ? "▲" : delta < 0 ? "▼" : "–"} {Math.abs(delta).toFixed(1)}% vs prior period
        </div>
      )}
    </div>
  );
}

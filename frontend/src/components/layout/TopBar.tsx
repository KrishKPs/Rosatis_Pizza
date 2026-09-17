import type { ReactNode } from "react";
import { useFilters } from "../../context/FiltersContext";

export function TopBar({
  title,
  subtitle,
  showFilters = true,
  right,
}: {
  title: string;
  subtitle?: string;
  showFilters?: boolean;
  right?: ReactNode;
}) {
  const { meta, start, end, channel, setStart, setEnd, setChannel, resetRange } = useFilters();

  return (
    <div className="flex flex-col gap-3 border-b border-border bg-surface-2 px-4 py-3 md:flex-row md:items-center md:justify-between md:px-8 md:py-4">
      <div>
        <h1 className="font-mono text-[17px] font-semibold text-text-primary">{title}</h1>
        {subtitle && <p className="mt-0.5 text-[13px] text-text-secondary">{subtitle}</p>}
      </div>
      <div className="flex flex-wrap items-center gap-2 md:gap-3">
        {right}
        {showFilters && meta && (
          <>
            <div className="flex items-center gap-1.5 rounded-lg border border-border bg-surface-1 px-2.5 py-1.5">
              <input
                type="date"
                value={start}
                min={meta.date_min}
                max={end}
                onChange={(e) => setStart(e.target.value)}
                className="bg-transparent font-mono text-[12.5px] text-text-primary outline-none [color-scheme:dark]"
              />
              <span className="text-text-tertiary">–</span>
              <input
                type="date"
                value={end}
                min={start}
                max={meta.date_max}
                onChange={(e) => setEnd(e.target.value)}
                className="bg-transparent font-mono text-[12.5px] text-text-primary outline-none [color-scheme:dark]"
              />
            </div>
            <select
              value={channel}
              onChange={(e) => setChannel(e.target.value)}
              className="rounded-lg border border-border bg-surface-1 px-3 py-2 font-mono text-[12.5px] text-text-primary outline-none"
            >
              <option value="">All channels</option>
              {meta.channels.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
            <button
              onClick={resetRange}
              className="font-mono text-[12px] text-text-tertiary hover:text-text-secondary"
            >
              Reset
            </button>
          </>
        )}
      </div>
    </div>
  );
}

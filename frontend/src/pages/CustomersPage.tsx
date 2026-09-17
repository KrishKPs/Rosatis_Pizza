import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { CustomerRow, CustomerSummary } from "../api/types";
import { useFilters } from "../context/FiltersContext";
import { TopBar } from "../components/layout/TopBar";
import { Card } from "../components/ui/Card";
import { StatCard } from "../components/ui/StatCard";
import { money, pct, shortDate } from "../lib/format";

type SortBy = "total_spent" | "order_count" | "loyalty_points";

export function CustomersPage() {
  const { start, end, channel, refreshKey } = useFilters();
  const [summary, setSummary] = useState<CustomerSummary | null>(null);
  const [all, setAll] = useState<CustomerRow[]>([]);
  const [sortBy, setSortBy] = useState<SortBy>("total_spent");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!start || !end) return;
    setLoading(true);
    Promise.all([
      api.customerSummary({ start, end, channel: channel || undefined }),
      api.customers(),
    ]).then(([s, c]) => {
      setSummary(s);
      setAll(c);
      setLoading(false);
    });
  }, [start, end, channel, refreshKey]);

  const sorted = [...all].sort((a, b) => b[sortBy] - a[sortBy]).slice(0, 15);
  const newCount = summary ? summary.total_customers - summary.repeat_customers : 0;

  return (
    <div>
      <TopBar title="Customers & Loyalty" subtitle="Who keeps coming back?" />
      <div className="px-4 py-4 md:px-8 md:py-6">
        {loading || !summary ? (
          <div className="py-24 text-center font-mono text-text-tertiary">Loading…</div>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4 lg:gap-4">
              <StatCard label="Active customers" value={summary.total_customers.toString()} hero />
              <StatCard label="Repeat rate" value={pct(summary.repeat_rate_pct)} tone="profit" />
              <StatCard label="Average visits" value={summary.avg_visits.toFixed(1)} />
              <StatCard label="Loyalty points outstanding" value={summary.loyalty_points_outstanding.toLocaleString()} />
            </div>

            <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
              <Card title="New vs. repeat">
                <div className="flex h-3 overflow-hidden rounded-full bg-surface-3">
                  <div
                    className="h-full bg-profit"
                    style={{ width: `${summary.repeat_rate_pct}%` }}
                    title="Repeat customers"
                  />
                  <div
                    className="h-full bg-accent-dim"
                    style={{ width: `${100 - summary.repeat_rate_pct}%` }}
                    title="New customers"
                  />
                </div>
                <div className="mt-3 flex justify-between font-mono text-[12px]">
                  <span className="text-profit">{summary.repeat_customers} repeat</span>
                  <span className="text-text-tertiary">{newCount} new</span>
                </div>
              </Card>

              <Card title="Loyalty standings" subtitle="Sort top customers" className="lg:col-span-2" emphasis>
                <div className="mb-3 flex gap-2">
                  {(
                    [
                      ["total_spent", "By spend"],
                      ["order_count", "By visits"],
                      ["loyalty_points", "By points"],
                    ] as [SortBy, string][]
                  ).map(([key, label]) => (
                    <button
                      key={key}
                      onClick={() => setSortBy(key)}
                      className={`rounded-full px-3 py-1 font-mono text-[11.5px] ${
                        sortBy === key
                          ? "bg-accent/[0.18] text-accent"
                          : "bg-surface-3 text-text-tertiary hover:text-text-secondary"
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </div>
                <div className="overflow-x-auto"><table className="w-full min-w-[520px]">
                  <thead>
                    <tr className="border-b border-border text-left font-mono text-[11px] text-text-tertiary">
                      <th className="pb-2 font-medium">Customer</th>
                      <th className="pb-2 font-medium">Since</th>
                      <th className="pb-2 text-right font-medium">Visits</th>
                      <th className="pb-2 text-right font-medium">Spent</th>
                      <th className="pb-2 text-right font-medium">Points</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sorted.map((c) => (
                      <tr key={c.customer_id} className="border-b border-border/60 last:border-0 hover:bg-surface-2">
                        <td className="py-2 text-[13px] text-text-primary">{c.name}</td>
                        <td className="py-2 font-mono text-[11.5px] text-text-tertiary">
                          {shortDate(c.first_order_date)}
                        </td>
                        <td className="py-2 text-right font-mono text-[12.5px] text-text-secondary">{c.order_count}</td>
                        <td className="py-2 text-right font-mono text-[12.5px] text-text-primary">
                          {money(c.total_spent)}
                        </td>
                        <td className="py-2 text-right font-mono text-[12.5px] text-accent">{c.loyalty_points}</td>
                      </tr>
                    ))}
                  </tbody>
                </table></div>
              </Card>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { ChannelBreakdown, OrderRow } from "../api/types";
import { useFilters } from "../context/FiltersContext";
import { TopBar } from "../components/layout/TopBar";
import { Card } from "../components/ui/Card";
import { StatCard } from "../components/ui/StatCard";
import { dateTime, money, pct } from "../lib/format";

export function OrdersPage() {
  const { start, end, channel, refreshKey } = useFilters();
  const [orders, setOrders] = useState<OrderRow[]>([]);
  const [channels, setChannels] = useState<ChannelBreakdown[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!start || !end) return;
    const f = { start, end, channel: channel || undefined };
    setLoading(true);
    Promise.all([api.orders(f, 60), api.ordersByChannel(f)]).then(([o, c]) => {
      setOrders(o);
      setChannels(c);
      setLoading(false);
    });
  }, [start, end, channel, refreshKey]);

  return (
    <div>
      <TopBar title="Orders & Channels" subtitle="What's coming in?" />
      <div className="px-4 py-4 md:px-8 md:py-6">
        {loading ? (
          <div className="py-24 text-center font-mono text-text-tertiary">Loading…</div>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:gap-4 xl:grid-cols-6">
              {channels.map((c) => (
                <StatCard
                  key={c.channel_id}
                  label={`${c.channel_name} — keeps ${pct(c.net_margin_pct)}`}
                  value={money(c.net_profit)}
                  tone={c.net_margin_pct < 55 ? "loss" : "profit"}
                />
              ))}
            </div>

            <div className="mt-4">
              <Card
                title="Recent orders"
                subtitle="Same-size orders net very different profit depending on channel and deal"
                emphasis
              >
                <div className="max-h-[560px] overflow-x-auto overflow-y-auto">
                  <table className="w-full min-w-[760px]">
                    <thead className="sticky top-0 bg-surface-1">
                      <tr className="border-b border-border text-left font-mono text-[11px] text-text-tertiary">
                        <th className="pb-2 font-medium">Time</th>
                        <th className="pb-2 font-medium">Channel</th>
                        <th className="pb-2 font-medium">Customer</th>
                        <th className="pb-2 font-medium">Items</th>
                        <th className="pb-2 font-medium">Deal</th>
                        <th className="pb-2 text-right font-medium">Revenue</th>
                        <th className="pb-2 text-right font-medium">App fee</th>
                        <th className="pb-2 text-right font-medium">Net profit</th>
                      </tr>
                    </thead>
                    <tbody>
                      {orders.map((o) => (
                        <tr key={o.order_id} className="border-b border-border/60 last:border-0 hover:bg-surface-2">
                          <td className="whitespace-nowrap py-2 font-mono text-[11.5px] text-text-tertiary">
                            {dateTime(o.timestamp)}
                          </td>
                          <td className="py-2 font-mono text-[12px] text-text-secondary">{o.channel_name}</td>
                          <td className="py-2 text-[13px] text-text-primary">{o.customer_name}</td>
                          <td className="max-w-[240px] truncate py-2 text-[12.5px] text-text-secondary" title={o.items.map((i) => `${i.qty}× ${i.name}`).join(", ")}>
                            {o.items.map((i) => i.name).join(", ")}
                          </td>
                          <td className="py-2 font-mono text-[11.5px] text-accent">{o.deal_name ?? "—"}</td>
                          <td className="py-2 text-right font-mono text-[12.5px] text-text-primary">
                            {money(o.revenue, { cents: true })}
                          </td>
                          <td className="py-2 text-right font-mono text-[12.5px] text-text-tertiary">
                            {o.commission_paid > 0 ? money(o.commission_paid, { cents: true }) : "—"}
                          </td>
                          <td
                            className="py-2 text-right font-mono text-[12.5px] font-medium"
                            style={{ color: o.net_profit >= 0 ? "var(--profit)" : "var(--loss)" }}
                          >
                            {money(o.net_profit, { cents: true })}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

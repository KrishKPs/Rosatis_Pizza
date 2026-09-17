import { useEffect, useState } from "react";
import {
  Area,
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  BarChart,
} from "recharts";
import { api } from "../api/client";
import type {
  CategoryBreakdown,
  ChannelBreakdown,
  HeatCell,
  SalesSummary,
  TimeseriesPoint,
  TopItem,
} from "../api/types";
import { useFilters } from "../context/FiltersContext";
import { TopBar } from "../components/layout/TopBar";
import { Card } from "../components/ui/Card";
import { StatCard } from "../components/ui/StatCard";
import { compactMoney, hourLabel, money, pct, shortDate, weekdayLabel } from "../lib/format";
import { CATEGORY_COLORS, theme } from "../lib/theme";
import { pctDelta, priorPeriod } from "../lib/dates";

export function SalesPage() {
  const { start, end, channel, refreshKey } = useFilters();
  const [summary, setSummary] = useState<SalesSummary | null>(null);
  const [priorSummary, setPriorSummary] = useState<SalesSummary | null>(null);
  const [series, setSeries] = useState<TimeseriesPoint[]>([]);
  const [byCategory, setByCategory] = useState<CategoryBreakdown[]>([]);
  const [byChannel, setByChannel] = useState<ChannelBreakdown[]>([]);
  const [heat, setHeat] = useState<HeatCell[]>([]);
  const [topItems, setTopItems] = useState<TopItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!start || !end) return;
    const f = { start, end, channel: channel || undefined };
    const prior = priorPeriod(start, end);
    setLoading(true);
    Promise.all([
      api.salesSummary(f),
      api.salesSummary({ ...prior, channel: f.channel }),
      api.salesTimeseries(f),
      api.salesByCategory(f),
      api.salesByChannel(f),
      api.salesHeatmap(f),
      api.salesTopItems(f, 8),
    ]).then(([s, ps, ts, cat, chan, hm, top]) => {
      setSummary(s);
      setPriorSummary(ps);
      setSeries(ts);
      setByCategory(cat);
      setByChannel(chan);
      setHeat(hm);
      setTopItems(top);
      setLoading(false);
    });
  }, [start, end, channel, refreshKey]);

  const maxHeat = Math.max(1, ...heat.map((h) => h.orders));

  return (
    <div>
      <TopBar title="Sales & Analytics" subtitle="How's business?" />
      <div className="px-4 py-4 md:px-8 md:py-6">
        {loading || !summary ? (
          <div className="py-24 text-center font-mono text-text-tertiary">Loading…</div>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4 lg:gap-4">
              <StatCard
                label="Net profit — what you actually keep"
                value={money(summary.net_profit)}
                delta={priorSummary ? pctDelta(summary.net_profit, priorSummary.net_profit) : null}
                hero
              />
              <StatCard
                label="Revenue"
                value={money(summary.revenue)}
                delta={priorSummary ? pctDelta(summary.revenue, priorSummary.revenue) : null}
              />
              <StatCard
                label="Orders"
                value={summary.order_count.toLocaleString()}
                delta={priorSummary ? pctDelta(summary.order_count, priorSummary.order_count) : null}
              />
              <StatCard
                label="Average order value"
                value={money(summary.avg_order_value, { cents: true })}
                delta={
                  priorSummary ? pctDelta(summary.avg_order_value, priorSummary.avg_order_value) : null
                }
              />
            </div>

            <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
              <Card
                title="Revenue vs. what you actually keep"
                subtitle="The gap between the two is food cost and app fees"
                className="lg:col-span-2"
                emphasis
              >
                <ResponsiveContainer width="100%" height={280}>
                  <ComposedChart data={series}>
                    <CartesianGrid stroke={theme.border} vertical={false} />
                    <XAxis
                      dataKey="date"
                      tickFormatter={shortDate}
                      stroke={theme.textTertiary}
                      tick={{ fontFamily: "IBM Plex Mono", fontSize: 11 }}
                      tickLine={false}
                      axisLine={{ stroke: theme.border }}
                    />
                    <YAxis
                      tickFormatter={compactMoney}
                      stroke={theme.textTertiary}
                      tick={{ fontFamily: "IBM Plex Mono", fontSize: 11 }}
                      tickLine={false}
                      axisLine={false}
                      width={54}
                    />
                    <Tooltip
                      contentStyle={{
                        background: theme.surface2,
                        border: `1px solid ${theme.border}`,
                        borderRadius: 8,
                        fontFamily: "IBM Plex Mono",
                        fontSize: 12,
                      }}
                      labelFormatter={(l) => shortDate(String(l))}
                      formatter={(v) => money(Number(v))}
                    />
                    <Legend wrapperStyle={{ fontFamily: "IBM Plex Mono", fontSize: 11.5 }} />
                    <Area
                      type="monotone"
                      dataKey="revenue"
                      name="Revenue"
                      stroke={theme.accentDim}
                      fill={theme.accentDim}
                      fillOpacity={0.14}
                      strokeWidth={1.5}
                      isAnimationActive={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="net_profit"
                      name="Net profit"
                      stroke={theme.profit}
                      strokeWidth={2.25}
                      dot={false}
                      isAnimationActive={false}
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </Card>

              <Card title="Sales by category">
                <div className="flex flex-col gap-2.5">
                  {byCategory.map((c, i) => {
                    const max = Math.max(...byCategory.map((x) => x.revenue));
                    return (
                      <div key={c.category}>
                        <div className="mb-1 flex items-center justify-between font-mono text-[12px]">
                          <span className="text-text-secondary">{c.category}</span>
                          <span className="text-text-primary">{money(c.revenue)}</span>
                        </div>
                        <div className="h-1.5 rounded-full bg-surface-3">
                          <div
                            className="h-1.5 rounded-full"
                            style={{
                              width: `${(c.revenue / max) * 100}%`,
                              background: CATEGORY_COLORS[i % CATEGORY_COLORS.length],
                            }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </Card>
            </div>

            <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
              <Card
                title="Sales & profit by channel"
                subtitle="Same order, different money — third-party apps take a cut"
                className="lg:col-span-2"
                emphasis
              >
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={byChannel} margin={{ left: 0, right: 12 }}>
                    <CartesianGrid stroke={theme.border} vertical={false} />
                    <XAxis
                      dataKey="channel_name"
                      stroke={theme.textTertiary}
                      tick={{ fontFamily: "IBM Plex Mono", fontSize: 10.5 }}
                      tickLine={false}
                      axisLine={{ stroke: theme.border }}
                      interval={0}
                      angle={-12}
                      textAnchor="end"
                      height={50}
                    />
                    <YAxis
                      tickFormatter={compactMoney}
                      stroke={theme.textTertiary}
                      tick={{ fontFamily: "IBM Plex Mono", fontSize: 11 }}
                      tickLine={false}
                      axisLine={false}
                      width={54}
                    />
                    <Tooltip
                      contentStyle={{
                        background: theme.surface2,
                        border: `1px solid ${theme.border}`,
                        borderRadius: 8,
                        fontFamily: "IBM Plex Mono",
                        fontSize: 12,
                      }}
                      formatter={(v, name) => [money(Number(v)), String(name)]}
                    />
                    <Legend wrapperStyle={{ fontFamily: "IBM Plex Mono", fontSize: 11.5 }} />
                    <Bar dataKey="revenue" name="Revenue" fill={theme.accentDim} radius={[4, 4, 0, 0]} isAnimationActive={false} />
                    <Bar dataKey="net_profit" name="What you keep" fill={theme.profit} radius={[4, 4, 0, 0]} isAnimationActive={false} />
                  </BarChart>
                </ResponsiveContainer>
                <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1 font-mono text-[11.5px] text-text-tertiary">
                  {byChannel.map((c) => (
                    <span key={c.channel_id}>
                      {c.channel_name}: keeps {pct(c.net_margin_pct)}
                      {c.commission_pct > 0 && ` (app fee ${pct(c.commission_pct, 0)})`}
                    </span>
                  ))}
                </div>
              </Card>

              <Card title="Busiest days & times" subtitle="Orders by day and hour">
                <div className="flex flex-col gap-1">
                  {Array.from({ length: 7 }, (_, wd) => (
                    <div key={wd} className="flex items-center gap-1">
                      <span className="w-8 shrink-0 font-mono text-[10.5px] text-text-tertiary">
                        {weekdayLabel(wd)}
                      </span>
                      <div className="flex flex-1 gap-[3px]">
                        {[11, 12, 13, 17, 18, 19, 20].map((hr) => {
                          const cell = heat.find((h) => h.weekday === wd && h.hour === hr);
                          const intensity = cell ? cell.orders / maxHeat : 0;
                          return (
                            <div
                              key={hr}
                              title={`${weekdayLabel(wd)} ${hourLabel(hr)}: ${cell?.orders ?? 0} orders`}
                              className="h-4 flex-1 rounded-sm"
                              style={{
                                background:
                                  intensity === 0 ? theme.surface3 : `rgba(224,145,47,${0.15 + intensity * 0.75})`,
                              }}
                            />
                          );
                        })}
                      </div>
                    </div>
                  ))}
                  <div className="mt-1 flex gap-1 pl-9 font-mono text-[10px] text-text-tertiary">
                    {[11, 12, 13, 17, 18, 19, 20].map((hr) => (
                      <span key={hr} className="flex-1 text-center">
                        {hourLabel(hr)}
                      </span>
                    ))}
                  </div>
                </div>
              </Card>
            </div>

            <div className="mt-4">
              <Card title="Top-selling items">
                <div className="overflow-x-auto"><table className="w-full min-w-[520px]">
                  <thead>
                    <tr className="border-b border-border text-left font-mono text-[11px] text-text-tertiary">
                      <th className="pb-2 font-medium">Item</th>
                      <th className="pb-2 font-medium">Category</th>
                      <th className="pb-2 text-right font-medium">Qty sold</th>
                      <th className="pb-2 text-right font-medium">Revenue</th>
                    </tr>
                  </thead>
                  <tbody>
                    {topItems.map((item) => (
                      <tr key={item.item_id} className="border-b border-border/60 last:border-0">
                        <td className="py-2 text-[13px] text-text-primary">{item.name}</td>
                        <td className="py-2 font-mono text-[12px] text-text-tertiary">{item.category}</td>
                        <td className="py-2 text-right font-mono text-[12.5px] text-text-secondary">
                          {item.qty_sold}
                        </td>
                        <td className="py-2 text-right font-mono text-[12.5px] text-text-primary">
                          {money(item.revenue)}
                        </td>
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

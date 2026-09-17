import { useEffect, useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api/client";
import type { InventoryItem, UsageDay } from "../api/types";
import { useFilters } from "../context/FiltersContext";
import { TopBar } from "../components/layout/TopBar";
import { Card } from "../components/ui/Card";
import { StatCard } from "../components/ui/StatCard";
import { StatusPill } from "../components/ui/StatusPill";
import { money, shortDate } from "../lib/format";
import { theme } from "../lib/theme";
import { InventoryCountPanel } from "./InventoryCountPanel";

export function InventoryPage() {
  const { refreshKey } = useFilters();
  const [view, setView] = useState<"overview" | "count">("overview");
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [kpis, setKpis] = useState({ items_low_or_out: 0, items_out: 0, total_inventory_value: 0 });
  const [usage, setUsage] = useState<UsageDay[]>([]);
  const [selectedIngredient, setSelectedIngredient] = useState<string>("dough");
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<Record<string, string>>({});

  const load = () => {
    setLoading(true);
    Promise.all([api.inventory(), api.inventoryUsage(14)]).then(([inv, u]) => {
      setItems(inv.items);
      setKpis(inv.kpis);
      setUsage(u);
      setLoading(false);
    });
  };

  useEffect(load, [refreshKey]);

  const alerts = items.filter((i) => i.low_stock);
  const usageSeries = useMemo(
    () => usage.map((u) => ({ date: u.date, qty: Math.round((u.usage[selectedIngredient] ?? 0) * 10) / 10 })),
    [usage, selectedIngredient],
  );

  const saveCost = async (id: string) => {
    const val = parseFloat(editing[id]);
    if (Number.isNaN(val) || val <= 0) return;
    await api.updateIngredient(id, val);
    setEditing((e) => {
      const next = { ...e };
      delete next[id];
      return next;
    });
    load();
  };

  return (
    <div>
      <TopBar
        title="Inventory & Ingredients"
        subtitle="What am I running low on?"
        showFilters={false}
        right={
          <div className="flex items-center gap-1 rounded-lg border border-border bg-surface-1 p-1">
            {(["overview", "count"] as const).map((v) => (
              <button
                key={v}
                onClick={() => setView(v)}
                className={`rounded-md px-3 py-1.5 font-mono text-[12px] transition-colors ${
                  view === v ? "bg-accent/[0.16] text-accent" : "text-text-secondary hover:text-text-primary"
                }`}
              >
                {v === "overview" ? "Overview" : "Manual count"}
              </button>
            ))}
          </div>
        }
      />
      <div className="px-4 py-4 md:px-8 md:py-6">
        {view === "count" ? (
          <InventoryCountPanel />
        ) : loading ? (
          <div className="py-24 text-center font-mono text-text-tertiary">Loading…</div>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 sm:gap-4">
              <StatCard
                label="Items to reorder"
                value={kpis.items_low_or_out.toString()}
                tone={kpis.items_low_or_out > 0 ? "loss" : "profit"}
              />
              <StatCard label="Completely out" value={kpis.items_out.toString()} tone={kpis.items_out > 0 ? "loss" : "neutral"} />
              <StatCard label="Total inventory value" value={money(kpis.total_inventory_value)} />
            </div>

            {alerts.length > 0 && (
              <div className="mt-4 flex flex-col gap-2">
                {alerts.map((a) => (
                  <div
                    key={a.ingredient_id}
                    className="flex items-center justify-between rounded-lg border px-4 py-2.5"
                    style={{
                      borderColor: a.status === "out" ? "rgba(226,72,61,0.35)" : "rgba(224,145,47,0.35)",
                      background: a.status === "out" ? "var(--loss-bg)" : "var(--accent-bg)",
                    }}
                  >
                    <span className="text-[13.5px] text-text-primary">
                      {a.status === "out" ? "Out of" : "Low on"} {a.name.replace(/\s*\(.*\)/, "").toLowerCase()} —
                      reorder soon
                    </span>
                    <span className="font-mono text-[12px] text-text-tertiary">
                      {a.stock_level} {a.unit} on hand · reorder point {a.reorder_point}
                    </span>
                  </div>
                ))}
              </div>
            )}

            <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
              <Card title="Stock on hand" className="lg:col-span-2" emphasis>
                <div className="max-h-[440px] overflow-x-auto overflow-y-auto">
                  <table className="w-full min-w-[560px]">
                    <thead className="sticky top-0 bg-surface-1">
                      <tr className="border-b border-border text-left font-mono text-[11px] text-text-tertiary">
                        <th className="pb-2 font-medium">Ingredient</th>
                        <th className="pb-2 text-right font-medium">On hand</th>
                        <th className="pb-2 text-right font-medium">Cost per unit</th>
                        <th className="pb-2 text-right font-medium">Value</th>
                        <th className="pb-2 text-right font-medium">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {items.map((i) => (
                        <tr
                          key={i.ingredient_id}
                          className="cursor-pointer border-b border-border/60 last:border-0 hover:bg-surface-2"
                          onClick={() => setSelectedIngredient(i.ingredient_id)}
                        >
                          <td className="py-2 text-[13px] text-text-primary">{i.name}</td>
                          <td className="py-2 text-right font-mono text-[12.5px] text-text-secondary">
                            {i.stock_level.toLocaleString()} {i.unit}
                          </td>
                          <td className="py-2 text-right font-mono text-[12.5px]" onClick={(e) => e.stopPropagation()}>
                            {editing[i.ingredient_id] !== undefined ? (
                              <input
                                autoFocus
                                value={editing[i.ingredient_id]}
                                onChange={(e) =>
                                  setEditing((s) => ({ ...s, [i.ingredient_id]: e.target.value }))
                                }
                                onBlur={() => saveCost(i.ingredient_id)}
                                onKeyDown={(e) => e.key === "Enter" && saveCost(i.ingredient_id)}
                                className="w-16 rounded border border-accent/40 bg-surface-2 px-1.5 py-0.5 text-right text-text-primary outline-none"
                              />
                            ) : (
                              <button
                                onClick={() =>
                                  setEditing((s) => ({ ...s, [i.ingredient_id]: String(i.unit_cost) }))
                                }
                                className="text-text-secondary underline decoration-dotted underline-offset-2 hover:text-accent"
                              >
                                {money(i.unit_cost, { cents: true })}
                              </button>
                            )}
                          </td>
                          <td className="py-2 text-right font-mono text-[12.5px] text-text-primary">
                            {money(i.value)}
                          </td>
                          <td className="py-2 text-right">
                            <StatusPill status={i.status} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>

              <Card
                title={`Recent usage — ${items.find((i) => i.ingredient_id === selectedIngredient)?.name ?? selectedIngredient}`}
                subtitle="What the last 14 days consumed. Click a row to change it."
              >
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={usageSeries}>
                    <CartesianGrid stroke={theme.border} vertical={false} />
                    <XAxis
                      dataKey="date"
                      tickFormatter={shortDate}
                      stroke={theme.textTertiary}
                      tick={{ fontFamily: "IBM Plex Mono", fontSize: 10 }}
                      tickLine={false}
                      axisLine={{ stroke: theme.border }}
                      interval={2}
                    />
                    <YAxis
                      stroke={theme.textTertiary}
                      tick={{ fontFamily: "IBM Plex Mono", fontSize: 10.5 }}
                      tickLine={false}
                      axisLine={false}
                      width={40}
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
                    />
                    <Bar dataKey="qty" fill={theme.accent} radius={[3, 3, 0, 0]} isAnimationActive={false} />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
